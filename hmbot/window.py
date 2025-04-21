from .page import Page
from .vht import VHT

class Window(object):
    def __init__(self, vht, img):
        self.vht = vht
        self.img = img
        # roots = vht.roots()
        # self._pages = []
        # for root in roots:
        #     name = root.attribute['page']
        #     bundle = root.attribute['bundle']
        #     from .cv import _crop
        #     page = Page(name=name, vht=VHT(root), img=_crop(screen, root.attribute['bounds']), ability='', bundle=bundle)
        #     self._pages.append(page)
    def __call__(self, **kwds):
        return self.vht(kwds)
    
    def current_page(self, app):
        for page in self._pages:
            if page.bundle == app.bundle:
                return page
