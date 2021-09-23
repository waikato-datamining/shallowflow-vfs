from opex import ObjectPredictions
from shallowflow.api.condition import AbstractBooleanCondition
from shallowflow.api.config import Option


class OpexLabelPresent(AbstractBooleanCondition):
    """
    Checks whether a specific label is present in the .
    """

    def description(self):
        """
        Returns a description for the object.

        :return: the object description
        :rtype: str
        """
        return "Combines the results of the base conditions using OR."

    def _define_options(self):
        """
        For configuring the options.
        """
        super()._define_options()
        self._option_manager.add(Option("label", str, "", "Checks whether the specified label is present in the OPEX prediction output"))
        self._option_manager.add(Option("min_score", float, 0.0, "The minimum score the objects must have"))

    def _do_evaluate(self, o):
        """
        Evaluates the condition.

        :param o: the current object from the owning actor (json string or dict)
        :return: the result of the evaluation
        :rtype: bool
        """
        if isinstance(o, str):
            preds = ObjectPredictions.from_json_string(o)
        elif isinstance(o, bytes):
            preds = ObjectPredictions.from_json_string(o.decode())
        else:
            raise Exception("Data must be an OPEX JSON string!")

        label = self.get("label")
        min_score = self.get("min_score")
        result = False
        for obj in preds.objects:
            if (obj.label == label) and (obj.score >= min_score):
                result = True
                break
        return result
