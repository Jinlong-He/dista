import cv2
import numpy as np
import time
import math
import base64

def read(img_path):
    img = cv2.imread(img_path, cv2.IMREAD_COLOR)
    return img

def write(img_path, img):
    cv2.imwrite(img_path, img)

def _crop(img, bound):
    (x1, y1), (x2, y2) = bound
    return img[y1:y2, x1:x2]

def encode_image(image):
    _, buffer = cv2.imencode('.jpeg', image)
    encoded_image = base64.b64encode(buffer).decode('utf-8')
    return encoded_image

