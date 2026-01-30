import cv2

def read_image(path):
    img = cv2.imread(path)
    if img is None:
        raise RuntimeError("Image could not be read.")
    return img

def resize_image(img, size=(224, 224)):
    return cv2.resize(img, size)
