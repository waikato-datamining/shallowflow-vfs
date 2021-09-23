import os
import redis
from shallowflow.api.io import File
from shallowflow.base.conditions import NumExpr
from shallowflow.base.controls import Flow, Tee, Trigger, ConditionalTee, run_flow
from shallowflow.base.sources import FileSupplier, GetVariable
from shallowflow.base.transformers import SetVariable
from shallowflow.base.sinks import ConsoleOutput
from shallowflow.cv2.transformers import VideoFileReader
from shallowflow.cv2.sinks import VideoWriter
from shallowflow.redis.standalones import RedisConnection
from shallowflow.redis.transformers import RedisTransformer
from shallowflow.redis.transformers.action import BroadcastAndListen
from shallowflow.vfs.conditions import OpexLabelPresent

channel_in = "predictions"
channel_out = "images"
labels = ["object", "nothing"]
count = 0

pred = """{
  "timestamp": "2021-09-22 13:12:00.123456",
  "id": "str",
  "objects": [
    {
      "score": 1.0,
      "label": "%s",
      "bbox": {
        "top": 100,
        "left": 100,
        "bottom": 200,
        "right": 200
      },
      "polygon": {
        "points": [
          [100, 100],
          [200, 200],
          [100, 200]
        ]
      }
    }
  ]
}
"""

# dummy redis process, simply appends "-done" to incoming data
r = redis.Redis()
p = r.pubsub()
def anon_handler(message):
    global count
    count += 1
    if count >= len(labels):
        count = 0
    r.publish(channel_in, pred % labels[count])
p.psubscribe(**{channel_out: anon_handler})
p.run_in_thread(sleep_time=0.001)

flow = Flow().manage([
    RedisConnection(),
    FileSupplier({"files": [File("./data/track_book.mjpeg")]}),
    VideoFileReader({"nth_frame": 2, "max_frames": 10}),  # extract every 2nd frame, but only 10 at most
    Tee().manage([
        SetVariable({"var_name": "keep", "var_value": "False"}),
        RedisTransformer({"action": BroadcastAndListen({"channel_out": channel_out, "channel_in": channel_in})}),
        ConditionalTee({"condition": OpexLabelPresent({"label": "object"})}).manage([
            SetVariable({"var_name": "keep", "var_value": "True"}),
        ]),
    ]),
    Trigger().manage([
        GetVariable({"var_name": "keep"}),
        ConsoleOutput(),
    ]),
    ConditionalTee({"condition": NumExpr({"expression": "@{keep} == True"})}).manage([
        VideoWriter({"output_file": File("./output/track_book.avi")}),
    ]),
])

msg = run_flow(flow, dump_file="./output/" + os.path.splitext(os.path.basename(__file__))[0] + ".json")
if msg is not None:
    print(msg)

print("done, press Ctrl+C to stop dummy redis transformer...")
