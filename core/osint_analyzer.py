"""
OSINT Analysis Orchestrator
Main coordinator for comprehensive media analysis with maximum data extraction
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import time
from loguru import logger

from core.metadata.extractor import MetadataExtractor
from core.reasoning.llm_reasoning import LLMReasoning
from core.vision.google_vision import GoogleVisionAnalyzer
from core.audio.audio_analyzer import AudioAnalyzer
from graph.knowledge_graph import KnowledgeGraph


class OSINTAnalyzer:
    """
    Complete OSINT analysis system
    
    Orchestrates:
    1. Metadata extraction (EXIF, FFmpeg)
    2. Google Cloud Vision analysis
    3. LLM intelligence analysis (Gemini 2.5 Flash)
    4. Audio analysis (for videos/audio files)
    5. Knowledge graph updates
    6. Reasoning trace generation
    """
    
    def __init__(self, graph_storage_path: Optional[str] = None):
        logger.info("Initializing OSINT Analyzer...")
        
        # Initialize components
        self.metadata_extractor = MetadataExtractor()
        self.llm = LLMReasoning()
        self.vision = GoogleVisionAnalyzer()
        self.audio = AudioAnalyzer()
        self.graph = KnowledgeGraph(graph_storage_path)
        
        # Log component status
        self._log_component_status()
    
    def _log_component_status(self):
        """Log initialization status of all components"""
        status = {
            "Metadata Extractor": "✓ Ready",
            "LLM (Gemini)": "✓ Ready" if self.llm.model else "✗ Not configured",
            "Google Vision": "✓ Ready" if self.vision.is_enabled() else "✗ Not configured",
            "Audio Analyzer": "✓ Ready",
            "Knowledge Graph": f"✓ Ready ({self.graph.graph.number_of_nodes()} entities)"
        }
        
        logger.info("Component Status:")
        for component, state in status.items():
            logger.info(f"  {component}: {state}")
    
    def analyze_media(
        self,
        file_path: str,
        context: str = "OSINT Investigation",
        update_graph: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive media analysis
        
        Args:
            file_path: Path to media file (image/video/audio)
            context: Investigation context
            update_graph: Whether to update knowledge graph
            
        Returns:
            Complete analysis results with:
            - metadata
            - vision_analysis
            - llm_intelligence
            - audio_analysis (if applicable)
            - exposures
            - entities
            - relationships
            - reasoning_trace
        """
        start_time = time.time()
        file_path = Path(file_path)
        
        logger.info(f"=== Starting OSINT Analysis: {file_path.name} ===")
        
        if not file_path.exists():
            return {"error": "File not found", "path": str(file_path)}
        
        results = {
            "file_info": {
                "name": file_path.name,
                "path": str(file_path.absolute()),
                "analysis_timestamp": datetime.now().isoformat()
            },
            "context": context,
            "analysis_steps": []
        }
        
        try:
            # Step 1: Extract Metadata
            logger.info("Step 1/5: Extracting metadata...")
            results["metadata"] = self._extract_metadata(file_path)
            results["analysis_steps"].append({
                "step": "metadata_extraction",
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            })
            
            # Step 2: Vision Analysis (for images/videos)
            mime_type = results["metadata"].get("mime_type", "")
            
            if mime_type.startswith('image'):
                logger.info("Step 2/5: Running Google Vision analysis...")
                results["vision_analysis"] = self._vision_analysis(file_path)
                results["analysis_steps"].append({
                    "step": "vision_analysis",
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                })
            elif mime_type.startswith('video'):
                logger.info("Step 2/5: Extracting video frames for analysis...")
                results["vision_analysis"] = self._analyze_video_frames(file_path)
                results["analysis_steps"].append({
                    "step": "video_frame_analysis",
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                results["vision_analysis"] = None
            
            # Step 3: Audio Analysis (for videos/audio)
            if mime_type.startswith('audio'):
                logger.info("Step 3/5: Analyzing audio...")
                results["audio_analysis"] = self.audio.analyze_audio(str(file_path))
                results["analysis_steps"].append({
                    "step": "audio_analysis",
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                })
            elif mime_type.startswith('video'):
                logger.info("Step 3/5: Extracting and analyzing audio from video...")
                audio_path = self.audio.extract_audio_from_video(str(file_path))
                if audio_path:
                    results["audio_analysis"] = self.audio.analyze_audio(audio_path)
                    results["analysis_steps"].append({
                        "step": "video_audio_analysis",
                        "status": "completed",
                        "timestamp": datetime.now().isoformat()
                    })
            else:
                results["audio_analysis"] = None
            
            # Step 4: LLM Intelligence Analysis
            logger.info("Step 4/5: Running LLM intelligence analysis...")
            
            # Compile all signals for LLM
            signals = {
                "metadata": results["metadata"],
                "vision": results.get("vision_analysis"),
                "audio": results.get("audio_analysis")
            }
            
            # Run LLM analysis with media file
            media_path = str(file_path) if mime_type.startswith(('image', 'video')) else None
            llm_result = self.llm.analyze_comprehensive(
                signals=signals,
                media_path=media_path,
                context=context
            )
            
            # Extract intelligence and reasoning trace
            results["llm_intelligence"] = llm_result
            
            # Log what we got from LLM
            entities_count = len(llm_result.get('entities', []))
            exposures_count = len(llm_result.get('exposures', []))
            relationships_count = len(llm_result.get('relationships', []))
            logger.info(f"LLM analysis complete: {entities_count} entities, {exposures_count} exposures, {relationships_count} relationships")
            
            # Extract reasoning trace if present
            if llm_result.get('reasoning_trace'):
                results["reasoning_trace"] = llm_result['reasoning_trace']
            
            results["analysis_steps"].append({
                "step": "llm_intelligence",
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            })
            
            # Step 5: Update Knowledge Graph
            if update_graph:
                logger.info("Step 5/5: Updating knowledge graph...")
                self._update_knowledge_graph(results, str(file_path))
                results["analysis_steps"].append({
                    "step": "knowledge_graph_update",
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Add summary
            results["summary"] = self._create_summary(results)
            
            # Processing time
            results["processing_time"] = round(time.time() - start_time, 2)
            
            logger.success(f"✓ Analysis completed in {results['processing_time']}s")
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            results["error"] = str(e)
            results["status"] = "failed"
        
        return results
    
    def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract comprehensive metadata"""
        try:
            return self.metadata_extractor.extract_all(str(file_path))
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {"error": str(e)}
    
    def _vision_analysis(self, file_path: Path) -> Dict[str, Any]:
        """Run Google Vision analysis on image"""
        try:
            if self.vision.is_enabled():
                return self.vision.analyze_image(str(file_path))
            else:
                return {"status": "disabled", "message": "Google Vision API not configured"}
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return {"error": str(e)}
    
    def _analyze_video_frames(self, video_path: Path) -> Dict[str, Any]:
        """Extract and analyze key frames from video"""
        results = {
            "frames_analyzed": 0,
            "objects": [],
            "faces": [],
            "text": [],
            "labels": []  # For Google Vision labels
        }
        
        try:
            import cv2
            import numpy as np
            
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return {"error": "Could not open video file"}
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            results["video_info"] = {
                "fps": fps,
                "total_frames": total_frames,
                "duration": duration,
                "resolution": f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}"
            }
            
            # Analyze 1 frame per second (max 10 frames to avoid rate limits/timeouts)
            sample_rate = int(fps) if fps > 0 else 30
            max_frames = 10
            frames_processed = 0
            
            current_frame = 0
            while cap.isOpened() and frames_processed < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if current_frame % sample_rate == 0:
                    # Save frame temporarily for analysis
                    temp_frame_path = video_path.parent / f"temp_frame_{frames_processed}.jpg"
                    cv2.imwrite(str(temp_frame_path), frame)
                    
                    try:
                        # Analyze frame with available vision models
                        frame_results = self.vision.analyze_image(str(temp_frame_path))
                        
                        # Aggregate results
                        if frame_results.get("google_vision", {}).get("labels"):
                            results["labels"].extend(frame_results["google_vision"]["labels"])
                        
                        # Cleanup
                        if temp_frame_path.exists():
                            temp_frame_path.unlink()
                            
                        frames_processed += 1
                        
                    except Exception as e:
                        logger.warning(f"Frame analysis failed: {e}")
                        if temp_frame_path.exists():
                            temp_frame_path.unlink()
                
                current_frame += 1
            
            cap.release()
            results["frames_analyzed"] = frames_processed
            
            # Uniqueify labels (sort by score)
            seen_labels = set()
            unique_labels = []
            for label in sorted(results["labels"], key=lambda x: x.get('score', 0), reverse=True):
                desc = label.get('description')
                if desc and desc not in seen_labels:
                    seen_labels.add(desc)
                    unique_labels.append(label)
            results["google_vision"] = {"labels": unique_labels[:20]}  # Top 20 unique labels
            
            return results
            
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            return {"error": str(e)}
    
    def _update_knowledge_graph(self, analysis_results: Dict[str, Any], source_file: str):
        """Update knowledge graph with entities and relationships from analysis"""
        try:
            llm_intel = analysis_results.get("llm_intelligence", {})
            
            # Add media file as entity
            media_id = f"media_{Path(source_file).stem}_{int(time.time())}"
            self.graph.add_entity(
                entity_id=media_id,
                entity_type="Media",
                properties={
                    "name": Path(source_file).name,
                    "path": source_file,
                    "type": analysis_results.get("metadata", {}).get("mime_type", "unknown")
                },
                source_file=source_file
            )
            
            # Extract entities from ALL possible locations in LLM response
            entities = []
            
            # 1. Direct 'entities' list
            if isinstance(llm_intel.get("entities"), list):
                entities.extend(llm_intel["entities"])
            
            # 2. 'visual_intelligence' -> 'people', 'objects'
            vis_intel = llm_intel.get("visual_intelligence", {})
            if isinstance(vis_intel, dict):
                for person in vis_intel.get("people", []):
                    entities.append({
                        "id": person.get("id", f"person_{int(time.time())}"),
                        "type": "Person",
                        "name": person.get("description", "Unknown Person"),
                        "confidence": person.get("confidence", 0.0),
                        "attributes": person
                    })
                for obj in vis_intel.get("objects", []):
                    entities.append({
                        "id": obj.get("id", f"obj_{int(time.time())}"),
                        "type": "Object",
                        "name": obj.get("name", "Unknown Object"),
                        "confidence": obj.get("confidence", 0.0),
                        "attributes": obj
                    })
            
            entity_ids = {}
            
            for entity in entities:
                # Generate stable ID if missing
                raw_id = entity.get("id") or entity.get("name", "").replace(" ", "_")
                entity_id = f"{entity.get('type', 'Unknown')}_{raw_id}"
                
                self.graph.add_entity(
                    entity_id=entity_id,
                    entity_type=entity.get("type", "Unknown"),
                    properties={
                        "name": entity.get("name", entity.get("value", "")),
                        "confidence": entity.get("confidence", 0.0),
                        **entity.get("attributes", {})
                    },
                    source_file=source_file
                )
                
                entity_ids[raw_id] = entity_id
                
                # Link entity to media
                self.graph.add_relationship(
                    source_id=entity_id,
                    target_id=media_id,
                    relationship_type="found_in"
                )
            
            # Add relationships involving these entities
            relationships = llm_intel.get("relationships", [])
            
            for rel in relationships:
                source = rel.get("source") or rel.get("source_entity_id")
                target = rel.get("target") or rel.get("target_entity_id")
                
                # Try to resolve IDs
                source_id = entity_ids.get(source, source)
                target_id = entity_ids.get(target, target)
                
                if source_id and target_id:
                    self.graph.add_relationship(
                        source_id=source_id,
                        target_id=target_id,
                        relationship_type=rel.get("relationship_type", rel.get("relation", "related")),
                        properties={
                            "confidence": rel.get("confidence", 0.0),
                            "evidence": rel.get("evidence", "")
                        }
                    )
            
            # Add GPS location if available
            gps = analysis_results.get("metadata", {}).get("gps")
            if gps and gps.get("latitude") and gps.get("longitude"):
                location_id = f"location_{gps['latitude']}_{gps['longitude']}"
                
                self.graph.add_entity(
                    entity_id=location_id,
                    entity_type="Location",
                    properties={
                        "latitude": gps["latitude"],
                        "longitude": gps["longitude"],
                        "source": "GPS_EXIF"
                    },
                    source_file=source_file
                )
                
                # Link media to location
                self.graph.add_relationship(
                    source_id=media_id,
                    target_id=location_id,
                    relationship_type="captured_at"
                )
            
            logger.info(f"Knowledge graph updated: {len(entities)} entities added")
        
        except Exception as e:
            logger.error(f"Knowledge graph update failed: {e}")
    
    def _create_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create analysis summary"""
        llm_intel = results.get("llm_intelligence", {})
        
        return {
            "entities_found": len(llm_intel.get("entities", [])),
            "exposures_identified": len(llm_intel.get("exposures", [])),
            "relationships_found": len(llm_intel.get("relationships", [])),
            "confidence_overall": llm_intel.get("confidence_scores", {}).get("overall", 0.0),
            "has_gps": bool(results.get("metadata", {}).get("gps")),
            "has_text": bool(results.get("vision_analysis", {}).get("text", {}).get("full_text")),
            "has_faces": len(results.get("vision_analysis", {}).get("faces", [])) > 0,
            "has_audio": results.get("audio_analysis") is not None
        }
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        return self.graph.get_statistics()
    
    def export_graph_visualization(self) -> Dict[str, Any]:
        """Export knowledge graph for visualization"""
        return self.graph.export_for_visualization()
    
    def get_entity_network(self, entity_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get network of entities connected to given entity"""
        return self.graph.get_connected_entities(entity_id, max_depth=depth)