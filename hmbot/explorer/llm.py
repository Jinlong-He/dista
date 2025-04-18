from openai import OpenAI
from .explorer import Explorer
from ..ptg import PTG
API_KEY='sk-2b3e688d49584db394caaff1dea36d4a'


class LLM(Explorer):
    def __init__(self, device=None, app=None, model='', api_key=API_KEY):
        super.__init__(device, app)
        self.model = model
        self.api_key = api_key
    
    def explore(self, ptg=PTG(), **termination):
        pass

    def select(self, page=None, **description):
        """
        根据提供的控件描述返回对应的控件
        """
        nodes = page.vht.all(clickable='true')
        screenshot = page.img
        images = []
        for node in nodes:
            images.append(_crop(screenshot, node.attribute['bounds']))

        # 显示可点击控件
        # for image in images:
        #     cv2.imshow('image', image)
        #     cv2.waitKey(0)
        #     cv2.destroyAllWindows()

        clickable_weights_description = self._add_information(nodes, screenshot, images)
        index = int(self._ask_llm_select_node(clickable_weights_description, **description))
        # cv2.imshow('image', images[index])
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        return nodes[index]


    def _add_information(self, nodes, screenshot, images):
        """
        提取每个控件中的信息
        """
        clickable_weights_description = []
        image_list = []
        for index, node in enumerate(nodes):
            node_info = {'index': index}
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


    def _ask_llm_image(self, screenshot, components):
        """
        发送截图和多个控件截图给LLM，获取每个控件的描述列表
        """
        # 获取组件数量
        component_count = len(components)
        
        description_prompt = f"""
## Task
I have uploaded a screenshot of a mobile app interface followed by {component_count} images of clickable components from that interface.
Please analyze each component image in order and briefly describe its function (max 15 Chinese characters per description).

## Requirements
- You MUST provide exactly {component_count} descriptions in the exact order of the component images
- Return your answer as a Python list with exactly {component_count} strings
- Each description should be concise and functional
- Do not include any additional explanations

## Example response format
['返回按钮', '搜索框', '设置按钮', '添加设备']

Remember: Your response MUST contain exactly {component_count} descriptions in a list.
"""
        # Build content with all component images
        content = [{"type": "text", "text": description_prompt},
                  {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(screenshot)}"}}]

        # Add each component image with a label
        for i, component in enumerate(components):
            content.append({"type": "text", "text": f"Component {i+1} of {component_count}:"})
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(component)}"}})

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

        # 尝试解析返回的列表
        try:
            # 使用正则表达式匹配列表格式
            match = re.search(r'\[(.*)\]', response_text, re.DOTALL)
            if match:
                # 提取列表内容并分割成单独的项
                items_str = match.group(1)
                # 分割字符串，处理带引号的项
                items = re.findall(r'\'([^\']*?)\'|\"([^\"]*?)\"', items_str)
                # 合并每个匹配组的非空值
                descriptions = [item[0] if item[0] else item[1] for item in items]
                return descriptions
            else:
                # 如果没有找到列表格式，返回空列表
                return ["未知功能"] * len(components)
        except Exception as e:
            print(f"解析响应时出错: {e}")
            return ["未知功能"] * len(components)



    def _ask_llm_select_node(self, clickable_weights_description, **description):
        """
        发送控件描述给LLM，获取最佳控件
        """
        select_prompt = """
## Task
I have uploaded a list of clickable components on the current page. Please select the best one based on the following description.

## Component List
{}

## Description
{}

## Instructions
- Analyze the component list and find the component that best matches the description
- Return ONLY the index number of the best matching component
- Do not include any explanations, just the number
- If no component matches well, return the closest match

Example response:
2
"""

        formatted_prompt = select_prompt.format(str(clickable_weights_description), str(description))
        # print(formatted_prompt)
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
                        {"type": "text", "text": formatted_prompt},
                    ],
                },
            ],
            stream=False,
        )
        response_text = response.choices[0].message.content
        # print(response_text)
        return response_text



