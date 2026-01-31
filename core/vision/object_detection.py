import logging
logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

class ObjectDetector:
    def __init__(self, model_path: str = None):
        if YOLO is None:
            logger.warning("ultralytics not installed - object detection disabled")
            self.model = None
            return

        # Use config if available
        if model_path is None:
            try:
                from app.config import config
                model_path = config.YOLO_MODEL_PATH
            except:
                model_path = "models/yolov8n.pt"

        try:
            self.model = YOLO(model_path)
            logger.info(f"YOLO model loaded: {model_path}")
        except Exception as e:
            logger.error(f"Failed to load YOLO: {e}")
            self.model = None

    def detect(self, image_path: str):
        if self.model is None:
            return []

        try:
            results = self.model(image_path, verbose=False, conf=0.5)
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
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return []