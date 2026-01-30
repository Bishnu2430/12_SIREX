import torch
import clip
from PIL import Image
import os
import numpy as np

class LandmarkSimilarity:
    def __init__(self, landmark_dir="models/landmarks"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
        self.landmark_dir = landmark_dir
        self.landmark_embeddings = self.load_landmarks()

    def load_landmarks(self):
        embeddings = {}
        for file in os.listdir(self.landmark_dir):
            if file.endswith(".npy"):
                name = file.replace(".npy", "")
                embeddings[name] = np.load(os.path.join(self.landmark_dir, file))
        return embeddings

    def encode_image(self, image_path):
        image = self.preprocess(Image.open(image_path)).unsqueeze(0).to(self.device)
        with torch.no_grad():
            embedding = self.model.encode_image(image)
        return embedding.cpu().numpy()

    def compare(self, image_path, top_k=3):
        image_embedding = self.encode_image(image_path)

        similarities = []

        for name, landmark_emb in self.landmark_embeddings.items():
            score = np.dot(image_embedding, landmark_emb.T) / (
                np.linalg.norm(image_embedding) * np.linalg.norm(landmark_emb)
            )
            similarities.append((name, float(score)))

        similarities.sort(key=lambda x: x[1], reverse=True)

        return [
            {"landmark": name, "similarity": round(score, 3)}
            for name, score in similarities[:top_k]
        ]
