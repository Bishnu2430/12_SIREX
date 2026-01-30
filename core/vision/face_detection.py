import logging
logger = logging.getLogger(__name__)

try:
    from deepface import DeepFace
except ImportError:
    DeepFace = None

class FaceDetector:
    def __init__(self, backend: str = "opencv"):
        self.backend = backend

    def detect_faces(self, image_path: str):
        if DeepFace is None:
            logger.warning("deepface not installed - using fallback")
            return []

        try:
            detections = DeepFace.extract_faces(
                img_path=image_path,
                detector_backend=self.backend,
                enforce_detection=False
            )
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return []

        faces = []
        for idx, face in enumerate(detections):
            area = face.get("facial_area", {})
            confidence = face.get("confidence", 0)
            
            if confidence >= 0.85: # Filter low confidence faces
                faces.append({
                    "face_id": idx,
                    "confidence": round(float(confidence), 3),
                    "bbox": [
                        area.get("x", 0),
                        area.get("y", 0),
                        area.get("w", 100),
                        area.get("h", 100)
                    ]
                })

        return faces