import json
import re
import threading
import time
# import cv2
from loguru import logger
from openai import OpenAI
from .explorer import Explorer
from .prompt import *
from ..cv import _crop, encode_image
from ..event import *
from ..proto import SwipeDirection, ExploreGoal, AudioStatus, ResourceType
from ..wtg import WTG, WTGParser


class LLM(Explorer):
    def __init__(self, device=None, app=None, url='', model='', api_key=''):
        super().__init__(device, app)
        self.client = OpenAI(api_key=api_key, base_url=url)
        self.model = model
        self.terminated = False
        self.lock = threading.Lock()

    def explore(self, **goal):
        """
        Exploration
        """
        wtg = WTG()

        ability_count = set()
        edges_count = 0
        start = time.time()

        with self.lock:
            first_window = self.device.dump_window(refresh=True)
        scenario = self._understand(goal.get('key'), goal.get('value'), first_window)
        # All completed operations, excluding erroneous operations
        events_without_error = []
        # All completed operations, including erroneous operations
        all_completed_events = []
        # Feedback information
        feedback = []
        # Interface element information
        nodes_before = []
        nodes_description_before = []
        steps = 0

        t1 = threading.Thread(target=self._should_terminate_thread, args=(goal,))
        t1.start()

        # Termination condition
        # self.terminated = self._should_terminate(window=first_window, goal=goal)
        # logger.debug("terminated: " + str(terminated))
        if self.terminated:
            wtg.add_window(first_window)
            ability_count.add(first_window.ability)

        while not self.terminated and steps < goal.get('max_steps'):
            # logger.debug("terminated: " + str(self.terminated))
            # Get interface before operation execution

            with self.lock:
                window_before = self.device.dump_window(refresh=True)

            # Get interface element information (only needed first time, as verify gets post-operation interface info)
            if not nodes_description_before:
                nodes_description_before, nodes_before = self._nodes_detect(window_before)

            # Get next operation event, event_explanation converts event to a form easily understood by LLM
            events, event_explanation = self._get_next_event(scenario, nodes_description_before, nodes_before,
                                                            window_before, all_completed_events, feedback)

            # Execute operation
            logger.debug("-----------------------Executing LLM-decided operation-----------------------")
            self.device.execute(events)
            logger.debug(event_explanation)
            all_completed_events.append(event_explanation)
            steps += 1

            # Wait for UI update
            time.sleep(2)
            with self.lock:
                window_after = self.device.dump_window(refresh=True)
            nodes_description_after, nodes_after = self._nodes_detect(window_after)
            # self.terminated = self._should_terminate(window=window_after, goal=goal)

            if isinstance(events[0], KeyEvent) and events[0].key == SystemKey.BACK:
                # Back operation doesn't need verification
                nodes_description_before, nodes_before = nodes_description_after, nodes_after
                continue

            # Verify operation result
            verify_result = self._verify_event(scenario, event_explanation, window_before, nodes_description_before,
                                               window_after, nodes_description_after)
            # self.terminated = self._should_terminate(window=window_after, goal=goal)

            # If current operation is valid, add it to the completed operations list
            if verify_result["validity"]:
                events_without_error.extend(events)
                wtg.add_edge(window_before, window_after, events)
                ability_count.add(window_before.ability)
                ability_count.add(window_after.ability)
                edges_count += 1

            # If verification result is complete, end exploration
            # if verify_result["goal_completion"] or (isinstance(events[0], KeyEvent) and events[0].key == SystemKey.HOME):
            #     break

            nodes_description_before, nodes_before = nodes_description_after, nodes_after

            feedback.clear()
            feedback.append("Analysis of the previous operation: " + verify_result["analysis"] + "\n")
            feedback.append("Suggested Next Steps: " + verify_result["next_steps"])
            logger.debug(f"Feedback: {feedback}")

        end = time.time()
        logger.debug("events_count: " + str(len(events_without_error)))
        logger.debug("windows_count: " + str(len(wtg.windows)))
        logger.debug("edges_count: " + str(edges_count))
        logger.debug("ability_count: " + str(len(ability_count)))
        logger.debug("total_time: %.2f seconds" % (end - start))
        WTGParser.dump(wtg, 'wtg.json')
        t1.join()

    def _should_terminate(self, window, goal):
        if goal.get('key') == ExploreGoal.TESTCASE:
            return False
        if goal.get('key') == ExploreGoal.HARDWARE:
            if goal.get('value') == ResourceType.AUDIO:
                # status = self.device.get_audio_status()
                status = window.rsc.get(ResourceType.AUDIO)
                if status in [AudioStatus.START, AudioStatus.START_, AudioStatus.DUCK]:
                    logger.debug("Audio is playing, terminating exploration.")
                    return True
        return False

    def _should_terminate_thread(self, goal):
        """
        Termination condition
        """
        while True:
            with self.lock:
                window = self.device.dump_window(refresh=True)
            if goal.get('key') == ExploreGoal.TESTCASE:
                return False
            if goal.get('key') == ExploreGoal.HARDWARE:
                if goal.get('value') == ResourceType.AUDIO:
                    status = window.rsc.get(ResourceType.AUDIO)
                    if status in [AudioStatus.START, AudioStatus.START_, AudioStatus.DUCK]:
                        logger.debug("Audio is playing, terminating exploration.")
                        self.terminated = True
                        return True
            time.sleep(1)

    def test(self, **goal):
        t1 = threading.Thread(target=self._should_terminate_thread, args=(goal,))
        t1.start()
        t1.join()


    def _understand(self, key, value, first_window=None):
        """
        Understand value to build scenario
        """
        logger.debug("-----------------------Building scenario based on value-----------------------")
        if key == ExploreGoal.TESTCASE:
            understanding_prompt = test_understanding_prompt.format(value)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a UI Testing Assistant.",
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": understanding_prompt},
                        ],
                    },
                ],
                stream=False,
            )
            scenario = response.choices[0].message.content
            logger.debug(scenario)
            return scenario
        elif key == ExploreGoal.HARDWARE:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a UI Testing Assistant.", 
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": first_window_understanding_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(first_window.img)}"}}
                        ],
                    },
                ],
                stream=False,
            )
            app_kind = response.choices[0].message.content
            scenario = ''
            if value == ResourceType.AUDIO:
                if app_kind == 'Navigation':
                    scenario = navigation_audio_prompt
                elif app_kind == 'Music Player':
                    scenario = music_player_audio_prompt
                elif app_kind == 'Video Player':
                    scenario = video_player_audio_prompt
                elif app_kind == 'Social Media':
                    scenario = social_media_audio_prompt
                else:
                    scenario = other_audio_prompt
            elif value == ResourceType.CAMERA:
                scenario = camera_prompt
            elif value == ResourceType.MICRO:
                scenario = micro_prompt
            elif value == ResourceType.KEYBOARD:
                scenario = keyboard_prompt
            else:
                logger.debug("Unknown hardware resource")
            logger.debug(scenario)
            return scenario


    def _nodes_detect(self, window):
        """
        Detect controls that match the description
        """
        logger.debug("-----------------------Control detection-----------------------")
        nodes = window(clickable='true', enabled='true')
        screenshot = window.img

        images = []
        for node in nodes:
            images.append(_crop(screenshot, node.attribute['bounds']))
            # logger.debug(node)

        # Display clickable controls
        # for image in images:
        #     cv2.imshow('image', image)
        #     cv2.waitKey(0)
        #     cv2.destroyAllWindows()

        nodes_description = self._add_information(nodes, screenshot, images)
        logger.debug(nodes_description)
        return nodes_description, nodes

    def _add_information(self, nodes, screenshot, images):
        """
        Extract information from each control
        """
        nodes_description = []
        image_list = []
        for index, node in enumerate(nodes):
            node_info = {'element_id': index, 'type': node.attribute['type']}
            texts = self._extract_nested_text(node)
            node_info['description'] = ', '.join(texts) if texts else None
            if node_info['description'] is None:
                node_info['description'] = 'image'
                image_list.append(images[index])
            nodes_description.append(node_info)
        if image_list:
            image_description = self._ask_llm_image(screenshot, image_list)
            # logger.debug(len(image_list))
            # logger.debug(image_description)
            index = 0

            for node_info in nodes_description:
                if node_info['description'] == 'image':
                    node_info['description'] = image_description[index]
                    index += 1
        return nodes_description

    def _extract_nested_text(self, node):
        """
        Recursively extract all text from node and its children
        """
        texts = []

        # If current node has text, add to list
        if 'text' in node.attribute and node.attribute['text']:
            texts.append(node.attribute['text'])

        # Recursively process all child nodes
        for child in node._children:
            texts.extend(self._extract_nested_text(child))
        return texts

    def _ask_llm_image(self, screenshot, nodes):
        """
        Send screenshot and multiple control screenshots to LLM, get description list for each control
        """
        # Get component count
        nodes_count = len(nodes)

        # Use template imported from prompt.py
        description_prompt = image_description_prompt.format(component_count=nodes_count)

        # Prepare message content
        content = [{"type": "text", "text": description_prompt},
                   {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(screenshot)}"}}]

        # Add screenshot for each control
        for i, component in enumerate(nodes):
            content.append({"type": "text", "text": f"Component {i + 1} of {nodes_count}:"})
            content.append(
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(component)}"}})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a UI Testing Assistant.",
                },
                {
                    "role": "user",
                    "content": content,
                },
            ],
            stream=False,
        )

        response_text = response.choices[0].message.content

        try:
            match = re.search(r'\[(.*)]', response_text, re.DOTALL)
            if match:
                items_str = match.group(1)
                items = re.findall(r'\'([^\']*?)\'|\"([^\"]*?)\"', items_str)
                descriptions = [item[0] if item[0] else item[1] for item in items]
                return descriptions
            else:
                # If list format not found, return empty list
                return ["Unknown function"] * len(nodes)
        except Exception as e:
            logger.debug(f"Error parsing response: {e}")
            return ["Unknown function"] * len(nodes)

    def _get_next_event(self, scenario, nodes_description, nodes, window, all_completed_events=None, feedback=None):
        """
        Use LLM to decide next operation event
        """
        logger.debug("-----------------------LLM deciding next operation-----------------------")

        if all_completed_events is None:
            all_completed_events = []

        if feedback is None:
            feedback = []

        # Build prompt
        prompt = next_event_prompt.format(scenario, nodes_description, all_completed_events, feedback)

        # Prepare message content
        messages = [
            {"role": "system", "content": "You are a UI testing assistant that helps users decide what to do next."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{encode_image(window.img)}"}}]}, ]

        # Call LLM API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False,
            )
            event_str = response.choices[0].message.content
            try:
                # Try to parse JSON
                event_json = json.loads(event_str)
            except json.JSONDecodeError as e:
                event_json = json.loads(re.search(r'\{.*}', event_str, re.DOTALL).group(0))

            logger.debug(f"Next action returned by LLM: {str(event_json)}", )


        except Exception as e:
            logger.debug(f"Failed to call LLM API: {e}")
            return {"action": "error", "message": str(e)}

        events_list = []
        event_explanation = ''

        # Parse JSON returned by LLM
        event_type = event_json.get("event_type")
        if event_type == "click":
            element_id = event_json.get("element_id")
            if element_id is not None and 0 <= element_id <= len(nodes_description)-1:
                node = nodes[element_id]
                events_list.append(ClickEvent(node))
                # Build operation description, easy for LLM to understand
                event_explanation = f"Click widget{element_id}: {nodes_description[element_id]['description']} at ({node.attribute['center']})"

        elif event_type == "input":
            element_id = event_json.get("element_id")
            text = event_json.get("text", "")
            if element_id is not None and 0 <= element_id <= len(nodes_description)-1:
                node = nodes[element_id]
                if node.attribute['focused'] == 'false':
                    events_list.append(ClickEvent(node))
                events_list.append(InputEvent(node, text))
                event_explanation = f"Input text '{text}' into widget{element_id}: {nodes_description[element_id]['description']}"

        elif event_type == "swipe":
            direction = event_json.get("direction")
            if direction in ["left", "right", "up", "down"]:
                events_list.append(SwipeExtEvent(self.device, window, SwipeDirection(direction)))
                event_explanation = f"Swipe {direction} to the screen"

        elif event_type == "back":
            event_explanation = "Go back to the previous screen"
            events_list.append(KeyEvent(self.device, window, SystemKey.BACK))

        elif event_type == "home":
            event_explanation = "Return to the home screen"
            events_list.append(KeyEvent(self.device, window, SystemKey.HOME))

        return events_list, event_explanation

    def _verify_event(self, scenario, event_explanation, window_before, nodes_description_before, window_after,
                      nodes_description_after):
        """
        Verify operation result
        """
        logger.debug("-----------------------Verifying operation result-----------------------")

        before_image_base64 = encode_image(window_before.img)
        before_image_content = f"data:image/jpeg;base64,{before_image_base64}"

        after_image_base64 = encode_image(window_after.img)
        after_image_content = f"data:image/jpeg;base64,{after_image_base64}"

        # Build prompt
        prompt = verify_prompt.format(scenario, event_explanation, nodes_description_before,
                                      nodes_description_after)

        # Prepare message content
        messages = [
            {"role": "system",
             "content": "You are a UI test verification assistant that helps users verify the results of their actions."}
        ]

        # Add user message
        user_message = {"role": "user", "content": [{"type": "text", "text": prompt}]}

        # If there are images, add to message
        user_message["content"].extend([
            {"type": "image_url", "image_url": {"url": before_image_content}},
            {"type": "image_url", "image_url": {"url": after_image_content}}
        ])

        messages.append(user_message)

        # Call LLM API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=False,
        )
        verify_result_str = response.choices[0].message.content
        logger.debug(f"Verification result: {verify_result_str}")

        # Parse JSON
        verify_result_json = re.search(r'\{.*}', verify_result_str, re.DOTALL)
        if verify_result_json:
            verify_result = json.loads(verify_result_json.group(0))
            return verify_result
