from .window import Window
from .event import Event
import json, re

class WTG(object):
    def __init__(self):
        self.main_windows = []
        self.windows = []
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
            self._adj_list[window] = {}
            return True
        return False
    
    def add_edge(self, src_window, tgt_window, events):
        self.add_window(src_window)
        self.add_window(tgt_window)
        self._adj_list[src_window][tgt_window] = events
    
    def _is_new_window(self, new_window):
        for window in self.windows:
            if window._is_same(new_window):
                return False
        return True
    
    def _json_list(self):
        res = []
        for id in range(len(self.windows)):
            src_window = self.windows[id]
            vht_file, img_file = src_window._dump(id)
            edge_list = []
            for (tgt_window, events) in self._adj_list[src_window].items():
                tgt_id = self.windows.index(tgt_window)
                event_list = [event._json() for event in events]
                edge_dict = {'target_id': tgt_id,
                             'events': event_list}
                edge_list.append(edge_dict)
            src_window_dict = src_window._dict(vht_file, img_file)
            src_window_dict['id'] = id
            res.append({'info': src_window_dict, 
                        'edge': edge_list})
        return res



class WTGParser(object):
    def parse(cls, file):
        wtg = WTG()
        return wtg

    @classmethod
    def dump(cls, wtg, file, indent=2):
        with open(file, 'w') as write_file:
            json.dump(wtg._json_list(), write_file, indent=indent, ensure_ascii=False)

