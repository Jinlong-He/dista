from .window import Window
from .event import Event

class WTG(object):
    def __init__(self, main_page):
        self.main_pages = [main_page]
        self.pages = [main_page]
        self._adj_list = {}
        self._visited = {}
    
    def add_main_page(self, page):
        if self.add_page(self, page):
            self.main_pages.append(page)
            return True
        return False

    def add_page(self, page):
        if self._is_new_page(page):
            self.pages.append(page)
            return True
        return False
    
    def add_edge(self, src_page, tgt_page, events):
        self.add_page(src_page)
        self.add_page(tgt_page)
        if src_page not in self._adj_list:
            self._adj_list[src_page] = {tgt_page: [events]}
        else:
            if tgt_page not in self._adj_list[src_page]:
                self._adj_list[src_page][tgt_page] = [events]
            else:
                self._adj_list[src_page][tgt_page].append(events)
    
    def _is_new_page(self, new_page):
        for page in self.pages:
            if page._is_same(new_page):
                return False
        return True


class PTGParser(object):
    def parse(cls, file):
        ptg = PTG()
        return ptg

    @classmethod
    def dump(cls, ptg, file, indent=2):
        pass

