from enum import Enum
from dataclasses import dataclass

class OperatingSystem(str, Enum):
    HARMONY = 'harmony'
    ANDROID = 'android'

class SwipeDirection(str, Enum):
    LEFT = 'left'
    RIGHT = "right"
    UP = "up"
    DOWN = "down"

class SystemKey(str, Enum):
    BACK = 'back'
    HOME = "home"
    RECENT = "recent"
    HOP = "hop"
    RESTART = "restart_app"

class ExploreStrategy(str, Enum):
    DFS = 'dfs'
    BFS = 'bfs'
    QLN = 'qln'
    LLM = 'llm'

class ExploreMission(str, Enum):
    IMC = 'INITIAL_MODEL_CONSTRUCTION'

class TerminateCondition(str, Enum):
    IMC = 'INITIAL_MODEL_CONSTRUCTION'

class LLMUrl(str, Enum):
    DS = 'https://api.deepseek.com'

class DisplayRotation(int, Enum):
    ROTATION_0 = 0
    ROTATION_90 = 1
    ROTATION_180 = 2
    ROTATION_270 = 3

@dataclass
class DisplayInfo:
    sdk: str
    width: int
    height: int
    rotation: DisplayRotation

class ResourceType:
    AUDIO = 'audio'
    CAMERA = 'camera'
    MICRO = 'micro'
    KEYBOARD = 'keyboard'

class AudioStatus:
    START = 'START'
    START_ = 'START*'
    PAUSE = 'PAUSE'
    PAUSE_ = 'PAUSE*'
    DUCK = 'DUCK'
    STOP = 'STOP'

class MicroStatus:
    START = 'start'
    STOP = 'stop'

class ExploreKind:
    TEST = 'test'
    HARDWARE = 'hardware'
