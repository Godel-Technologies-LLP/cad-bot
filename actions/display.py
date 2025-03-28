from typing import Text, Dict, Any, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from actions.file_handler import DataProcessor


class ActionShowImage(Action):

    def name(self) -> Text:
        return "action_show_image"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        data_processor = DataProcessor()
        image = data_processor.convert_to_image()
        # Send to s3
        # send URL in the image
        dispatcher.utter_message(
            text="",
            image="https://s3.amazonaws.com/your-bucket/output.png",
        )
        return []
