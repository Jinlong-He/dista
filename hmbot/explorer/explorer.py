from abc import ABC, abstractmethod
from ..proto import ExploreMission
# from ..wtg import PTG
from ..device import Device
from ..app.app import App
from ..event import Event

class Explorer(ABC):
    """
    this interface describes a explorer
    """
    def __init__(self, device=None, app=None):
        if isinstance(device, Device):
            self.device = device
        if isinstance(app, App):
            self.app = app

    def explore(self, **goal):
        window = self.device.dump_window(refresh=True)
        while (not self.should_terminate(goal)):
            events = self.best(window, goal)
            self.device.execute(events=events)
            window = self.device.dump_window(refresh=True)
            if not self.verify(window, goal):
                pass
    
    @abstractmethod
    def best(self, window, **goal):
        pass

    @abstractmethod
    def verify(self, window, **goal):
        pass

    @abstractmethod
    def should_terminate(self, **goal):
        pass

