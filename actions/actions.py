from typing import Text, Dict, Any, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
from rasa_sdk.events import SlotSet
from requests.exceptions import RequestException
import random
import string


class ActionShowImage(Action):

    def name(self) -> Text:
        return "action_show_image"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        try:
            response = requests.request(
                "GET",
                "http://localhost:8080/api/render/image/",
            )
            response.raise_for_status()
            headers = {"Cache-Control": "no-cache", "Content-Type": "image/png"}
            upload_response = requests.request(
                "PUT",
                "https://archcad.s3.ap-south-1.amazonaws.com/floorplan.png",
                data=response.content,
                headers=headers,
            )
            upload_response.raise_for_status()

            dispatcher.utter_message(
                text="Here's the floorplan image:",
                image="https://archcad.s3.ap-south-1.amazonaws.com/floorplan.png?"
                + generate_random_string(5),
            )

        except RequestException as e:
            error_message = f"An error occurred: {str(e)}"
            dispatcher.utter_message(text=error_message)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            dispatcher.utter_message(text=error_message)

        return []


class ActionToggleLayer(Action):

    def name(self) -> Text:
        return "action_toggle_layer"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        layer = tracker.get_slot("layer")
        end_state = tracker.get_slot("end_state")
        response = requests.request(
            "GET",
            f"http://localhost:8080/api/render/info",
            params={"layer_name": layer},
        )
        response = requests.request(
            "GET",
            f"http://localhost:8080/api/render/toggle_layer",
            params={"layer_name": layer, "end_state": end_state},
        )
        response = requests.request(
            "GET",
            f"http://localhost:8080/api/render/info",
            params={"layer_name": layer},
        )
        if response.status_code == 200:
            dispatcher.utter_message(
                text=f"Layer {layer} toggled to {end_state}.",
            )
        else:
            dispatcher.utter_message(
                text="Failed to toggle layer display.",
            )
        return []


def generate_random_string(length):
    # Define the characters to choose from
    characters = string.ascii_letters

    # Generate the random string
    random_string = "".join(random.choice(characters) for _ in range(length))

    return random_string
