extraction_prompt = """
## BACKGROUND
Suppose you are mobile phone app testers specialized in cross-platform testing. You are good at extracting testing scenarios from source scripts and understanding the functional intent behind them. Here is the source script to be extracted:
```python
{}
```
## YOUR TASK
Please read the source script carefully, try to understand it and ultimately answer the following questions.
1.What kind of functionality is the script designed to test?
2.Summarize the detailed test steps in the testing procedure(including `operation type`, `parameters` and `description`).
3.What is the expected result of implementation? 
Additionally, I've provided screenshots of the function tested by this script to assist you in further understanding.
Answer these three questions one by one to ensure the accuracy.

## CONSTRAINT
Your output must strictly be a valid jSON object with three keys!
`Target Function`: the answer to the first question.
`Test Steps`: the answer to the second question. Its format must be a list, where each item is a sublist containing `operation type`, `parameters` and `description`.
`Result`: the answer to the third question.
Return **only** the JSON object without any additional text, explanations, or formatting.

## EXAMPLE
Example target script: 
`d(description="确定").click()
d(resourceId="com.android.settings:id/device_name").set_text("Xiaomi 14")`
Example answers: 
```json
{{
    "Target Function": "Implement a click on the OK button.",
    "Test Steps": [
        {{
            "Operation Type": "Click",
            "Parameters": "description=\"确定\"",
            "description": "A click on the OK button."
        }},
        {{
            "Operation Type": "Input",
            "Parameters": "resourceId=\"com.android.settings:id/device_name\", text=\"Xiaomi 14\"",
            "description": "Enter 'Xiaomi 14' as the new device name."
        }},
    ],
    "Result": "Button is successfully clicked to achieve the action."
}}
```
"""


image_description_prompt = """
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

select_prompt = """
## Task
I have uploaded a list of clickable components on the current page. Please select the best one based on the following description.

## Component List
{}

## Description
{}

## Instructions
- Analyze the component list and find the component that best matches the description
- Return ONLY the element_id number of the best matching component
- Do not include any explanations, just the number
- If no component matches well, return the closest match

Example response:
2
"""


next_action_prompt = """
## Test Scenario: 
{}
Note: The original test scenario is from Android platform and needs to be adapted to the HarmonyOS platform. There may be differences in UI layouts, element identifiers, and interaction patterns between these platforms.

## Clickable Elements on the Current Screen:
{}

## Operations Completed So Far:
{}

## Feedback and Suggestions from the Previous Operation:
{}

## Your Task
Based on the test scenario, the current screenshot, the list of clickable elements, the operations completed, 
and the feedback and suggestions from the previous operation, determine what the next operation should be.

Consider the following when making your decision:
1. Focus on functional intent rather than exact UI element matching, adapting to the current UI state.
2. Choose the most appropriate element that serves the same purpose as in the original scenario.
3. If the target element is not visible on the current screen, prioritize swiping operations to reveal more content before attempting other actions.
4. When swiping, consider both direction (vertical/horizontal) and context of what you're looking for, paying attention to visual cues like partial items at screen edges.
5. If exact elements are unavailable after swiping, look for alternatives with similar functionality.
6. Recognize equivalent functionality across different naming conventions (e.g., "屏幕超时", "自动锁屏", "休眠" may all refer to the same auto-lock functionality).
7. Avoid repeating operations that have already been executed, based on previous feedback.

## Available Operations
You can only choose from the following types of actions:
1. "click": Specify the element ID from the provided list
2. "input": Specify the element ID and the text to be entered
3. "swipe": Specify the direction ("up", "down", "left", "right")
4. "back": Press the back button
5. "home": Return to the home screen (close the application)
6. "finish": If the test scenario is finished

## Response Format
Return your decision strictly in the following JSON format, without any explanatory language:
{{"action": "click", "element_id": 3}}
{{"action": "input", "element_id": 2, "text": "测试文本"}}
{{"action": "swipe", "direction": "up"}}
{{"action": "back"}}
{{"action": "home"}}
{{"action": "finish"}}
"""


verify_prompt = """
## Test Scenario: The original test scenario comes from similar applications on different platforms and needs to be adapted to the current target platform and application. There may be differences in interfaces and interaction methods between them.
{}

## Operations Performed
{}

## Interface Elements Before Operation
{}

## Interface Elements After Operation
{}

## Analysis Task
Please carefully analyze the screenshots and UI element changes before and after the operation, and strictly evaluate according to the following dimensions:

1. Goal Direction:
   - Whether the operation performed is moving in the correct direction toward the test goal
   - Whether there is any deviation from the test goal
   - If there is deviation, what specific aspects it manifests in

2. Interface Response:
   - Whether the interface has undergone significant changes (ignoring status information such as time and battery)
   - Whether the changes align with the expected operation results
   - If there are no changes, what might be the possible reasons

3. Goal Completion:
   - Whether the current state has completed the result described in the test scenario
   - Whether further operations are needed
   - Specific manifestations of the completion level

4. Next Step Recommendations:
   - Based on the current state, what operations should be taken to continue testing
   - If the current path is incorrect, how to adjust


## Output Requirements
Please return the analysis results strictly in the following format:
{{
    "validity": true/false, // Whether the operation is valid (successfully executed, correct UI response, matches functional intent, and leads to reasonable state change)
    "goal_completion": true/false, // Whether the test scenario's objective has been fully achieved
    "analysis": "Detailed analysis of the operation's effectiveness, interface changes, and progress toward the test goal",
    "next_steps": "Suggested next steps based on the current state, including correction if the current path is incorrect"
}}

Ensure your analysis focuses on functional intent rather than exact UI matching, considering the cross-platform adaptation context. 
Be precise, objective, and base your evaluation solely on the evidence from screenshots and UI elements. 
If the current operation deviates from the test goal, clearly indicate this and provide correction suggestions.

"""



