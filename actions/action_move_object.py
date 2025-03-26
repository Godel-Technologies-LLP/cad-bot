from typing import Text, Dict, Any, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from actions.file_handler import DXFProcessor  # Import the modified DXFHandler


class ActionMoveObjects(Action):

    def name(self) -> Text:
        return "action_move_object"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Extract required parameters
        object = tracker.get_slot("object")
        distance = tracker.get_slot("distance")

        if not all([object, distance]):
            dispatcher.utter_message(
                text="Missing required parameters. Please provide all details."
            )
            return []

        # Use singleton DXFHandler (does not reload file if already loaded)
        dxf_processor = DXFProcessor()
        dxf_processor.move_objects(object, distance)
        dxf_processor.save("./files/restroom_modified.dxf")
        # image = dxf_processor.convert_to_image()
        dispatcher.utter_message(text=f"Here is the modified position of the {object}")

        return []
