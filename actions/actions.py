from typing import Text, Dict, Any, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests


class ActionShowImage(Action):

    def name(self) -> Text:
        return "action_show_image"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        response = requests.request(
            "GET",
            "http://localhost:8080/api/render/image/",
        )
        # upload image to presigned URL of AWS
        response = requests.request(
            "POST",
            "https://archcad.s3.ap-south-1.amazonaws.com/floorplan.png",
            data=response.content,
            headers={"Content-Type": "image/jpeg"},
        )
        dispatcher.utter_message(
            text="",
            image="https://archcad.s3.ap-south-1.amazonaws.com/floorplan.png",
        )
        return []
