import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    YOLO_MODEL_PATH = "models/yolov8n.pt"
    LANDMARK_DIR = "models/landmarks"
    LOG_DIR = "storage/logs"
    UPLOAD_DIR = "storage/uploads"
    SESSION_DIR = "storage/sessions"
    
    FACE_DETECTION_BACKEND = "ssd"
    FACE_EMBEDDING_MODEL = "Facenet"
    FRAME_EXTRACTION_INTERVAL = 2
    MAX_FRAMES_TO_PROCESS = 10
    
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    
    @classmethod
    def init_directories(cls):
        for dir_path in [cls.LOG_DIR, cls.UPLOAD_DIR, cls.SESSION_DIR, cls.LANDMARK_DIR, "models"]:
            os.makedirs(dir_path, exist_ok=True)

config = Config()
config.init_directories()