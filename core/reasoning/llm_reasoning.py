"""
Enhanced LLM Client with Gemini 2.5 Flash
Provides intelligent analysis with comprehensive reasoning traces
"""

import os
import time
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from PIL import Image
import google.generativeai as genai
from loguru import logger


class LLMReasoning:
    """
    Advanced LLM client with:
    - Gemini 2.5 Flash (primary)
    - Automatic fallback chain
    - Comprehensive reasoning traces
    - Vision + multimodal support
    """
    
    GEMINI_MODELS = [
        "gemini-1.5-flash",              # Fast, efficient
        "gemini-1.5-flash-latest",       # Latest version
        "gemini-1.5-pro",                # More capable
    ]
    
    def __init__(self):
        # Check multiple environment variables for flexibility
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model = None
        self.model_name = None
        self.reasoning_traces = []
        
        # Diagnostic logging
        logger.info(f"LLM Initialization - API Key found: {bool(self.api_key)}")
        if self.api_key:
            logger.info(f"API Key source: {'GOOGLE_API_KEY' if os.getenv('GOOGLE_API_KEY') else 'GEMINI_API_KEY'}")
            logger.info(f"API Key prefix: {self.api_key[:20]}...")
        
        if not self.api_key:
            logger.warning("No API key found (sought GOOGLE_API_KEY or GEMINI_API_KEY). LLM analysis disabled.")
            return
        
        try:
            genai.configure(api_key=self.api_key)
            self._initialize_model()
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")
    
    def _initialize_model(self):
        """Initialize with best available model"""
        available_models = self._get_available_models()
        logger.info(f"Available Gemini models: {available_models}")
        
        for model_name in self.GEMINI_MODELS:
            # Check if model exists in available models
            if any(model_name in avail for avail in available_models):
                try:
                    self.model = genai.GenerativeModel(model_name)
                    self.model_name = model_name
                    logger.success(f"✓ LLM initialized with {model_name}")
                    self._log_reasoning("initialization", f"Successfully initialized {model_name}")
                    return
                except Exception as e:
                    logger.warning(f"Failed to initialize {model_name}: {e}")
                    self._log_reasoning("initialization_failed", f"{model_name}: {e}")
                    continue
        
        logger.error("❌ No working Gemini models found")
        self._log_reasoning("initialization_failed", "All models failed")
    
    def _get_available_models(self) -> List[str]:
        """Get list of available models with proper error handling"""
        try:
            models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    # Store both full name and short name
                    models.append(m.name)
                    models.append(m.name.replace('models/', ''))
            
            return models
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def analyze_comprehensive(
        self,
        signals: Dict[str, Any],
        media_path: Optional[str] = None,
        context: str = "OSINT Investigation"
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis with full reasoning traces
        
        Args:
            signals: All extracted signals (metadata, vision, audio, etc.)
            media_path: Path to media file for visual analysis
            context: Investigation context
            
        Returns:
            {
                "analysis": {...},
                "reasoning": [...],
                "confidence": 0.0-1.0,
                "model_used": "gemini-x"
            }
        """
        if not self.model:
            return self._empty_response("LLM not initialized")
        
        start_time = time.time()
        self._log_reasoning("analysis_start", f"Starting analysis with {self.model_name}")
        
        try:
            # Build comprehensive prompt
            prompt = self._build_osint_prompt(signals, context)
            self._log_reasoning("prompt_built", f"Prompt length: {len(prompt)} chars")
            
            # Prepare content
            content = [prompt]
            
            # Add media if provided
            if media_path and Path(media_path).exists():
                content = self._add_media_to_content(content, media_path)
                self._log_reasoning("media_added", f"Added media: {Path(media_path).name}")
            
            # Generate with retry
            response = self._generate_with_retry(content)
            
            if not response:
                return self._empty_response("Generation failed")
            
            # Parse response
            result = self._parse_response(response)
            
            # Add metadata
            result["model_used"] = self.model_name
            result["processing_time"] = round(time.time() - start_time, 2)
            result["reasoning_trace"] = self.reasoning_traces.copy()
            
            self._log_reasoning("analysis_complete", 
                              f"Completed in {result['processing_time']}s")
            
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            self._log_reasoning("analysis_error", str(e))
            return self._empty_response(f"Error: {e}")
    
    def _build_osint_prompt(self, signals: Dict, context: str) -> str:
        """Build comprehensive OSINT analysis prompt"""
        
        return f"""You are an elite OSINT analyst with expertise in digital forensics, geolocation, facial analysis, and threat assessment.

**MISSION**: Extract MAXIMUM intelligence from all available signals and provide actionable OSINT insights.

**CONTEXT**: {context}

**YOUR TASK**:
1. Analyze ALL provided signals comprehensively
2. Extract entities (people, places, organizations, events)
3. Identify exposures and security risks
4. Provide geolocation estimates
5. Suggest OSINT techniques for further investigation
6. Generate a knowledge graph structure

**ANALYSIS FRAMEWORK**:

### Visual Intelligence (if image/video present):
- **People**: Age, gender, ethnicity, clothing, body language, emotions, distinctive features
- **Objects**: Items, brands, serial numbers, condition
- **Environment**: Indoor/outdoor, lighting, weather, architecture, vegetation
- **Text**: ALL visible text (signs, documents, screens, labels)
- **Location Clues**: Architectural style, language, infrastructure, landmarks
- **Technology**: Devices, software, equipment
- **Activities**: What's happening, interactions, behaviors

### Metadata Intelligence:
- GPS coordinates analysis
- Timestamps and patterns
- Device fingerprints
- Software signatures
- File properties

### Audio Intelligence (if applicable):
- Speech content and language
- Accents and dialects
- Background sounds
- Voice characteristics
- Environmental acoustics

### Geolocation:
- Estimate location from visual/metadata clues
- Cross-reference multiple indicators
- Provide confidence levels

### Threat Assessment:
- Identify ALL exposures (biometric, location, organizational, behavioral, digital)
- Rate risk levels (CRITICAL/HIGH/MEDIUM/LOW)
- Provide attack scenarios
- Suggest mitigations

### Knowledge Graph:
- Extract entities with relationships
- Identify connections and patterns
- Build network structure

**INPUT SIGNALS**:
```json
{json.dumps(signals, indent=2, default=str)}
```

**OUTPUT FORMAT** (STRICT JSON - no markdown fences):
{{
  "executive_summary": "2-3 sentence high-level summary of key findings",
  
  "narrative_report": "Comprehensive analysis narrative with all findings in detail...",
  
  "visual_intelligence": {{
    "people": [
      {{
        "id": "person_1",
        "description": "Detailed physical description",
        "estimated_age_range": "25-35",
        "gender": "male/female/unknown",
        "ethnicity_estimate": "description",
        "emotion": "happy/neutral/concerned/etc",
        "clothing": "Detailed clothing description with brands",
        "distinctive_features": ["feature1", "feature2"],
        "confidence": 0.85
      }}
    ],
    "objects": [
      {{
        "id": "obj_1",
        "name": "object name",
        "description": "detailed description",
        "brand": "if visible",
        "significance": "why it matters",
        "confidence": 0.90
      }}
    ],
    "environment": {{
      "setting": "office/home/street/vehicle/etc",
      "indoor_outdoor": "indoor/outdoor/mixed",
      "lighting": "natural/artificial/time_of_day",
      "weather": "if visible",
      "architecture_style": "modern/traditional/etc",
      "infrastructure_level": "developed/developing",
      "confidence": 0.80
    }},
    "text_extracted": [
      {{
        "text": "exact visible text",
        "location": "where found in image",
        "language": "detected language",
        "significance": "what it reveals",
        "confidence": 0.95
      }}
    ],
    "location_clues": [
      {{
        "clue_type": "architecture/vegetation/text/infrastructure",
        "observation": "specific observation",
        "suggests": "geographic region/country",
        "confidence": 0.75
      }}
    ]
  }},
  
  "entities": [
    {{
      "id": "unique_id",
      "type": "Person/Location/Organization/Event/Device",
      "name": "entity name or identifier",
      "aliases": ["alternative names"],
      "confidence": 0.85,
      "attributes": {{
        "key": "value"
      }},
      "sources": ["visual", "metadata", "audio"],
      "first_seen": "timestamp or context"
    }}
  ],
  
  "relationships": [
    {{
      "source_entity_id": "entity_id_1",
      "target_entity_id": "entity_id_2",
      "relationship_type": "located_at/associated_with/owns/etc",
      "confidence": 0.80,
      "evidence": "description of evidence"
    }}
  ],
  
  "geolocation": {{
    "estimated_location": "City, Region, Country",
    "latitude": null,
    "longitude": null,
    "confidence": 0.70,
    "reasoning": [
      "specific clue and what it suggests"
    ],
    "evidence": {{
      "architectural": ["observation1", "observation2"],
      "linguistic": ["observation1"],
      "environmental": ["observation1"],
      "cultural": ["observation1"],
      "technological": ["observation1"]
    }},
    "alternative_locations": [
      {{
        "location": "Alternative location",
        "confidence": 0.40,
        "reasoning": "why this is possible"
      }}
    ]
  }},
  
  "temporal_analysis": {{
    "estimated_time_of_day": "morning/afternoon/evening/night",
    "estimated_season": "spring/summer/fall/winter",
    "estimated_era": "2020s/2010s/etc",
    "confidence": 0.75,
    "indicators": ["shadow angle", "vegetation", "clothing", "technology"]
  }},
  
  "exposures": [
    {{
      "id": "exp_1",
      "type": "Specific exposure type",
      "category": "biometric/location/organizational/behavioral/digital/device",
      "severity": "CRITICAL/HIGH/MEDIUM/LOW",
      "description": "What exactly is exposed",
      "exposed_data": ["specific", "data", "points"],
      "attack_scenarios": [
        "Specific realistic attack vector"
      ],
      "likelihood": "HIGH/MEDIUM/LOW",
      "impact": "Potential consequences",
      "recommendations": [
        "Concrete mitigation step"
      ],
      "confidence": 0.85
    }}
  ],
  
  "extracted_data": {{
    "names": ["any names found"],
    "organizations": ["companies, groups"],
    "locations": ["specific places mentioned"],
    "phone_numbers": ["any visible"],
    "emails": ["any visible"],
    "urls": ["any visible"],
    "social_media": ["handles, usernames"],
    "credentials": ["badges, IDs"],
    "license_plates": ["plates visible"],
    "serial_numbers": ["device serials"],
    "ip_addresses": ["if visible"],
    "mac_addresses": ["if visible"],
    "wifi_networks": ["if visible"]
  }},
  
  "osint_techniques": [
    {{
      "technique": "Technique name",
      "description": "What it involves",
      "tools": ["tool1", "tool2"],
      "expected_outcome": "What you might find",
      "priority": "HIGH/MEDIUM/LOW"
    }}
  ],
  
  "next_steps": [
    {{
      "action": "Specific investigative action",
      "rationale": "Why this should be done",
      "tools_needed": ["tool1", "tool2"],
      "estimated_effort": "time estimate",
      "priority": "HIGH/MEDIUM/LOW"
    }}
  ],
  
  "confidence_scores": {{
    "overall": 0.80,
    "visual_analysis": 0.85,
    "entity_extraction": 0.75,
    "geolocation": 0.70,
    "threat_assessment": 0.90,
    "data_extraction": 0.95
  }},
  
  "metadata": {{
    "analysis_timestamp": "ISO timestamp",
    "signals_analyzed": ["list of signal types processed"],
    "limitations": ["any limitations in the analysis"],
    "assumptions": ["any assumptions made"]
  }}
}}

**CRITICAL RULES**:
1. Extract MAXIMUM intelligence - be thorough, not generic
2. Provide specific observations, not vague descriptions
3. Include confidence scores for ALL estimates
4. Clearly label speculation vs fact
5. Be forensically precise
6. Consider cultural, linguistic, and geographic context
7. Think like an investigator - what's significant? what's unusual?
8. Cross-reference multiple signals for validation
9. NO MARKDOWN in JSON - pure JSON only
10. Properly escape all strings in JSON"""

    def _add_media_to_content(self, content: List, media_path: str) -> List:
        """Add image or video with proper handling"""
        try:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(media_path)
            
            if mime_type and mime_type.startswith('image'):
                img = Image.open(media_path)
                content.append(img)
                logger.info(f"✓ Image added: {Path(media_path).name}")
                
            elif mime_type and mime_type.startswith('video'):
                # Upload video to Gemini
                uploaded_file = genai.upload_file(media_path)
                
                # Wait for processing
                timeout = 120
                start = time.time()
                
                while uploaded_file.state.name == "PROCESSING":
                    if time.time() - start > timeout:
                        raise TimeoutError("Video processing timeout")
                    time.sleep(2)
                    uploaded_file = genai.get_file(uploaded_file.name)
                
                if uploaded_file.state.name == "FAILED":
                    raise ValueError("Video processing failed")
                
                content.append(uploaded_file)
                logger.info(f"✓ Video added: {Path(media_path).name}")
            
            return content
            
        except Exception as e:
            logger.warning(f"Failed to add media: {e}")
            self._log_reasoning("media_add_failed", str(e))
            return content
    
    def _generate_with_retry(
        self, 
        content: List, 
        max_retries: int = 3
    ) -> Optional[str]:
        """Generate with exponential backoff retry"""
        
        for attempt in range(max_retries):
            try:
                generation_config = {
                    "response_mime_type": "application/json",
                    "temperature": 0.3,  # Lower for factual precision
                    "top_p": 0.95,
                    "top_k": 40,
                }
                
                self._log_reasoning("generation_attempt", 
                                  f"Attempt {attempt + 1}/{max_retries}")
                
                response = self.model.generate_content(
                    content,
                    generation_config=generation_config,
                    request_options={"timeout": 120}
                )
                
                if response and response.text:
                    self._log_reasoning("generation_success", 
                                      f"Response length: {len(response.text)}")
                    return response.text
                else:
                    self._log_reasoning("generation_empty", "Empty response received")
                
            except Exception as e:
                error_msg = str(e)
                self._log_reasoning("generation_error", 
                                  f"Attempt {attempt + 1} failed: {error_msg}")
                
                if attempt < max_retries - 1:
                    sleep_time = 2 ** attempt
                    logger.warning(f"Retry in {sleep_time}s... ({error_msg})")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"All attempts failed: {error_msg}")
                    return None
        
        return None
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response with robust error handling"""
        try:
            # Clean response
            cleaned = response_text.strip()
            
            # Remove markdown code blocks if present
            if cleaned.startswith('```'):
                lines = cleaned.split('\n')
                cleaned = '\n'.join(lines[1:-1]) if len(lines) > 2 else cleaned
                if cleaned.startswith('json'):
                    cleaned = cleaned[4:].strip()
            
            # Parse JSON
            result = json.loads(cleaned)
            
            # Ensure required fields with proper defaults
            result.setdefault('narrative_report', '')
            result.setdefault('entities', [])
            result.setdefault('exposures', [])
            result.setdefault('relationships', [])
            result.setdefault('confidence_scores', {})
            result.setdefault('extracted_data', {})
            result.setdefault('visual_intelligence', {'people': [], 'objects': []})
            
            self._log_reasoning("parse_success", f"Parsed {len(result.get('entities', []))} entities, {len(result.get('exposures', []))} exposures")
            logger.info(f"LLM generated {len(result.get('entities', []))} entities, {len(result.get('exposures', []))} exposures")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed: {e}")
            logger.error(f"Response preview: {response_text[:500]}")
            self._log_reasoning("parse_error", f"JSONDecodeError: {e}")
            
            # Return structured fallback
            return {
                "narrative_report": response_text[:5000],  # Truncate
                "entities": [],
                "exposures": [],
                "relationships": [],
                "confidence_scores": {"overall": 0.0},
                "extracted_data": {},
                "visual_intelligence": {"people": [], "objects": []},
                "parse_error": str(e),
                "raw_response": response_text[:1000]
            }
    
    def _empty_response(self, reason: str = "") -> Dict[str, Any]:
        """Return empty response structure"""
        logger.warning(f"Returning empty LLM response: {reason}")
        return {
            "analysis_status": "unavailable",
            "reason": reason,
            "narrative_report": f"LLM analysis unavailable: {reason}",
            "entities": [],
            "exposures": [],
            "relationships": [],
            "confidence_scores": {"overall": 0.0},
            "extracted_data": {},
            "visual_intelligence": {"people": [], "objects": []},
            "geolocation": {},
            "model_used": self.model_name if self.model_name else "none",
            "reasoning_trace": self.reasoning_traces.copy()
        }
    
    def _log_reasoning(self, step: str, detail: str):
        """Log reasoning step for observability"""
        trace = {
            "timestamp": time.time(),
            "step": step,
            "detail": detail
        }
        self.reasoning_traces.append(trace)
        logger.debug(f"[{step}] {detail}")
    
    def test_connection(self) -> bool:
        """Test if LLM is working"""
        if not self.model:
            return False
        
        try:
            response = self.model.generate_content("Test message. Reply with OK.")
            return bool(response.text)
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get current model information"""
        return {
            "model": self.model_name,
            "available": 1 if self.model is not None else 0,
            "api_key_set": 1 if self.api_key else 0,
            "reasoning_steps": len(self.reasoning_traces)
        }