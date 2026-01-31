import logging
from typing import Dict, List, Any, Optional
import os
import numpy as np

logger = logging.getLogger(__name__)


class EnhancedVisionProcessor:
    """
    Multi-model vision processing system combining:
    - YOLO for object detection
    - DeepFace for face analysis
    - EasyOCR for text
    - CLIP for semantic understanding
    - Google Vision API
    - Custom ensemble methods
    
    Goal: Maximum accuracy and data extraction
    """
    
    def __init__(self):
        self.models = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all available models"""
        
        # YOLO for object detection
        try:
            from ultralytics import YOLO
            self.models['yolo'] = YOLO('yolov8x.pt')  # Use largest model for accuracy
            logger.info("✓ YOLO initialized (YOLOv8x - highest accuracy)")
        except Exception as e:
            logger.warning(f"YOLO init failed: {e}")
        
        # DeepFace for facial analysis
        try:
            from deepface import DeepFace
            self.models['deepface'] = DeepFace
            logger.info("✓ DeepFace initialized")
        except Exception as e:
            logger.warning(f"DeepFace init failed: {e}")
        
        # EasyOCR for text detection
        try:
            import easyocr
            # Support multiple languages for better coverage
            self.models['easyocr'] = easyocr.Reader(
                ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ar', 'hi', 'zh_sim', 'ja', 'ko'],
                gpu=True
            )
            logger.info("✓ EasyOCR initialized (12 languages)")
        except Exception as e:
            logger.warning(f"EasyOCR init failed: {e}")
        
        # CLIP for semantic understanding
        try:
            import clip
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model, preprocess = clip.load("ViT-L/14", device=device)  # Largest CLIP model
            self.models['clip'] = {
                'model': model,
                'preprocess': preprocess,
                'device': device
            }
            logger.info("✓ CLIP initialized (ViT-L/14)")
        except Exception as e:
            logger.warning(f"CLIP init failed: {e}")
        
        # Google Cloud Vision
        try:
            from core.vision.google_vision import GoogleVisionAnalyzer
            vision_analyzer = GoogleVisionAnalyzer()
            if vision_analyzer.is_enabled():
                self.models['google_vision'] = vision_analyzer
                logger.info("✓ Google Cloud Vision initialized")
            else:
                logger.warning("Google Cloud Vision not enabled - check credentials")
        except Exception as e:
            logger.warning(f"Google Vision init failed: {e}")
        
        # PaddleOCR as OCR backup (often more accurate than EasyOCR)
        try:
            from paddleocr import PaddleOCR
            self.models['paddleocr'] = PaddleOCR(use_angle_cls=True, lang='en')
            logger.info("✓ PaddleOCR initialized")
        except Exception as e:
            logger.warning(f"PaddleOCR init failed: {e}")
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Comprehensive multi-model image analysis
        
        Returns maximum possible extracted data
        """
        results = {
            "objects": [],
            "faces": [],
            "text": [],
            "scene": {},
            "semantic": {},
            "google_vision": {},
            "confidence_ensemble": {}
        }
        
        # Run all models in parallel conceptually (sequentially for now)
        
        # 1. Object Detection (YOLO)
        if 'yolo' in self.models:
            results['objects'] = self._detect_objects_yolo(image_path)
        
        # 2. Face Analysis (DeepFace)
        if 'deepface' in self.models:
            results['faces'] = self._analyze_faces_deepface(image_path)
        
        # 3. Text Detection (Multi-OCR ensemble)
        results['text'] = self._detect_text_ensemble(image_path)
        
        # 4. Scene Understanding (CLIP)
        if 'clip' in self.models:
            results['scene'] = self._analyze_scene_clip(image_path)
            results['semantic'] = self._semantic_search_clip(image_path)
        
        # 5. Google Vision API (comprehensive)
        if 'google_vision' in self.models:
            results['google_vision'] = self.models['google_vision'].analyze_image(image_path)
        
        # 6. Create ensemble confidence scores
        results['confidence_ensemble'] = self._create_ensemble_confidence(results)
        
        # 7. Deduplicate and merge results
        results = self._merge_and_deduplicate(results)
        
        return results
    
    def _detect_objects_yolo(self, image_path: str) -> List[Dict[str, Any]]:
        """Enhanced YOLO detection with confidence filtering"""
        try:
            model = self.models['yolo']
            
            # Run detection with lower confidence threshold to catch more
            detections = model(image_path, conf=0.25, verbose=False)
            
            objects = []
            for result in detections:
                for box in result.boxes:
                    objects.append({
                        "label": model.names[int(box.cls[0])],
                        "confidence": float(box.conf[0]),
                        "bbox": box.xyxy[0].tolist(),
                        "source": "yolo"
                    })
            
            logger.info(f"YOLO detected {len(objects)} objects")
            return objects
            
        except Exception as e:
            logger.error(f"YOLO detection failed: {e}")
            return []
    
    def _analyze_faces_deepface(self, image_path: str) -> List[Dict[str, Any]]:
        """Comprehensive face analysis with DeepFace"""
        try:
            DeepFace = self.models['deepface']
            
            faces = []
            
            # 1. Face Detection
            try:
                detected_faces = DeepFace.extract_faces(
                    img_path=image_path,
                    detector_backend='retinaface',  # Most accurate
                    enforce_detection=False
                )
            except:
                # Fallback to faster detector
                detected_faces = DeepFace.extract_faces(
                    img_path=image_path,
                    detector_backend='opencv',
                    enforce_detection=False
                )
            
            for idx, face_obj in enumerate(detected_faces):
                face_data = {
                    "face_id": idx,
                    "confidence": float(face_obj.get('confidence', 0)),
                    "bbox": self._format_bbox(face_obj.get('facial_area', {})),
                    "source": "deepface"
                }
                
                # 2. Facial Attributes Analysis
                try:
                    analysis = DeepFace.analyze(
                        img_path=image_path,
                        actions=['age', 'gender', 'race', 'emotion'],
                        enforce_detection=False,
                        detector_backend='skip'  # We already have faces
                    )
                    
                    if isinstance(analysis, list):
                        analysis = analysis[idx] if idx < len(analysis) else analysis[0]
                    
                    face_data.update({
                        "age": analysis.get('age'),
                        "gender": analysis.get('dominant_gender'),
                        "gender_confidence": analysis.get('gender', {}),
                        "race": analysis.get('dominant_race'),
                        "race_confidence": analysis.get('race', {}),
                        "emotion": analysis.get('dominant_emotion'),
                        "emotion_confidence": analysis.get('emotion', {})
                    })
                except Exception as e:
                    logger.warning(f"Face analysis failed for face {idx}: {e}")
                
                # 3. Face Embedding
                try:
                    embedding = DeepFace.represent(
                        img_path=image_path,
                        model_name='Facenet512',  # Most accurate
                        enforce_detection=False
                    )
                    if embedding:
                        face_data['embedding'] = embedding[idx]['embedding'] if isinstance(embedding, list) else embedding['embedding']
                except Exception as e:
                    logger.warning(f"Face embedding failed: {e}")
                
                faces.append(face_data)
            
            logger.info(f"DeepFace analyzed {len(faces)} faces")
            return faces
            
        except Exception as e:
            logger.error(f"DeepFace analysis failed: {e}")
            return []
    
    def _detect_text_ensemble(self, image_path: str) -> List[Dict[str, Any]]:
        """Multi-OCR ensemble for maximum text extraction accuracy"""
        all_text = []
        
        # EasyOCR
        if 'easyocr' in self.models:
            try:
                reader = self.models['easyocr']
                results = reader.readtext(image_path)
                
                for bbox, text, conf in results:
                    all_text.append({
                        "text": text,
                        "confidence": float(conf),
                        "bbox": bbox,
                        "source": "easyocr"
                    })
                
                logger.info(f"EasyOCR found {len(results)} text regions")
            except Exception as e:
                logger.error(f"EasyOCR failed: {e}")
        
        # PaddleOCR
        if 'paddleocr' in self.models:
            try:
                ocr = self.models['paddleocr']
                results = ocr.ocr(image_path, cls=True)
                
                if results and results[0]:
                    for line in results[0]:
                        bbox, (text, conf) = line
                        all_text.append({
                            "text": text,
                            "confidence": float(conf),
                            "bbox": bbox,
                            "source": "paddleocr"
                        })
                    
                    logger.info(f"PaddleOCR found {len(results[0])} text regions")
            except Exception as e:
                logger.error(f"PaddleOCR failed: {e}")
        
        # Tesseract as additional backup
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(image_path)
            
            # Get text with confidence
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            for i in range(len(data['text'])):
                if data['text'][i].strip():
                    all_text.append({
                        "text": data['text'][i],
                        "confidence": float(data['conf'][i]) / 100.0,
                        "bbox": [
                            data['left'][i],
                            data['top'][i],
                            data['left'][i] + data['width'][i],
                            data['top'][i] + data['height'][i]
                        ],
                        "source": "tesseract"
                    })
            
            logger.info(f"Tesseract found {len([t for t in data['text'] if t.strip()])} text regions")
        except Exception as e:
            logger.warning(f"Tesseract failed: {e}")
        
        # Deduplicate and merge similar text detections
        merged_text = self._merge_text_detections(all_text)
        
        logger.info(f"Total text detections (merged): {len(merged_text)}")
        return merged_text
    
    def _analyze_scene_clip(self, image_path: str) -> Dict[str, Any]:
        """Scene classification using CLIP"""
        try:
            import torch
            from PIL import Image
            
            clip_data = self.models['clip']
            model = clip_data['model']
            preprocess = clip_data['preprocess']
            device = clip_data['device']
            
            image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
            
            # Scene categories
            scene_categories = [
                "indoor scene", "outdoor scene", "urban environment", "natural environment",
                "office setting", "home interior", "street scene", "park or garden",
                "restaurant or cafe", "shopping area", "transportation hub",
                "industrial area", "residential area", "commercial building",
                "daytime scene", "nighttime scene", "sunrise or sunset",
                "crowded place", "empty or sparse area"
            ]
            
            text_tokens = torch.cat([torch.clip.tokenize(f"a photo of {c}") for c in scene_categories]).to(device)
            
            with torch.no_grad():
                image_features = model.encode_image(image)
                text_features = model.encode_text(text_tokens)
                
                # Calculate similarity
                similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
                values, indices = similarity[0].topk(5)
            
            results = [
                {
                    "category": scene_categories[idx],
                    "confidence": float(val)
                }
                for val, idx in zip(values, indices)
            ]
            
            return {
                "categories": results,
                "primary_scene": results[0]['category'] if results else "unknown"
            }
            
        except Exception as e:
            logger.error(f"CLIP scene analysis failed: {e}")
            return {}
    
    def _semantic_search_clip(self, image_path: str) -> Dict[str, Any]:
        """Semantic understanding using CLIP with detailed queries"""
        try:
            import torch
            from PIL import Image
            
            clip_data = self.models['clip']
            model = clip_data['model']
            preprocess = clip_data['preprocess']
            device = clip_data['device']
            
            image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
            
            # Comprehensive semantic queries
            queries = {
                "people": ["no people", "one person", "small group (2-5 people)", "large group (6+ people)"],
                "activity": ["people working", "people socializing", "people exercising", "people traveling", "people eating"],
                "setting": ["professional setting", "casual setting", "formal event", "recreational activity"],
                "time": ["morning", "afternoon", "evening", "night"],
                "weather": ["sunny", "cloudy", "rainy", "snowy"],
                "formality": ["very formal", "business casual", "casual", "very casual"],
                "objects": ["vehicles present", "technology visible", "furniture present", "nature elements"]
            }
            
            semantic_results = {}
            
            for category, options in queries.items():
                text_tokens = torch.cat([torch.clip.tokenize(f"a photo showing {opt}") for opt in options]).to(device)
                
                with torch.no_grad():
                    image_features = model.encode_image(image)
                    text_features = model.encode_text(text_tokens)
                    similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
                    values, indices = similarity[0].topk(len(options))
                
                semantic_results[category] = [
                    {
                        "option": options[idx],
                        "confidence": float(val)
                    }
                    for val, idx in zip(values, indices)
                ]
            
            return semantic_results
            
        except Exception as e:
            logger.error(f"CLIP semantic search failed: {e}")
            return {}
    
    def _merge_text_detections(self, text_list: List[Dict]) -> List[Dict]:
        """Merge similar text detections from multiple OCR engines"""
        if not text_list:
            return []
        
        # Simple merge: group by similar text
        merged = {}
        
        for item in text_list:
            text = item['text'].strip().lower()
            
            if not text:
                continue
            
            # Find similar existing text
            found = False
            for key in list(merged.keys()):
                if self._text_similarity(text, key) > 0.8:
                    # Merge: keep higher confidence
                    if item['confidence'] > merged[key]['confidence']:
                        merged[key] = item
                    found = True
                    break
            
            if not found:
                merged[text] = item
        
        return list(merged.values())
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity (Levenshtein ratio)"""
        try:
            from difflib import SequenceMatcher
            return SequenceMatcher(None, text1, text2).ratio()
        except:
            return 1.0 if text1 == text2 else 0.0
    
    def _create_ensemble_confidence(self, results: Dict) -> Dict[str, float]:
        """Create confidence scores based on model agreement"""
        confidence = {
            "overall": 0.0,
            "objects": 0.0,
            "faces": 0.0,
            "text": 0.0,
            "scene": 0.0
        }
        
        # Calculate based on number of models that found data
        models_used = len([k for k in self.models.keys()])
        
        if results.get('objects'):
            confidence['objects'] = min(1.0, len(results['objects']) / 10)
        
        if results.get('faces'):
            confidence['faces'] = 0.9 if len(results['faces']) > 0 else 0.0
        
        if results.get('text'):
            confidence['text'] = min(1.0, len(results['text']) / 5)
        
        if results.get('scene'):
            confidence['scene'] = 0.8
        
        confidence['overall'] = sum(confidence.values()) / len(confidence)
        
        return confidence
    
    def _merge_and_deduplicate(self, results: Dict) -> Dict:
        """Merge results from different models and remove duplicates"""
        # This is a placeholder - implement sophisticated merging logic
        return results
    
    def _format_bbox(self, area: Dict) -> List[float]:
        """Format bounding box consistently"""
        return [
            area.get('x', 0),
            area.get('y', 0),
            area.get('w', 0),
            area.get('h', 0)
        ]