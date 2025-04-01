from typing import Text, Dict, Any, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
from rasa_sdk.events import SlotSet, FollowupAction
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout
import random
import string
from actions.query_db import get_layer_name
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ActionShowImage(Action):

    def name(self) -> Text:
        return "action_show_image"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        image_content = None

        # Step 1: Get the image from the render API
        try:
            response = requests.request(
                "GET", "http://localhost:8080/api/render/image/", timeout=10
            )
            response.raise_for_status()
            image_content = response.content
            logger.info("Successfully retrieved image from render API")
        except ConnectionError:
            logger.error("Connection error when trying to fetch image")
            dispatcher.utter_message(
                text="I couldn't connect to the design server. Please check if it's running."
            )
            return []
        except Timeout:
            logger.error("Timeout when trying to fetch image")
            dispatcher.utter_message(
                text="The request to the design server timed out. Please try again later."
            )
            return []
        except HTTPError as e:
            logger.error(f"HTTP error when fetching image: {str(e)}")
            dispatcher.utter_message(
                text=f"There was a problem retrieving the image: {e.response.status_code}"
            )
            return []
        except Exception as e:
            logger.error(f"Unexpected error when fetching image: {str(e)}")
            dispatcher.utter_message(
                text="An unexpected error occurred while retrieving the floorplan image."
            )
            return []

        # Step 2: Upload the image to S3
        if image_content:
            try:
                headers = {"Cache-Control": "no-cache", "Content-Type": "image/png"}
                upload_response = requests.request(
                    "PUT",
                    "https://archcad.s3.ap-south-1.amazonaws.com/floorplan.png",
                    data=image_content,
                    headers=headers,
                    timeout=15,
                )
                upload_response.raise_for_status()
                logger.info("Successfully uploaded image to S3")
            except ConnectionError:
                logger.error("Connection error when trying to upload image")
                dispatcher.utter_message(
                    text="I couldn't connect to the storage server. Please try again later."
                )
                return []
            except Timeout:
                logger.error("Timeout when trying to upload image")
                dispatcher.utter_message(
                    text="The upload to the storage server timed out. Please try again later."
                )
                return []
            except HTTPError as e:
                logger.error(f"HTTP error when uploading image: {str(e)}")
                dispatcher.utter_message(
                    text=f"There was a problem uploading the image: {e.response.status_code}"
                )
                return []
            except Exception as e:
                logger.error(f"Unexpected error when uploading image: {str(e)}")
                dispatcher.utter_message(
                    text="An unexpected error occurred while uploading the floorplan image."
                )
                return []

            # Step 3: Display the image to the user
            try:
                random_suffix = generate_random_string(5)
                dispatcher.utter_message(
                    text="Here's the floorplan image:",
                    image=f"https://archcad.s3.ap-south-1.amazonaws.com/floorplan.png?{random_suffix}",
                )
                logger.info("Successfully displayed image to user")
            except Exception as e:
                logger.error(f"Error displaying image to user: {str(e)}")
                dispatcher.utter_message(
                    text="I had trouble displaying the image, but it has been uploaded successfully."
                )

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
        # Get and validate slots
        raw_layer = tracker.get_slot("layer")
        end_state = tracker.get_slot("end_state")

        layer = get_layer_name(raw_layer)

        print(f"Raw layer: {raw_layer} mapped to design naming convention: {layer}")

        # Step 2: Toggle the layer
        try:
            toggle_response = requests.request(
                "GET",
                "http://localhost:8080/api/render/toggle_layer",
                params={"layer_name": layer, "end_state": end_state},
                timeout=10,
            )
            toggle_response.raise_for_status()
            logger.info(f"Successfully toggled layer {layer} to {end_state}")
        except ConnectionError:
            logger.error(f"Connection error when toggling layer {layer}")
            dispatcher.utter_message(
                text="I couldn't connect to the design server when trying to toggle the layer."
            )
            return []
        except Timeout:
            logger.error(f"Timeout when toggling layer {layer}")
            dispatcher.utter_message(
                text="The request to toggle the layer timed out. Please try again later."
            )
            return []
        except HTTPError as e:
            logger.error(f"HTTP error when toggling layer {layer}: {str(e)}")
            dispatcher.utter_message(
                text=f"There was a problem toggling the layer: {e.response.status_code}"
            )
            return []
        except Exception as e:
            logger.error(f"Unexpected error when toggling layer {layer}: {str(e)}")
            dispatcher.utter_message(text=f"Failed to toggle layer '{layer}'. {str(e)}")
            return []

        # Step 3: Get updated layer info
        # try:
        #     updated_info_response = requests.request(
        #         "GET",
        #         "http://localhost:8080/api/render/info",
        #         params={"layer_name": layer},
        #         timeout=10,
        #     )
        #     updated_info_response.raise_for_status()
        #     logger.info(f"Successfully retrieved updated info for layer {layer}")
        # except Exception as e:
        #     # We can continue even if this fails, as it's just for verification
        #     logger.warning(f"Error getting updated layer info: {str(e)}")

        # dispatcher.utter_message(
        #     text=f"Layer '{layer}' has been updated successfully.",
        # )

        # Automatically show the updated image
        return [FollowupAction("action_show_image")]


def generate_random_string(length):
    # Define the characters to choose from
    characters = string.ascii_letters + string.digits
    # Generate the random string
    random_string = "".join(random.choice(characters) for _ in range(length))
    return random_string


class ActionMoveObject(Action):

    def name(self) -> Text:
        return "action_move_object"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Get and validate slots
        object_name = tracker.get_slot("object")
        distance = tracker.get_slot("distance")

        layer = get_layer_name(object_name)
        movable_layers = []

        # Step 1: Get list of movable objects
        try:
            list_response = requests.request(
                "GET", "http://localhost:8080/api/transform/list/", timeout=10
            )
            list_response.raise_for_status()

            movable_data = list_response.json()

            if (
                not isinstance(movable_data, dict)
                or "movable_layers" not in movable_data
            ):
                dispatcher.utter_message(
                    text="I received an unexpected response from the design server."
                )
                return []

            movable_layers = movable_data.get("movable_layers", [])
            logger.info(
                f"Successfully retrieved list of movable objects: {movable_layers}"
            )
        except ConnectionError:
            logger.error("Connection error when listing movable objects")
            dispatcher.utter_message(
                text="I couldn't connect to the design server. Please check if it's running."
            )
            return []
        except Timeout:
            logger.error("Timeout when listing movable objects")
            dispatcher.utter_message(
                text="The request to the design server timed out. Please try again later."
            )
            return []
        except HTTPError as e:
            logger.error(f"HTTP error when listing movable objects: {str(e)}")
            dispatcher.utter_message(
                text=f"There was a problem retrieving the list of movable objects: {e.response.status_code}"
            )
            return []
        except Exception as e:
            logger.error(f"Unexpected error when listing movable objects: {str(e)}")
            dispatcher.utter_message(
                text=f"Failed to retrieve the list of movable objects. {str(e)}"
            )
            return []

        # Step 2: Check if object is movable and move it
        if layer in movable_layers:
            try:
                move_response = requests.request(
                    "GET",
                    "http://localhost:8080/api/transform/move/",
                    params={"entity_layer_name": layer, "distance": distance},
                    timeout=10,
                )
                move_response.raise_for_status()
                logger.info(f"Successfully moved object {layer} by {distance}")

                dispatcher.utter_message(
                    text=f"I've moved the {object_name} by {distance} units."
                )
                return [FollowupAction("action_show_image")]
            except ConnectionError:
                logger.error(f"Connection error when moving object {layer}")
                dispatcher.utter_message(
                    text="I couldn't connect to the design server when trying to move the object."
                )
                return []
            except Timeout:
                logger.error(f"Timeout when moving object {layer}")
                dispatcher.utter_message(
                    text="The request to move the object timed out. Please try again later."
                )
                return []
            except HTTPError as e:
                logger.error(f"HTTP error when moving object {layer}: {str(e)}")
                dispatcher.utter_message(
                    text=f"There was a problem moving the object: {e.response.status_code}"
                )
                return []
            except Exception as e:
                logger.error(f"Unexpected error when moving object {layer}: {str(e)}")
                dispatcher.utter_message(
                    text=f"Failed to move '{object_name}'. {str(e)}"
                )
                return []
        else:
            dispatcher.utter_message(
                text=f"Sorry, '{object_name}' cannot be moved in this version. It might be a fixed element."
            )
            return []


class ActionListObjects(Action):

    def name(self) -> Text:
        return "action_list_objects"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Step 1: Get list of objects
        try:
            list_response = requests.request(
                "GET", "http://localhost:8080/api/transform/list/", timeout=10
            )
            list_response.raise_for_status()

            data = list_response.json()

            if (
                not isinstance(data, dict)
                or "movable_layers" not in data
                or "immovable_layers" not in data
            ):
                dispatcher.utter_message(
                    text="I received an unexpected response from the design server."
                )
                return []

            movable_layers = data.get("movable_layers", [])
            immovable_layers = data.get("immovable_layers", [])
            logger.info(
                f"Successfully retrieved list of objects. Movable: {len(movable_layers)}, Immovable: {len(immovable_layers)}"
            )

            # Format the response in a more user-friendly way
            if movable_layers:
                movable_text = ", ".join(movable_layers)
                dispatcher.utter_message(
                    text=f"Objects that can be moved: {movable_text}"
                )
            else:
                dispatcher.utter_message(text="There are no objects that can be moved.")

            if immovable_layers:
                immovable_text = ", \n".join(immovable_layers)
                dispatcher.utter_message(
                    text=f"Objects that cannot be moved: {immovable_text}"
                )
            else:
                dispatcher.utter_message(text="There are no immovable objects.")

        except ConnectionError:
            logger.error("Connection error when listing objects")
            dispatcher.utter_message(
                text="I couldn't connect to the design server. Please check if it's running."
            )
        except Timeout:
            logger.error("Timeout when listing objects")
            dispatcher.utter_message(
                text="The request to the design server timed out. Please try again later."
            )
        except HTTPError as e:
            logger.error(f"HTTP error when listing objects: {str(e)}")
            dispatcher.utter_message(
                text=f"There was a problem retrieving the object list: {e.response.status_code}"
            )
        except Exception as e:
            logger.error(f"Unexpected error when listing objects: {str(e)}")
            dispatcher.utter_message(
                text=f"Failed to retrieve the list of objects. {str(e)}"
            )

        return []
