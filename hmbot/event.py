from abc import ABC, abstractmethod
from .proto import SystemKey

class Event(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def execute(self):
        pass

class ClickEvent(Event):
    def __init__(self, device, window, x, y):
        self.device = device
        self.window = window
        self.x = x
        self.y = y

    def execute(self):
        self.device.click(self.x, self.y)

class InputEvent(Event):
    def __init__(self, device, window, node, text):
        self.device = device
        self.window = window
        self.node = node
        self.text = text

    def execute(self):
        self.device.input(self.node, self.text)

class KeyEvent(Event):
    def __init__(self, device, window, key):
        self.device = device
        self.window = window
        self.key = key

    def execute(self):
        getattr(self.device, self.key)()