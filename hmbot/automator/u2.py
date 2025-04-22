from .automator import Automator
from loguru import logger
from ..vht import VHTParser, VHT
from ..proto import SwipeDirection, DisplayInfo, DisplayRotation, SystemKey
from ..app.app import App
import uuid, os, shutil
import uiautomator2

class U2(Automator):
    def __init__(self, device):
        self._serial = device.serial
        self._driver = uiautomator2.connect(self._serial)
        self._display_info = None
        logger.debug("uiautomator2 is connected to device:%s" %(self._serial))

    def install_app(self, app):
        if isinstance(app, App):
            self._driver.app_install(app.app_path)
        else:
            raise TypeError('expected an App, not %s' % type(app).__name__)

    def uninstall_app(self, app):
        pass
        # if isinstance(app, App):
        #     self._driver.uninstall_app(app.package_name)
        # else:
        #     raise TypeError('expected an App, not %s' % type(app).__name__)

    def start_app(self, app):
        if isinstance(app, App):
            self._driver.app_start(app.package_name)
        else:
            raise TypeError('expected an App, not %s' % type(app).__name__)

    def stop_app(self, app):
        if isinstance(app, App):
            self._driver.app_stop(app.package_name)
        else:
            raise TypeError('expected an App, not %s' % type(app).__name__)

    def restart_app(self, app):
        self.stop_app(app)
        self.start_app(app)
    
    def click(self, x, y):
        return self._driver.click(x, y)

    def long_click(self, x, y):
        return self._driver.long_click(x, y)

    def drag(self, x1, y1, x2, y2, speed):
        if x1 < 1 and y1 < 1 and x2 < 1 and y2 < 1:
            self.display_info(refresh=True)
            width = self._display_info.width
            height = self._display_info.height
            # print(x1*width, y1*height, x2*width, y2*height, speed)
            duration = speed/4000
            return self._driver.drag(x1*width, y1*height, x2*width, y2*height, duration)
        else:
            return self._driver.drag(x1, y1, x2, y2, duration)

    def swipe(self, x1, y1, x2, y2, speed):
        if x1 < 1 and y1 < 1 and x2 < 1 and y2 < 1:
            self.display_info(refresh=True)
            width = self._display_info.width
            height = self._display_info.height
            duration = speed/4000
            return self._driver.swipe(x1 * width, y1 * height, x2 * width, y2 * height, duration)
        else:
            return self._driver.swipe(x1, y1, x2, y2, duration)

    def swipe_ext(self, direction, scale=0.4):
        #to check
        if direction == SwipeDirection.LEFT :
            self.drag(0.5, 0.5, 0.5-scale, 0.5)
        elif direction == SwipeDirection.RIGHT :
            self.drag(0.5, 0.5, 0.5+scale, 0.5)
        elif direction == SwipeDirection.UP :
            self.drag(0.5, 0.5, 0.5, 0.5-scale)
        elif direction == SwipeDirection.DOWN :
            self.drag(0.5, 0.5, 0.5, 0.5+scale)

    def input(self, node, text):
        id = node.attribute['id']
        if id:
            self._driver(resourceId=id).set_text(text)

    def dump_hierarchy(self, device):
        root = VHTParser._parse_adb_xml(self._driver.dump_hierarchy(compressed=True), device)._root
        # root_child = max(root._children, key=lambda child:
        #     (child.attribute['bounds'][1][0] - child.attribute['bounds'][0][0]) * (child.attribute['bounds'][1][1] - child.attribute['bounds'][0][1]))
        # root_child.attribute['type'] = 'root'
        # root_child.attribute['page'] = self._current()['activity']
        return VHT(root)

    def screenshot(self, path=''):
        img = self._driver.screenshot(format='opencv')
        if isinstance(path, str):
            if path:
                from ..cv import write
                write(path, img)
            return img
        else:
            raise TypeError('expected an str, not %s' % type(path).__name__)
    
    def display_info(self, refresh=True):
        if self._display_info is None or refresh:
            info = self._driver.info
            self._display_info = DisplayInfo(sdk=info['sdkInt'],
                                             width=info['displayWidth'],
                                             height=info['displayHeight'],
                                             rotation=info['displayRotation'])
        return self._display_info

    def home(self):
        self._driver.press(SystemKey.HOME)

    def back(self):
        self._driver.press(SystemKey.BACK)

    def recent(self):
        self._driver.press(SystemKey.RECENT)

    def _current(self):
        return self._driver.app_current()