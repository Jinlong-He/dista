from .page import Page
from .vht import VHT

class Window(object):
    def __init__(self, vht, screen):
        roots = vht.roots()
        self._pages = []
        for root in roots:
            name = root.attribute['page']
            bundle = root.attribute['bundle']
            from .cv import _crop
            page = Page(name=name, vht=VHT(root), img=_crop(screen, root.attribute['bounds']), ability='', bundle=bundle)
            self._pages.append(page)
    
    def current_page(self, app):
        for page in self._pages:
            if page.bundle == app.bundle:
                return page
