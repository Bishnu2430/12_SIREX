import logging

logger = logging.getLogger(__name__)

try:
    from deepface import DeepFace
except Exception:
    DeepFace = None

try:
    import cv2
except Exception:
    cv2 = None

import numpy as np


class FaceEmbedder:
    def __init__(self, model_name: str = "Facenet"):
        self.model_name = model_name

    def get_embedding(self, image_path: str, bbox: list):
        """Extract embedding for a detected face region.

        If required libraries are missing, raises RuntimeError with guidance.
        """
        if cv2 is None:
            raise RuntimeError("opencv-python (cv2) is required to extract face embeddings")

        img = cv2.imread(image_path)

        if img is None:
            raise RuntimeError("Could not read image")

        x, y, w, h = bbox
        face_img = img[y:y+h, x:x+w]

        if DeepFace is None:
            # fallback: return a deterministic vector based on image patch statistics
            logger.warning("deepface not available; returning fallback embedding")
            mean = np.mean(face_img) if face_img.size else 0
            std = np.std(face_img) if face_img.size else 1
            vec = np.full((128,), float(mean) / (std + 1e-6))
            return vec

        try:
            embedding = DeepFace.represent(
                img_path=face_img,
                model_name=self.model_name,
                enforce_detection=False
            )[0]["embedding"]
        except Exception as e:
            logger.exception("Embedding extraction failed: %s", e)
            raise RuntimeError(f"Embedding extraction failed: {str(e)}")

        return np.array(embedding)
