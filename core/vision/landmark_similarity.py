import torch, os, numpy as np, logging
from PIL import Image
logger = logging.getLogger(__name__)
try:
    import clip
except:
    clip = None

class LandmarkSimilarity:
    def __init__(self, landmark_dir="models/landmarks"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.landmark_dir = landmark_dir
        if clip is None:
            self.model = None
            self.preprocess = None
            self.landmark_embeddings = {}
            return
        try:
            self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
            self.landmark_embeddings = self.load_landmarks()
        except:
            self.model = None
            self.preprocess = None
            self.landmark_embeddings = {}

    def load_landmarks(self):
        embeddings = {}
        if not os.path.exists(self.landmark_dir):
            return embeddings
        for file in os.listdir(self.landmark_dir):
            if file.endswith(".npy"):
                try:
                    name = file.replace(".npy", "")
                    embeddings[name] = np.load(os.path.join(self.landmark_dir, file))
                except: pass
        return embeddings

    def encode_image(self, image_path):
        if self.model is None:
            return None
        try:
            image = self.preprocess(Image.open(image_path)).unsqueeze(0).to(self.device)
            with torch.no_grad():
                embedding = self.model.encode_image(image)
            return embedding.cpu().numpy()
        except:
            return None

    def compare(self, image_path, top_k=3):
        if self.model is None or not self.landmark_embeddings:
            return []
        image_embedding = self.encode_image(image_path)
        if image_embedding is None:
            return []
        similarities = []
        for name, landmark_emb in self.landmark_embeddings.items():
            try:
                score = np.dot(image_embedding, landmark_emb.T) / (
                    np.linalg.norm(image_embedding) * np.linalg.norm(landmark_emb))
                similarities.append((name, float(score)))
            except: pass
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [{"landmark": name, "similarity": round(score, 3)} for name, score in similarities[:top_k]]