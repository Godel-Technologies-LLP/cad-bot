from typing import Text, Dict, Any, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from actions.file_handler import DataProcessor
from rasa_sdk.events import SlotSet


class ActionInitData(Action):

    def name(self) -> Text:
        return "action_initialize_data"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Read the dxf file if not already in memeory
        data_processor = DataProcessor()
        data_processor_dict = data_processor.to_dict()

        # save to tracker
        return [SlotSet("data_processor", data_processor_dict)]
