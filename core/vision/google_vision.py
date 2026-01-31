"""
Google Cloud Vision API Wrapper
Provides comprehensive vision analysis using Google's Cloud Vision API
"""

import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger

try:
    from google.cloud import vision
    from google.oauth2 import service_account
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    vision = None
    GOOGLE_VISION_AVAILABLE = False
    logger.warning("google-cloud-vision not installed. Run: pip install google-cloud-vision")


class GoogleVisionAnalyzer:
    """
    Google Cloud Vision API client for comprehensive image analysis
    
    Features:
    - Label detection
    - Face detection  
    - Landmark detection
    - Logo detection
    - Text detection (OCR)
    - Safe search detection
    - Image properties
    - Web detection
    """
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Vision client with proper credential handling"""
        if not GOOGLE_VISION_AVAILABLE:
            logger.warning("Google Cloud Vision library not available. Install: pip install google-cloud-vision")
            return
        
        try:
            # Check for credentials in environment
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            
            if not credentials_path:
                logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set in environment")
                return
            
            credentials_file = Path(credentials_path)
            if not credentials_file.exists():
                logger.error(f"Google Cloud credentials file not found: {credentials_path}")
                return
            
            # Initialize client with credentials
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    str(credentials_file)
                )
                self.client = vision.ImageAnnotatorClient(credentials=credentials)
                logger.success(f"✓ Google Cloud Vision initialized with credentials from {credentials_file.name}")
            except Exception as e:
                logger.error(f"Failed to load credentials from {credentials_path}: {e}")
                return
        
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Vision: {e}")
    
    def is_enabled(self) -> bool:
        """Check if Google Vision is enabled"""
        return self.client is not None
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Comprehensive image analysis using Google Cloud Vision
        
        Returns all available detections:
        - labels
        - faces
        - landmarks
        - logos
        - text
        - safe_search
        - properties
        - web_detection
        """
        if not self.is_enabled():
            return {
                "status": "disabled",
                "message": "Google Cloud Vision API not configured"
            }
        
        try:
            # Load image
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Run all detections
            results = {}
            
            # Label Detection
            try:
                response = self.client.label_detection(image=image)
                results["labels"] = [
                    {
                        "description": label.description,
                        "score": float(label.score),
                        "topicality": float(label.topicality) if hasattr(label, 'topicality') else 0.0
                    }
                    for label in response.label_annotations
                ]
                logger.debug(f"Labels: {len(results['labels'])}")
            except Exception as e:
                logger.warning(f"Label detection failed: {e}")
                results["labels"] = []
            
            # Face Detection
            try:
                response = self.client.face_detection(image=image)
                results["faces"] = []
                for face in response.face_annotations:
                    results["faces"].append({
                        "confidence": float(face.detection_confidence),
                        "joy": self._likelihood_to_score(face.joy_likelihood),
                        "sorrow": self._likelihood_to_score(face.sorrow_likelihood),
                        "anger": self._likelihood_to_score(face.anger_likelihood),
                        "surprise": self._likelihood_to_score(face.surprise_likelihood),
                        "headwear": self._likelihood_to_score(face.headwear_likelihood),
                        "bounds": {
                            "vertices": [
                                {"x": vertex.x, "y": vertex.y} 
                                for vertex in face.bounding_poly.vertices
                            ]
                        }
                    })
                logger.debug(f"Faces: {len(results['faces'])}")
            except Exception as e:
                logger.warning(f"Face detection failed: {e}")
                results["faces"] = []
            
            # Landmark Detection
            try:
                response = self.client.landmark_detection(image=image)
                results["landmarks"] = [
                    {
                        "description": landmark.description,
                        "score": float(landmark.score),
                        "locations": [
                            {
                                "latitude": loc.lat_lng.latitude,
                                "longitude": loc.lat_lng.longitude
                            }
                            for loc in landmark.locations
                        ] if landmark.locations else []
                    }
                    for landmark in response.landmark_annotations
                ]
                logger.debug(f"Landmarks: {len(results['landmarks'])}")
            except Exception as e:
                logger.warning(f"Landmark detection failed: {e}")
                results["landmarks"] = []
            
            # Logo Detection
            try:
                response = self.client.logo_detection(image=image)
                results["logos"] = [
                    {
                        "description": logo.description,
                        "score": float(logo.score)
                    }
                    for logo in response.logo_annotations
                ]
                logger.debug(f"Logos: {len(results['logos'])}")
            except Exception as e:
                logger.warning(f"Logo detection failed: {e}")
                results["logos"] = []
            
            # Text Detection
            try:
                response = self.client.text_detection(image=image)
                if response.text_annotations:
                    # First annotation is full text
                    results["text"] = {
                        "full_text": response.text_annotations[0].description if response.text_annotations else "",
                        "blocks": [
                            {
                                "description": text.description,
                                "bounds": {
                                    "vertices": [
                                        {"x": vertex.x, "y": vertex.y} 
                                        for vertex in text.bounding_poly.vertices
                                    ]
                                }
                            }
                            for text in response.text_annotations[1:]  # Skip first (full text)
                        ]
                    }
                else:
                    results["text"] = {"full_text": "", "blocks": []}
                logger.debug(f"Text blocks: {len(results['text']['blocks'])}")
            except Exception as e:
                logger.warning(f"Text detection failed: {e}")
                results["text"] = {"full_text": "", "blocks": []}
            
            # Safe Search Detection
            try:
                response = self.client.safe_search_detection(image=image)
                safe = response.safe_search_annotation
                results["safe_search"] = {
                    "adult": self._likelihood_to_score(safe.adult),
                    "violence": self._likelihood_to_score(safe.violence),
                    "racy": self._likelihood_to_score(safe.racy),
                    "medical": self._likelihood_to_score(safe.medical),
                    "spoof": self._likelihood_to_score(safe.spoof)
                }
            except Exception as e:
                logger.warning(f"Safe search detection failed: {e}")
                results["safe_search"] = {}
            
            # Image Properties
            try:
                response = self.client.image_properties(image=image)
                props = response.image_properties_annotation
                results["properties"] = {
                    "dominant_colors": [
                        {
                            "color": {
                                "red": color.color.red,
                                "green": color.color.green,
                                "blue": color.color.blue
                            },
                            "score": float(color.score),
                            "pixel_fraction": float(color.pixel_fraction)
                        }
                        for color in props.dominant_colors.colors[:5]  # Top 5 colors
                    ] if props.dominant_colors else []
                }
            except Exception as e:
                logger.warning(f"Image properties failed: {e}")
                results["properties"] = {}
            
            # Web Detection
            try:
                response = self.client.web_detection(image=image)
                web = response.web_detection
                results["web_detection"] = {
                    "web_entities": [
                        {
                            "description": entity.description,
                            "score": float(entity.score)
                        }
                        for entity in web.web_entities[:10]  # Top 10
                    ] if web.web_entities else [],
                    "best_guess_labels": [
                        label.label for label in web.best_guess_labels
                    ] if web.best_guess_labels else []
                }
            except Exception as e:
                logger.warning(f"Web detection failed: {e}")
                results["web_detection"] = {}
            
            results["status"] = "success"
            return results
        
        except Exception as e:
            logger.error(f"Google Vision analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _likelihood_to_score(self, likelihood) -> float:
        """Convert likelihood enum to numeric score"""
        likelihood_map = {
            0: 0.0,    # UNKNOWN
            1: 0.1,    # VERY_UNLIKELY
            2: 0.3,    # UNLIKELY
            3: 0.5,    # POSSIBLE
            4: 0.7,    # LIKELY
            5: 0.9     # VERY_LIKELY
        }
        return likelihood_map.get(likelihood, 0.0)