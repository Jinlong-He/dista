from .window import Window
from .event import Event

class WTG(object):
    def __init__(self, main_window):
        self.main_windows = [main_window]
        self.windows = [main_window]
        self._adj_list = {}
        self._visited = {}
    
    def add_main_window(self, window):
        if self.add_window(window):
            self.main_windows.append(window)
            return True
        return False

    def add_window(self, window):
        if self._is_new_window(window):
            self.windows.append(window)
            return True
        return False
    
    def add_edge(self, src_window, tgt_window, events):
        self.add_window(src_window)
        self.add_window(tgt_window)
        if src_window not in self._adj_list:
            self._adj_list[src_window] = {tgt_window: [events]}
        else:
            if tgt_window not in self._adj_list[src_window]:
                self._adj_list[src_window][tgt_window] = [events]
            else:
                self._adj_list[src_window][tgt_window].append(events)
    
    def _is_new_window(self, new_window):
        for window in self.windows:
            if window._is_same(new_window):
                return False
        return True


class PTGParser(object):
    def parse(cls, file):
        ptg = PTG()
        return ptg

    @classmethod
    def dump(cls, ptg, file, indent=2):
        pass

