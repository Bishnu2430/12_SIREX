import os, logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from core.media.intake import MediaIntake
from core.media.frame_extractor import FrameExtractor
from core.media.audio_extractor import AudioExtractor
from core.media.metadata import MetadataExtractor
from core.vision.object_detection import ObjectDetector
from core.vision.face_detection import FaceDetector
from core.vision.face_embedding import FaceEmbedder
from core.vision.scene_classification import SceneClassifier
from core.vision.ocr_reader import OCRReader
from core.vision.landmark_similarity import LandmarkSimilarity
from core.audio.speech_detection import SpeechDetector
from core.audio.language_detection import LanguageDetector
from core.audio.sound_classification import SoundClassifier
from core.audio.speaker_embedding import SpeakerEmbedder
from agent.controller import AgentController
from graph.neo4j_client import Neo4jClient
from app.config import config

app = FastAPI(title="OSINT Exposure Intelligence System", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

controller = AgentController()
graph_client = Neo4jClient()

@app.get("/")
async def root():
    return {"status": "online", "service": "OSINT Exposure Intelligence System"}

@app.post("/analyze")
async def analyze_media(file: UploadFile = File(...)):
    try:
        os.makedirs(config.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(config.UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        intake = MediaIntake(file_path)
        info = intake.process()
        metadata = MetadataExtractor(file_path).extract()
        
        frames = []
        audio_path = None
        
        if info["media_type"] == "video":
            try:
                frames = FrameExtractor(file_path, info["workspace"]).extract()["frames"]
                audio_path = AudioExtractor(file_path, info["workspace"]).extract()["audio_path"]
            except: pass
        elif info["media_type"] == "image":
            frames = [{"path": file_path}]
        elif info["media_type"] == "audio":
            audio_path = file_path
        
        all_faces, all_embeddings, all_objects, all_scenes, all_text, all_landmarks = [], [], [], [], [], []
        
        obj_detector = ObjectDetector(config.YOLO_MODEL_PATH)
        face_detector = FaceDetector(config.FACE_DETECTION_BACKEND)
        face_embedder = FaceEmbedder(config.FACE_EMBEDDING_MODEL)
        scene_classifier = SceneClassifier()
        ocr_reader = OCRReader()
        landmark_sim = LandmarkSimilarity(config.LANDMARK_DIR)
        
        for frame in frames[:config.MAX_FRAMES_TO_PROCESS]:
            img_path = frame["path"]
            try: all_objects.extend(obj_detector.detect(img_path))
            except: pass
            try:
                faces = face_detector.detect_faces(img_path)
                all_faces.extend(faces)
                for face in faces:
                    all_embeddings.append(face_embedder.get_embedding(img_path, face["bbox"]))
            except: pass
            try: all_scenes.extend(scene_classifier.classify(img_path))
            except: pass
            try: all_text.extend(ocr_reader.read_text(img_path))
            except: pass
            try: all_landmarks.extend(landmark_sim.compare(img_path))
            except: pass
        
        audio_signals = {}
        if audio_path and os.path.exists(audio_path):
            try: audio_signals["speech"] = SpeechDetector().detect(audio_path)
            except: pass
            try: audio_signals["language"] = LanguageDetector().detect(audio_path)
            except: pass
            try: audio_signals["environment"] = SoundClassifier().classify(audio_path)
            except: pass
            try: audio_signals["speaker_embedding"] = SpeakerEmbedder().extract(audio_path).tolist()
            except: pass
        
        signals = {
            "faces": all_faces, "embeddings": all_embeddings, "objects": all_objects,
            "scene": all_scenes, "ocr_text": all_text, "landmarks": all_landmarks,
            "metadata": metadata, "audio": audio_signals,
            "file_path": file_path
        }
        
        result = controller.run_pipeline(signals, info["session_id"])
        
        return {
            "session_id": info["session_id"],
            "media_type": info["media_type"],
            "report": result["report"],
            "summary": {
                "faces_detected": len(all_faces),
                "objects_detected": len(all_objects),
                "exposures_identified": len(result.get("exposures", []))
            }
        }
    except Exception as e:
        logger.exception(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph")
async def get_graph():
    data = {"nodes": [], "links": []}
    try:
        data = graph_client.get_graph_data()
    except:
        pass
    
    # Fallback to in-memory graph from latest session if DB is empty/down
    if not data.get("nodes") and controller.latest_graph_data.get("nodes"):
        return controller.latest_graph_data
        
    return data

@app.get("/logs/{session_id}")
async def get_session_logs(session_id: str):
    try:
        return {"session_id": session_id, "logs": controller.observer.get_logs(session_id)}
    except:
        return {"session_id": session_id, "logs": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)