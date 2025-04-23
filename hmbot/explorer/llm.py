import json
import re
import time
# import cv2
from openai import OpenAI
from .explorer import Explorer
from .prompt import *
from ..cv import _crop, encode_image
from ..event import *
from ..proto import SwipeDirection, ExploreGoal, AudioStatus, ResourceType


class LLM(Explorer):
    def __init__(self, device=None, app=None, url='', model='', api_key=''):
        super().__init__(device, app)
        self.client = OpenAI(api_key=api_key, base_url=url)
        self.model = model

    def explore(self, **goal):
        """
        探索
        """
        scenario = self._understand(goal.get('key'), goal.get('value'))
        # 所有的已完成的操作，不包括错误的操作
        events_without_error = []
        # 所有已完成的操作，包括错误的操作
        all_completed_events = []
        # 反馈信息
        feedback = []
        # 界面元素信息
        nodes_before = []
        nodes_description_before = []
        steps = 0
        while not self._should_terminate(goal=goal) and steps < goal.get('max_steps'):
            # 获取执行操作前的界面
            window_before = self.device.dump_window(refresh=True)

            # 获取界面元素信息（只有第一次需要获取，因为verify前获取了操作后的界面信息）
            if not nodes_description_before:
                nodes_description_before, nodes_before = self._nodes_detect(window_before)

            # 获取下一次操作事件，event_explanation是将event转换成大模型易于理解的形式
            event, event_explanation = self._get_next_event(scenario, nodes_description_before, nodes_before,
                                                            window_before, all_completed_events, feedback)

            # 执行操作
            print("-----------------------执行大模型决定的操作-----------------------")
            event.execute()
            print(event_explanation)
            all_completed_events.append(event_explanation)
            steps += 1

            # 等待UI更新
            time.sleep(2)
            window_after = self.device.dump_window(refresh=True)
            nodes_description_after, nodes_after = self._nodes_detect(window_after)

            if isinstance(event, KeyEvent) and event.key == SystemKey.BACK:
                # 直接返回不需要验证操作
                nodes_description_before, nodes_before = nodes_description_after, nodes_after
                continue

            # 验证操作结果
            verify_result = self._verify_event(scenario, event_explanation, window_before, nodes_description_before,
                                               window_after, nodes_description_after)

            # 如果当前操作有效，将其添加到已完成的操作列表
            if verify_result["validity"]:
                events_without_error.append(event)

            # 如果验证结果是完成，结束探索
            if verify_result["goal_completion"] or (isinstance(event, KeyEvent) and event.key == SystemKey.HOME):
                break

            nodes_description_before, nodes_before = nodes_description_after, nodes_after

            feedback.clear()
            feedback.append("Analysis of the previous operation: " + verify_result["analysis"] + "\n")
            feedback.append("Suggested Next Steps: " + verify_result["next_steps"])
            print("Feedback: ", feedback)

    def _should_terminate(self, **goal):
        if goal.get('key') == ExploreGoal.TESTCASE:
            return False
        if goal.get('key') == ExploreGoal.HARDWARE:
            if goal.get('value') == ResourceType.AUDIO:
                status = self.device.get_audio_status()
                if status in [AudioStatus.START, AudioStatus.START_, AudioStatus.DUCK]:
                    return True
        return False
        

    def _understand(self, key, value):
        """
        理解 value 构建 scenario
        """
        print("-----------------------根据value构建scenario-----------------------")
        understanding_prompt = ''
        if key == ExploreGoal.TESTCASE:
            understanding_prompt = test_understanding_prompt.format(value)
        elif key == ExploreGoal.HARDWARE:
            understanding_prompt = hardware_understanding_prompt.format(value)
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
        print(scenario)
        return scenario

    def _nodes_detect(self, window):
        """
        检测与描述相符合的控件
        """
        print("-----------------------控件检测-----------------------")
        nodes = window(clickable='true')
        screenshot = window.img

        images = []
        for node in nodes:
            images.append(_crop(screenshot, node.attribute['bounds']))

        # 显示可点击控件
        # for image in images:
        #     cv2.imshow('image', image)
        #     cv2.waitKey(0)
        #     cv2.destroyAllWindows()

        nodes_description = self._add_information(nodes, screenshot, images)
        print(nodes_description)
        return nodes_description, nodes

    def _add_information(self, nodes, screenshot, images):
        """
        提取每个控件中的信息
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
            # print(len(image_list))
            # print(image_description)
            index = 0

            for node_info in nodes_description:
                if node_info['description'] == 'image':
                    node_info['description'] = image_description[index]
                    index += 1
        return nodes_description

    def _extract_nested_text(self, node):
        """
        递归提取节点及其子节点中的所有文本
        """
        texts = []

        # 如果当前节点有文本，添加到列表
        if 'text' in node.attribute and node.attribute['text']:
            texts.append(node.attribute['text'])

        # 递归处理所有子节点
        for child in node._children:
            texts.extend(self._extract_nested_text(child))
        return texts

    def _ask_llm_image(self, screenshot, nodes):
        """
        发送截图和多个控件截图给LLM，获取每个控件的描述列表
        """
        # 获取组件数量
        nodes_count = len(nodes)

        # 使用从prompt.py导入的模板
        description_prompt = image_description_prompt.format(component_count=nodes_count)

        # 准备消息内容
        content = [{"type": "text", "text": description_prompt},
                   {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(screenshot)}"}}]

        # 添加每个控件的截图
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
                # 如果没有找到列表格式，返回空列表
                return ["未知功能"] * len(nodes)
        except Exception as e:
            print(f"解析响应时出错: {e}")
            return ["未知功能"] * len(nodes)

    def _get_next_event(self, scenario, nodes_description, nodes, window, all_completed_events=None, feedback=None):
        """
        使用大模型决定下一步操作事件
        """
        print("-----------------------大模型决定下一步操作-----------------------")

        if all_completed_events is None:
            all_completed_events = []

        if feedback is None:
            feedback = []

        # 构建提示词
        prompt = next_event_prompt.format(scenario, nodes_description, all_completed_events, feedback)

        # 准备消息内容
        messages = [
            {"role": "system", "content": "You are a UI testing assistant that helps users decide what to do next."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{encode_image(window.img)}"}}]}, ]

        # 调用大模型API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False,
            )
            event_str = response.choices[0].message.content
            try:
                # 尝试解析JSON
                event_json = json.loads(event_str)
            except json.JSONDecodeError as e:
                event_json = json.loads(re.search(r'\{.*}', event_str, re.DOTALL).group(0))

            print("大模型返回的下一步动作：", event_json)

        except Exception as e:
            print(f"调用大模型API失败: {e}")
            return {"action": "error", "message": str(e)}

        # 解析大模型返回的JSON
        event_type = event_json.get("event_type")
        if event_type == "click":
            element_id = event_json.get("element_id")
            if element_id is not None and 1 <= element_id <= len(nodes_description):
                node = nodes[element_id]
                # 构建操作描述，易于大模型理解
                event_explanation = f"Click widget{element_id}: {nodes_description[element_id]['description']} at ({node.attribute['center']})"
                return ClickEvent(node), event_explanation
            else:
                return None
        elif event_type == "input":
            element_id = event_json.get("element_id")
            text = event_json.get("text", "")
            if element_id is not None and 1 <= element_id <= len(nodes_description):
                node = nodes[element_id]
                event_explanation = f"Input text '{text}' into widget{element_id}: {nodes_description[element_id]['description']}"
                return InputEvent(node, text), event_explanation
            else:
                return None
        elif event_type == "swipe":
            direction = event_json.get("direction")
            if direction in ["left", "right", "up", "down"]:
                event_explanation = f"Swipe {direction} to the screen"
                return SwipeExtEvent(self.device, window, SwipeDirection(direction)), event_explanation
            else:
                return None
        elif event_type == "back":
            event_explanation = "Go back to the previous screen"
            return KeyEvent(self.device, window, SystemKey.BACK), event_explanation
        elif event_type == "home":
            event_explanation = "Return to the home screen"
            return KeyEvent(self.device, window, SystemKey.HOME), event_explanation
        else:
            return None, "Unknown event type"

    def _verify_event(self, scenario, event_explanation, window_before, nodes_description_before, window_after,
                      nodes_description_after):
        """
        验证操作结果
        """
        print("-----------------------验证操作结果-----------------------")

        before_image_base64 = encode_image(window_before.img)
        before_image_content = f"data:image/jpeg;base64,{before_image_base64}"

        after_image_base64 = encode_image(window_after.img)
        after_image_content = f"data:image/jpeg;base64,{after_image_base64}"

        # 构建提示词
        prompt = verify_prompt.format(scenario, event_explanation, nodes_description_before,
                                      nodes_description_after)

        # 准备消息内容
        messages = [
            {"role": "system",
             "content": "You are a UI test verification assistant that helps users verify the results of their actions."}
        ]

        # 添加用户消息
        user_message = {"role": "user", "content": [{"type": "text", "text": prompt}]}

        # 如果有图像，添加到消息中
        user_message["content"].extend([
            {"type": "image_url", "image_url": {"url": before_image_content}},
            {"type": "image_url", "image_url": {"url": after_image_content}}
        ])

        messages.append(user_message)

        # 调用大模型API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=False,
        )
        verify_result_str = response.choices[0].message.content
        print("验证结果:", verify_result_str)

        # 解析JSON
        verify_result_json = re.search(r'\{.*}', verify_result_str, re.DOTALL)
        if verify_result_json:
            verify_result = json.loads(verify_result_json.group(0))
            return verify_result
