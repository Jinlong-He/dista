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

    def explore(self, key='test', value=''):
        pass
    
    # @abstractmethod
    # def best(self, window, **goal):
    #     pass
    #
    # @abstractmethod
    # def verify(self, window_before, window_after, **goal):
    #     pass


