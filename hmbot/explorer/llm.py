import json
import re
import time
import cv2
from openai import OpenAI
from .explorer import Explorer
from .prompt import *
from ..cv import _crop, encode_image
from ..event import *
from ..proto import SwipeDirection


class LLM(Explorer):
    def __init__(self, device=None, app=None, url='', model='', api_key=''):
        super().__init__(device, app)
        self.client = OpenAI(api_key=api_key, base_url=url)
        self.model = model


    def explore(self, key='test', value=''):
        if key == 'test':
            self._run_test_transition(value)
        elif key == 'hardware':
            self._run_hardware_transition(value)

    def _run_test_transition(self, script):
        """
        运行测试迁移
        """
        # 测试脚本理解
        scenario = self._test_understand(script)

        # 初始化测试记录
        test_record = []
        # 所有已完成的操作
        completed_actions = []
        # 反馈信息
        feedback = []
        # 界面元素信息
        nodes = []
        clickable_weights_description_before = []


        for _ in range(20):
            # 获取当前界面
            window_before = self.device.dump_window(refresh=True)

            # 获取界面元素信息（只有第一次需要获取，后面直接使用verify获取的元素）
            if not clickable_weights_description_before:
                clickable_weights_description_before, nodes = self._widget_detect(window_before)

            # 获取下一次操作
            next_action = self._get_next_action(clickable_weights_description_before, scenario, window_before,
                                                completed_actions, feedback)

            # 执行操作
            op_list, op_explanation = self._execute_action(next_action, clickable_weights_description_before, nodes, window_before)
            # print(f"op_list: {op_list}")
            test_record.extend(op_list)
            print(op_explanation)

            # 等待UI更新
            time.sleep(2)
            window_after = self.device.dump_window(refresh=True)

            # 如果操作是完成或返回桌面，结束测试
            if next_action.get("action") == 'finish' or next_action.get("action") == 'home':
                break

            # 如果操作是返回，直接返回
            if next_action["action"] == "back":
                # 直接返回不需要验证操作
                clickable_weights_description_before, nodes = self._widget_detect(window_after)
                continue

            # 验证操作结果
            result_json, clickable_weights_description_before, nodes = self._verify_operation_result(window_before, window_after, scenario, op_explanation,
                                                                                  clickable_weights_description_before)

            feedback.clear()
            completed_actions.append(op_explanation)

            feedback.append("Analysis of the previous operation: " + result_json["analysis"])
            if result_json["goal_completion"]:
                break
            feedback.append("Suggested Next Steps: " + result_json["next_steps"] + "\n")
            print("Feedback: ", feedback)

        print(completed_actions)

    def _run_hardware_transition(self, value):
        pass

    def _test_understand(self, script):
        """
        测试脚本理解
        """
        print("-----------------------根据测试脚本构建测试场景-----------------------")
        text = extraction_prompt.format(script)
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
                        {"type": "text", "text": text},
                    ],
                },
            ],
            stream=False,
        )
        scenario = response.choices[0].message.content
        print(scenario)
        return scenario


    def _widget_detect(self, window):
        """
        检测与描述相符合的控件
        """
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

        clickable_weights_description = self._add_information(nodes, screenshot, images)
        print(clickable_weights_description)
        return clickable_weights_description, nodes

    def _add_information(self, nodes, screenshot, images):
        """
        提取每个控件中的信息
        """
        clickable_weights_description = []
        image_list = []
        for index, node in enumerate(nodes):
            node_info = {'element_id': index, 'type': node.attribute['type']}
            texts = self._extract_nested_text(node)
            node_info['description'] = ', '.join(texts) if texts else None
            if node_info['description'] is None:
                node_info['description'] = 'image'
                image_list.append(images[index])
            clickable_weights_description.append(node_info)
        if image_list:
            image_description = self._ask_llm_image(screenshot, image_list)
            # print(len(image_list))
            # print(image_description)
            index = 0

            for node_info in clickable_weights_description:
                if node_info['description'] == 'image':
                    node_info['description'] = image_description[index]
                    index += 1
        return clickable_weights_description

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

    def _ask_llm_image(self, screenshot, weights):
        """
        发送截图和多个控件截图给LLM，获取每个控件的描述列表
        """
        # 获取组件数量
        component_count = len(weights)

        # 使用从prompt.py导入的模板
        description_prompt = image_description_prompt.format(component_count=component_count)

        # Build content with all component images
        content = [{"type": "text", "text": description_prompt},
                   {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(screenshot)}"}}]

        # Add each component image with a label
        for i, component in enumerate(weights):
            content.append({"type": "text", "text": f"Component {i + 1} of {component_count}:"})
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
            match = re.search(r'\[(.*)\]', response_text, re.DOTALL)
            if match:
                items_str = match.group(1)
                items = re.findall(r'\'([^\']*?)\'|\"([^\"]*?)\"', items_str)
                descriptions = [item[0] if item[0] else item[1] for item in items]
                return descriptions
            else:
                # 如果没有找到列表格式，返回空列表
                return ["未知功能"] * len(weights)
        except Exception as e:
            print(f"解析响应时出错: {e}")
            return ["未知功能"] * len(weights)

    def _get_next_action(self, weights_description, test_scenario, window, completed_actions=None, feedback=None):
        """
        使用大模型决定下一步操作
        """
        print("-----------------------大模型决定下一步操作-----------------------")

        if completed_actions is None:
            completed_actions = []

        if feedback is None:
            feedback = []

        # 构建提示词
        prompt = next_action_prompt.format(test_scenario, weights_description, completed_actions, feedback)

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
            action_json = response.choices[0].message.content
            try:
                # 尝试解析JSON
                action = json.loads(action_json)
            except json.JSONDecodeError as e:
                action = json.loads(re.search(r'\{.*\}', action_json, re.DOTALL).group(0))

            print("大模型返回的下一步动作：", action)
            return action

        except Exception as e:
            print(f"调用大模型API失败: {e}")
            return {"action": "error", "message": str(e)}

    def _execute_action(self, action, weights_description, nodes, window):
        """
        执行大模型决定的操作
        """
        print("-----------------------执行大模型决定的操作-----------------------")

        action_type = action.get("action")
        op_list = []

        if action_type == "click":
            # 点击元素
            element_id = action.get("element_id")
            if element_id is not None and 1 <= element_id <= len(nodes):
                node = nodes[element_id]
                op_list.append(ClickEvent(self.device, window, node.attribute['center'][0], node.attribute['center'][1]))
                # ClickEvent(self.device, window, node.attribute['center'][0], node.attribute['center'][1]).execute()
                op_str = f"Click widget{element_id}: {weights_description[element_id].get('description', '')} at ({node.attribute['center']})"
                self.device.execute(events=op_list)
                return op_list, op_str
            else:
                return None, f"无效的元素ID: {element_id}"

        elif action_type == "input":
            # 输入文本
            element_id = action.get("element_id")
            text = action.get("text", "")

            if element_id is not None and 1 <= element_id <= len(nodes):
                node = nodes[element_id]
                # 先点击元素
                op_list.append(
                    ClickEvent(self.device, window, node.attribute['center'][0], node.attribute['center'][1]))
                time.sleep(1)
                # 输入文本
                op_list.append(InputEvent(self.device, window, node, text))
                op_str = f"{text} was entered in element {element_id}"
                self.device.execute(events=op_list)
                return op_list, op_str
            else:
                return None, f"无效的元素ID: {element_id}"

        elif action_type == "swipe":
            # 滑动屏幕
            direction = action.get("direction")
        
            # 根据方向设置滑动命令
            if direction == "up":
                op_list.append(SwipeExtEvent(self.device, window, SwipeDirection.UP))
            elif direction == "down":
                op_list.append(SwipeExtEvent(self.device, window, SwipeDirection.DOWN))
            elif direction == "left":
                op_list.append(SwipeExtEvent(self.device, window, SwipeDirection.LEFT))
            elif direction == "right":
                op_list.append(SwipeExtEvent(self.device, window, SwipeDirection.RIGHT))
            else:
                return op_list, f"无效的滑动方向: {direction}"

            self.device.execute(events=op_list)
            return f"执行{direction}方向的滑动操作", cmd_list

        elif action_type == "back":
            # 返回
            op_list.append(KeyEvent(self.device, window, SystemKey.BACK))
            self.device.execute(events=op_list)
            return op_list, "A return operation was performed"

        elif action_type == "home":
            # 返回
            op_list.append(KeyEvent(self.device, window, SystemKey.HOME))
            self.device.execute(events=op_list)
            return op_list, "A return home operation was performed"

        elif action_type == "finish":
            # 完成测试
            return "Finish"

        else:
            return f"未知的操作类型: {action_type}"

    def _verify_operation_result(self, window_before, window_after, test_scenario, operation,
                                 element_descriptions_before):
        """
        验证操作结果
        """
        print("-----------------------验证操作结果-----------------------")
        # 获取操作后的UI元素
        element_descriptions_after, elements_after = self._widget_detect(window_after)

        before_image_base64 = encode_image(window_before.img)
        before_image_content = f"data:image/jpeg;base64,{before_image_base64}"

        after_image_base64 = encode_image(window_after.img)
        after_image_content = f"data:image/jpeg;base64,{after_image_base64}"

        # 构建提示词
        prompt = verify_prompt.format(test_scenario, operation, element_descriptions_before, element_descriptions_after)

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
        result_text = response.choices[0].message.content
        print("验证结果:", result_text)

        # 解析JSON
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            return result, element_descriptions_after, elements_after
