from abc import ABC, abstractmethod
from .proto import SystemKey

class Event(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def execute(self):
        pass

class ClickEvent(Event):
    def __init__(self, device, page, x, y):
        self.device = device
        self.page = page
        self.x = x
        self.y = y

    def execute(self):
        self.device.click(self.x, self.y)

class InputEvent(Event):
    def __init__(self, device, page, x, y):
        self.device = device
        self.page = page
        self.x = x
        self.y = y

    def execute(self):
        self.device.click(self.x, self.y)

class KeyEvent(Event):
    def __init__(self, device, page, key):
        self.device = device
        self.page = page
        self.key = key

    def execute(self):
        getattr(self.device, self.key)()