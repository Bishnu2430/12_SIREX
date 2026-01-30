import cv2
import imagehash
import face_recognition
from PIL import Image
import numpy as np


def get_perceptual_hash(image_path):
    img = Image.open(image_path)
    return str(imagehash.phash(img))


def extract_face_embeddings(image_path):
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    return [np.array(e).tolist() for e in encodings]


def extract_basic_metadata(image_path):
    img = Image.open(image_path)
    return {
        "resolution": img.size,
        "format": img.format
    }
