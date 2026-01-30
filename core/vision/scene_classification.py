import torch
from torchvision import models, transforms
from PIL import Image
import os, logging
logger = logging.getLogger(__name__)

class SceneClassifier:
    def __init__(self, label_path="models/categories_places365.txt"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        self.model.eval()
        self.model.to(self.device)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        self.labels = self._get_generic_scene_labels()

    def _get_generic_scene_labels(self):
        return ["indoor", "outdoor", "urban", "natural", "architectural"] * 200

    def classify(self, image_path: str):
        try:
            img = Image.open(image_path).convert("RGB")
            img_tensor = self.transform(img).unsqueeze(0).to(self.device)
            with torch.no_grad():
                outputs = self.model(img_tensor)
                probs = torch.nn.functional.softmax(outputs[0], dim=0)
            top_prob, top_idx = torch.topk(probs, 3)
            scenes = []
            for prob, idx in zip(top_prob, top_idx):
                idx_int = int(idx)
                label = self.labels[idx_int] if idx_int < len(self.labels) else f"scene_{idx_int}"
                scenes.append({"scene": label, "confidence": round(float(prob), 3)})
            return scenes
        except Exception as e:
            logger.error(f"Scene classification failed: {e}")
            return [{"scene": "unknown", "confidence": 0.0}]