from .page import Page
from .vht import VHT

class Window(object):
    def __init__(self, vht, img):
        self.vht = vht
        self.img = img
        self.bundle = ''
        self.page = ''
        self.resource = {}
        # roots = vht.roots()
        # self._pages = []
        # for root in roots:
        #     name = root.attribute['page']
        #     bundle = root.attribute['bundle']
        #     from .cv import _crop
        #     page = Page(name=name, vht=VHT(root), img=_crop(screen, root.attribute['bounds']), ability='', bundle=bundle)
        #     self._pages.append(page)
    def __call__(self, **kwds):
        return self.vht(**kwds)
    
    def current_page(self, app):
        for page in self._pages:
            if page.bundle == app.bundle:
                return page

    def _is_same(self, new_window):
        # todo
        return False
        if isinstance(new_window, Window):
            vht_sim = self.vht_similarity(new_window)
            img_sim = self.img_similarity(new_window)
            print(f'vht_sim={vht_sim}, img_sim={img_sim}')
        return False

    def vht_similarity(self, new_window):
        # todo
        vht_sim = 0
        return vht_sim

    def img_similarity(self, new_window):
        # todo
        img_sim = 0
        return img_sim