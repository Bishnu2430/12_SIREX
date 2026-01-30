import logging

logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None


class ObjectDetector:
    def __init__(self, model_path: str = "yolov8n.pt"):
        # yolov8n = lightweight, fast
        if YOLO is None:
            logger.warning("ultralytics YOLO not available; ObjectDetector will be a no-op")
            self.model = None
            return

        try:
            self.model = YOLO(model_path)
        except Exception:
            logger.exception("Failed to load YOLO model; object detection disabled")
            self.model = None

    def detect(self, image_path: str):
        if self.model is None:
            return []

        results = self.model(image_path)

        detections = []

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = self.model.names[cls_id]
                confidence = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                detections.append({
                    "label": label,
                    "confidence": round(confidence, 3),
                    "bbox": [x1, y1, x2, y2]
                })

        return detections