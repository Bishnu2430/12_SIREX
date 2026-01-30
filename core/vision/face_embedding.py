import logging
import numpy as np

logger = logging.getLogger(__name__)

try:
    from deepface import DeepFace
    import cv2
except ImportError:
    DeepFace = None
    cv2 = None

class FaceEmbedder:
    def __init__(self, model_name: str = "Facenet"):
        self.model_name = model_name

    def get_embedding(self, image_path: str, bbox: list):
        if cv2 is None or DeepFace is None:
            logger.warning("Required libraries not available")
            return np.random.rand(128)  # Fallback random embedding

        try:
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError("Could not read image")

            x, y, w, h = bbox
            x, y, w, h = int(x), int(y), int(w), int(h)
            face_img = img[y:y+h, x:x+w]

            if face_img.size == 0:
                raise ValueError("Empty face region")

            embedding = DeepFace.represent(
                img_path=face_img,
                model_name=self.model_name,
                enforce_detection=False
            )[0]["embedding"]

            return np.array(embedding)
        except Exception as e:
            logger.error(f"Embedding extraction failed: {e}")
            return np.random.rand(128)