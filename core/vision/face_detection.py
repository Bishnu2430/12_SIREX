import logging

logger = logging.getLogger(__name__)

try:
    from deepface import DeepFace
except Exception:
    DeepFace = None


class FaceDetector:
    def __init__(self, backend: str = "retinaface"):
        self.backend = backend

    def detect_faces(self, image_path: str):
        """Detect faces and return bounding boxes + confidence.

        If the `deepface` package is not available, raises RuntimeError with guidance.
        """
        if DeepFace is None:
            raise RuntimeError("deepface is not installed; please install deepface to enable face detection")

        try:
            detections = DeepFace.extract_faces(
                img_path=image_path,
                detector_backend=self.backend,
                enforce_detection=False
            )
        except Exception as e:
            logger.exception("Face detection failed: %s", e)
            raise RuntimeError(f"Face detection failed: {str(e)}")

        faces = []

        for idx, face in enumerate(detections):
            area = face.get("facial_area", {})
            confidence = face.get("confidence", 0)

            faces.append({
                "face_id": idx,
                "confidence": round(float(confidence), 3),
                "bbox": [
                    area.get("x"),
                    area.get("y"),
                    area.get("w"),
                    area.get("h")
                ]
            })

        return faces
