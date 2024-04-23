from typing import List, Dict


def list_classes() -> Dict[str, List[str]]:
    return {
        "shallowflow.base.conversions.AbstractConversion": [
            "shallowflow.vfs.conversions",
        ],
    }
