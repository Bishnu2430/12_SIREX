import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class FaceMatcher:

    def __init__(self, threshold=0.6):
        self.known_faces = {}  # node_id -> embedding
        self.threshold = threshold

    def register_face(self, node_id, embedding):
        self.known_faces[node_id] = np.array(embedding)

    def find_match(self, embedding):
        if not self.known_faces:
            return None, 0

        embedding = np.array(embedding).reshape(1, -1)
        best_match = None
        best_score = 0

        for node_id, known_emb in self.known_faces.items():
            score = cosine_similarity(embedding, known_emb.reshape(1, -1))[0][0]
            if score > best_score:
                best_score = score
                best_match = node_id

        return best_match, best_score
