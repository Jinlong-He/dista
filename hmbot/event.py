from abc import ABC, abstractmethod
from .proto import SystemKey

class Event(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def execute(self):
        pass

class ClickEvent(Event):
    def __init__(self, node):
        self.node = node

    def execute(self):
        self.node.click()

class LongClickEvent(Event):
    def __init__(self, node):
        self.node = node
    def execute(self):
        self.node.long_click()

class InputEvent(Event):
    def __init__(self, node, text):
        self.node = node
        self.text = text

    def execute(self):
        self.node.input(self.text)

class SwipeExtEvent(Event):
    def __init__(self, device, window, direction):
        self.device = device
        self.window = window
        self.direction = direction

    def execute(self):
        self.device.swipe_ext(self.direction)

class KeyEvent(Event):
    def __init__(self, device, window, key):
        self.device = device
        self.window = window
        self.key = key

    def execute(self):
        getattr(self.device, self.key)()