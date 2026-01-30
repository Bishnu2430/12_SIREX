import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from core.media.intake import MediaIntake
from core.media.metadata import MetadataExtractor
from graph.neo4j_client import Neo4jClient
from agent.controller import AgentController

app = FastAPI(title="OSINT Exposure Intelligence System")


# Enable CORS for frontend dev usage
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

controller = AgentController()
graph_client = Neo4jClient()

@app.post("/analyze")
async def analyze_media(file: UploadFile = File(...)):
    # Save uploaded file
    os.makedirs("storage/uploads", exist_ok=True)
    file_path = f"storage/uploads/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # ---------- PHASE 1: Media Intake ----------
    intake = MediaIntake(file_path)
    info = intake.process()

    metadata = MetadataExtractor(file_path).extract()

    frames = []
    audio_path = None

    # Defer heavy imports to runtime; provide helpful error responses if unavailable
    try:
        from core.media.frame_extractor import FrameExtractor
        from core.media.audio_extractor import AudioExtractor
        from core.vision.object_detection import ObjectDetector
        from core.vision.face_detection import FaceDetector
        from core.vision.face_embedding import FaceEmbedder
        from core.vision.scene_classification import SceneClassifier
        from core.vision.ocr_reader import OCRReader
        from core.vision.landmark_similarity import LandmarkSimilarity
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Missing media/vision dependencies: {e}")

    if info["media_type"] == "video":
        frames = FrameExtractor(file_path, info["workspace"]).extract()["frames"]
        audio_path = AudioExtractor(file_path, info["workspace"]).extract()["audio_path"]
    else:
        frames = [{"path": file_path}]

    # ---------- PHASE 2: Vision Processing ----------
    obj_detector = ObjectDetector("models/yolov8n.pt")
    face_detector = FaceDetector()
    face_embedder = FaceEmbedder()
    scene_classifier = SceneClassifier()
    ocr_reader = OCRReader()
    landmark_sim = LandmarkSimilarity()

    all_faces = []
    all_embeddings = []
    all_objects = []
    all_scenes = []
    all_text = []
    all_landmarks = []

    for frame in frames:
        img_path = frame["path"]

        all_objects.extend(obj_detector.detect(img_path))

        faces = face_detector.detect_faces(img_path)
        all_faces.extend(faces)

        for face in faces:
            emb = face_embedder.get_embedding(img_path, face["bbox"])
            all_embeddings.append(emb)

        all_scenes.extend(scene_classifier.classify(img_path))
        all_text.extend(ocr_reader.read_text(img_path))
        all_landmarks.extend(landmark_sim.compare(img_path))

    # ---------- SIGNAL PACKAGE ----------
    signals = {
        "faces": all_faces,
        "embeddings": all_embeddings,
        "objects": all_objects,
        "scene": all_scenes,
        "ocr_text": all_text,
        "landmarks": all_landmarks,
        "metadata": metadata
    }

    # ---------- INTELLIGENCE PIPELINE ----------
    result = controller.run_pipeline(signals, info["session_id"])

    return result["report"]

@app.get("/graph")
def get_graph():
    # If Neo4j is not configured/available return an empty graph
    if not getattr(graph_client, "_is_available", lambda: False)():
        return {"nodes": [], "links": []}

    with graph_client.driver.session() as session:
        result = session.run("""
            MATCH (a)-[r]->(b)
            RETURN a.id AS source, b.id AS target, type(r) AS relationship
        """)

        nodes = set()
        links = []

        for record in result:
            nodes.add(record["source"])
            nodes.add(record["target"])
            links.append({
                "source": record["source"],
                "target": record["target"],
                "type": record["relationship"]
            })

        node_list = [{"id": n} for n in nodes]

        return {"nodes": node_list, "links": links}