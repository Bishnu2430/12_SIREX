import torch
from torchvision import models, transforms
from PIL import Image
import json
import os

class SceneClassifier:
    def __init__(self, label_path="models/categories_places365.txt"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load pretrained model
        self.model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        self.model.eval()
        self.model.to(self.device)

        # Image transform
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

        # Load scene labels
        if os.path.exists(label_path):
            with open(label_path) as f:
                self.labels = [line.strip() for line in f.readlines()]
        else:
            self.labels = []

    def classify(self, image_path: str):
        img = Image.open(image_path).convert("RGB")
        img_tensor = self.transform(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(img_tensor)
            probs = torch.nn.functional.softmax(outputs[0], dim=0)

        top_prob, top_idx = torch.topk(probs, 3)

        scenes = []
        for prob, idx in zip(top_prob, top_idx):
            label = self.labels[idx] if idx < len(self.labels) else f"class_{idx}"
            scenes.append({
                "scene": label,
                "confidence": round(float(prob), 3)
            })

        return scenes
