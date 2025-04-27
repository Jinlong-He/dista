test_understanding_prompt = """
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

first_window_understanding_prompt = """
## Task
Analyze the provided screenshot of a mobile application interface and determine its category.

## Categories
- Navigation
- Music Player
- Video Player
- Social Media
- Other

## Output Format
Return ONLY the category name as a single string, without any explanations or additional text.

Example response:
"Navigation"
"Music Player"
"""

navigation_audio_prompt = """
## Task Scenario: Navigation Application Testing
You are testing a navigation application. Your primary goal is to complete a navigation task by successfully initiating the navigation process.

## Background
Navigation applications provide route guidance from the current location to a destination. The core functionality involves searching for a destination and starting the navigation process.

## Testing Objective
Successfully start the navigation process in the application. This requires completing the following steps:

1. Find a search bar or destination input field in the application interface
2. Enter a common destination (such as "airport", "train station", or "city center")
3. Select an appropriate destination from the search results
4. Click the start navigation or route planning button
5. Confirm any prompts or dialogs to begin navigation

## Success Criteria
The test is considered successful as soon as the navigation process begins. This is typically indicated by:
- The application displaying a route on the map
- The interface changing to navigation mode
- Navigation controls becoming visible
- Navigation has actually started running with active guidance

You do not need to wait for or confirm voice guidance - simply ensuring that the navigation process has actually initiated and is actively running is sufficient to consider the test successful.
"""

music_player_audio_prompt = """
## Task Scenario: Music Player Application Testing
You are testing a music player application. Your primary goal is to successfully play music through the device's speaker.

## Background
Music player applications are designed to play audio files. The core functionality involves browsing music libraries, selecting tracks, and playing audio content.

## Testing Objective
Successfully play a music track in the application. This requires completing the following steps:

1. Look for and click any prominent play button on the main screen - if available, this is the quickest way to start playback
2. If no direct play button is available, navigate through the music library or collection interface
3. Look for music categories such as songs, albums, artists, or playlists
4. Select any available music track, album, or playlist
5. Activate the play function to start audio playback
6. Verify playback status: Check if the play button has changed to a pause button and if the playback progress is moving

## Success Criteria
The test is considered successful as soon as music playback begins. This is typically indicated by:
- A track beginning to play with visible playback controls
- Play button changing to pause button (confirm the play button has been clicked and changed to pause state)
- Playback progress indicators becoming active (check if the progress bar is moving)
- Track information being displayed
- You may hear audio playing through the device speaker

You do not need to evaluate the audio quality or complete playback of the entire track - simply initiating music playback is sufficient to consider the test successful. However, please ensure that playback has actually started, not just that a track has been selected but not yet playing.
"""

video_player_audio_prompt = """
## Task Scenario: Video Player Application Testing
You are testing a video player application. Your primary goal is to successfully play a video that produces sound through the device's speaker.

## Background
Video player applications are designed to play video files with accompanying audio. The core functionality involves browsing video libraries, selecting videos, and playing content.

## Testing Objective
Successfully play a video with audio in the application. This requires completing the following steps:

1. Look for and click any prominent play button on the main screen - if available, this is the quickest way to start playback
2. If no direct play button is available, navigate through the video library or collection interface
3. Look for video categories such as recent, popular, recommended, etc.
4. Select any available video content
5. Activate the play function to start video playback

## Success Criteria
The test is considered successful as soon as video playback begins. This is typically indicated by:
- Video content starting to play with visible playback controls
- Play button changing to pause button
- Playback progress indicators becoming active
- Video information being displayed

You do not need to evaluate the video quality or complete playback of the entire video - simply initiating video playback is sufficient to consider the test successful.
"""

social_media_audio_prompt = """
## Task Scenario: Social Media Application Testing
You are testing a social media application. Your primary goal is to find and activate any feature that produces sound through the device's speaker.

## Background
Social media applications typically offer multiple features that may produce sound, such as video playback, voice messages, video calls, and more.

## Testing Objective
Find and activate any sound-producing feature in the social media application. You can try several approaches:

1. Look for and play any video content or live streams - if you see any videos or live streaming content, click on them directly as they are the most likely to produce audio
2. Look for voice messages or voice memos features and play any available voice content
3. Try initiating a voice or video call (if supported by the app and safe in a test environment)
4. Look for and tap on any content or buttons with sound icons
5. Check notification sound settings or other system features that might trigger sounds

## Success Criteria
The test is considered successful when the application produces any audible sound through the device's speaker. This could come from:
- Video or audio content playback
- Call ringtones or connection sounds
- Notification or alert sounds
- Any other in-app audio feature

As long as the application produces any sound, regardless of the source, the test is considered successfully completed.
"""

other_audio_prompt = """
## Task Scenario: General Application Sound Testing
You are testing an application that doesn't clearly fall into common categories. Your primary goal is to explore the application and find any feature that produces sound through the device's speaker.

## Background
Various applications may integrate sound features in different ways, including notifications, feedback sounds, media playback, or interactive sound effects.

## Testing Objective
Systematically explore the application to find and activate any sound features. Try the following approaches in order of priority:

1. Look for and tap any obvious media controls (play buttons, sound icons, speaker symbols, etc.)
2. Browse through the main functional areas of the app, looking for sections that might contain audio content
3. Check settings menus for sound, notification, or audio-related options
4. Try completing main tasks or interactions in the app, noting if there are feedback sounds
5. If the app has search functionality, search for terms like "sound", "music", "audio", "video", etc.
6. Look for and use any tutorials, help, or example content, which often contain audio instructions

## Success Criteria
The test is considered successful when the application produces any audible sound through the device's speaker. Success indicators include:
- Any audio content playing
- Interface interaction sounds
- Notification or alert sounds
- System feedback sounds

The primary goal of exploring the application is to discover any sound functionality, regardless of its form. As long as the application produces any sound, the test is considered successfully completed.
"""

camera_prompt = """
## Task Scenario: Camera Access Testing
You are testing an application's camera access functionality. Your primary goal is to find and activate features that launch the device's camera.

## Background
Many applications provide access to the device's camera for taking photos, video calls, scanning QR codes, or augmented reality experiences. These features are typically accessed through specific buttons, menu options, or interaction flows.

## Testing Objective
Find and successfully launch the camera functionality within the application. Try the following approaches in order of priority:

1. Look for and tap any obvious camera icons, photo buttons, or video icons
2. Explore the main interface of the app, looking for areas that might relate to image/video capture
3. Check bottom navigation bars, floating action buttons, or top-right menu options for camera features
4. Look for camera-related functionality in profile, messaging, posting, or content creation areas
5. If the app has search functionality, try searching for terms like "camera", "photo", "scan", etc.
6. Check application settings for media, permissions, or content creation options

## Success Criteria
The test is considered successful when the application successfully launches the device's camera. This is typically indicated by:
- Camera preview screen appearing, showing a live feed
- System permission request for camera access appearing
- Photo/video capture controls becoming visible
- Interface transition to a camera capture mode

Once the camera is successfully launched (either front or rear camera), the test is considered complete. You do not need to actually capture photos or videos - just confirm that the camera has been activated.
"""

micro_prompt = """
## Task Scenario: Microphone Access Testing
You are testing an application's microphone access functionality. Your primary goal is to find and activate features that utilize the device's microphone.

## Background
Many applications provide features that require microphone access for voice recording, voice commands, voice calls, or audio input. These features are typically accessed through specific buttons, menu options, or interaction flows.

## Testing Objective
Find and successfully activate the microphone functionality within the application. Try the following approaches in order of priority:

1. Look for and tap any obvious microphone icons, voice recording buttons, or audio input indicators
2. Explore voice messaging or voice note features in communication apps
3. Check for voice search functionality, often indicated by microphone icons in search bars
4. Look for voice call or video call features in communication apps
5. Explore voice command or voice assistant features in the application
6. Check application settings for audio, microphone, or voice-related options
7. If the app has search functionality, try searching for terms like "voice", "record", "microphone", etc.

## Success Criteria
The test is considered successful when the application successfully activates the device's microphone. This is typically indicated by:
- Microphone permission request dialog appearing
- Voice recording or audio input interface becoming visible
- Audio level indicators or waveforms appearing
- Interface transition to a recording or listening mode
- Confirmation that the app is listening or recording

Once the microphone is successfully activated, the test is considered complete. You do not need to complete a full recording or voice interaction - just confirm that the microphone has been activated.
"""

keyboard_prompt = """
## Task Scenario: Keyboard Input Testing
You are testing an application's text input functionality. Your primary goal is to find and activate features that trigger the device's keyboard.

## Background
Most applications include text input fields for searching, messaging, form filling, or content creation. These input fields typically activate the device's keyboard when tapped.

## Testing Objective
Find and successfully trigger the keyboard within the application. Try the following approaches in order of priority:

1. Look for and tap any obvious text input fields, search bars, or message composition areas
2. Explore content creation features such as post creation, comment sections, or note-taking areas
3. Check for form fields in profile settings, account information, or registration areas
4. Look for search functionality in any section of the application
5. Explore messaging or communication features that would require text input
6. If the app has settings or configuration options, look for customizable fields that might accept text input

## Success Criteria
The test is considered successful when the application successfully triggers the device's keyboard. This is typically indicated by:
- On-screen keyboard appearing at the bottom of the screen
- Text cursor blinking in an input field
- Text input field becoming active or highlighted
- Placeholder text in the input field disappearing when tapped

Once the keyboard is successfully displayed, the test is considered complete. You do not need to complete text entry or form submission - just confirm that the keyboard has been activated.
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


next_event_prompt = """
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

## Response Format
Return your decision strictly in the following JSON format, without any explanatory language:
{{"event_type": "click", "element_id": 3}}
{{"event_type": "input", "element_id": 2, "text": "测试文本"}}
{{"event_type": "swipe", "direction": "up"}}
{{"event_type": "back"}}
{{"event_type": "home"}}
"""


verify_prompt = """
## Scenario: 
{}

## Operations Performed
{}

## Interface Elements Before Operation
{}

## Interface Elements After Operation
{}

## Analysis Task
Please carefully analyze the screenshots and UI element changes before and after the operation, and strictly evaluate according to the following dimensions:

1. Historical Context:
   - Review all previously completed operations
   - Evaluate if the current operation logically follows previous steps
   - Check for any unnecessary repetition of operations

2. Goal Direction:
   - Whether the operation performed is moving in the correct direction toward the scenario goal
   - Whether there is any deviation from the scenario goal
   - If there is deviation, what specific aspects it manifests in

3. Interface Response:
   - Whether the interface has undergone significant changes (ignoring status information such as time and battery)
   - Whether the changes align with the expected operation results
   - If there are no changes, what might be the possible reasons

4. Goal Completion:
   - Considering all executed operations, whether the current state has FULLY completed ALL aspects of the goal described in the scenario
   - Whether ANY further operations are needed to achieve complete success
   - Specific concrete evidence that ALL success criteria have been met
   - Identify any missing elements or incomplete aspects of the goal

5. Termination Assessment:
   - Based on the scenario goal and operation sequence, determine if testing should conclude
   - If termination is appropriate, identify MULTIPLE specific completion indicators that are ALL present
   - If continuation is needed, specify remaining steps required

## Output Requirements
Please return the analysis results strictly in the following format:
{{
    "validity": true/false, // Whether the operation is valid (successfully executed, correct UI response, matches functional intent, and leads to reasonable state change)
    "goal_completion": true/false, // Whether the test scenario's objective has been FULLY achieved with CONCRETE EVIDENCE. Set to true ONLY if ALL success criteria are clearly met with no ambiguity. When in doubt, set to false.
    "analysis": "Detailed analysis of the operation's effectiveness, interface changes, and progress toward the test goal",
    "next_steps": "Suggested next steps based on the current state, including correction if the current path is incorrect"
}}

Ensure your analysis focuses on functional intent rather than exact UI matching, considering the cross-platform adaptation context. 
Be precise, objective, and base your evaluation on evidence from operation history, screenshots, and UI elements. 
If the current operation deviates from the test goal, clearly indicate this and provide correction suggestions.

IMPORTANT: When determining goal completion, be extremely conservative. Set "goal_completion" to true ONLY when you have clear, unambiguous evidence that ALL aspects of the test goal have been achieved. If there is ANY doubt or if ANY success criterion has not been definitively met, set "goal_completion" to false. The testing should continue until there is overwhelming evidence that the goal has been completely achieved.
"""



