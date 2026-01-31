import os
import logging
import google.generativeai as genai
from core.reasoning.prompts import (
    SYSTEM_ROLE_PROMPT,
    INPUT_DESCRIPTION_PROMPT,
    CORE_ANALYSIS_INSTRUCTIONS,
    ANTI_HALLUCINATION_PROMPT
)

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        from app.config import config
        api_key = config.GOOGLE_API_KEY
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found. LLM analysis will be disabled.")
            self.model = None
            return

        try:
            from app.config import config
            genai.configure(api_key=api_key)
            
            # Enable Search Tool
            tools = [
                {"google_search_retrieval": {
                    "dynamic_retrieval_config": {
                        "mode": "dynamic",
                        "dynamic_threshold": 0.3,
                    }
                }}
            ]
            
            # Use just the model name without any prefix
            model_name = config.LLM_MODEL
            # Remove any "models/" prefix if present
            if model_name.startswith("models/"):
                model_name = model_name.replace("models/", "")
            
            self.model = genai.GenerativeModel(model_name, tools=tools)
            logger.info(f"LLM Client initialized with {model_name} and Search Grounding")
        except Exception as e:
            logger.error(f"Failed to initialize LLM Client: {e}")
            self.model = None

    def analyze_signals(self, signals, image_path=None, context="General OSINT Investigation"):
        if not self.model:
            return "LLM Analysis Unavailable: API Key missing or initialization failed."

        try:
            prompt_parts = [
                SYSTEM_ROLE_PROMPT,
                INPUT_DESCRIPTION_PROMPT.format(input_type="mixed", context=context),
                CORE_ANALYSIS_INSTRUCTIONS,
                f"\n=== INPUT SIGNALS ===\n{signals}\n",
                ANTI_HALLUCINATION_PROMPT
            ]

            # If media path is provided, handle image or video
            content = prompt_parts
            uploaded_file = None
            
            if image_path and os.path.exists(image_path):
                import mimetypes
                import time
                import mimetypes
                import time
                mime_type, _ = mimetypes.guess_type(image_path)
                
                # Check for video or audio
                is_video = mime_type and mime_type.startswith('video')
                is_audio = mime_type and mime_type.startswith('audio')
                
                if is_video or is_audio:
                    try:
                        media_type = "video" if is_video else "audio"
                        logger.info(f"Uploading {media_type} for analysis: {image_path}")
                        uploaded_file = genai.upload_file(image_path)
                        
                        # Wait for processing
                        while uploaded_file.state.name == "PROCESSING":
                            time.sleep(2)
                            uploaded_file = genai.get_file(uploaded_file.name)
                            
                        if uploaded_file.state.name == "FAILED":
                            raise ValueError(f"{media_type} processing failed.")
                            
                        logger.info(f"{media_type} processing complete: {uploaded_file.uri}")
                        content.append(uploaded_file)
                    except Exception as vid_e:
                        logger.warning(f"Failed to process media file: {vid_e}")
                else:
                    try:
                        from PIL import Image
                        img = Image.open(image_path)
                        content.append(img)
                        logger.info(f"Attached image for analysis: {image_path}")
                    except Exception as img_e:
                        logger.warning(f"Failed to load image for LLM: {img_e}")

            # Using JSON mode if model supports it, otherwise prompt engineering handles it
            generation_config = {"response_mime_type": "application/json"}
            try:
                response = self.model.generate_content(content, generation_config=generation_config)
            except:
                # Fallback
                response = self.model.generate_content(content)
            
            # Cleanup uploaded file
            if uploaded_file:
                try:
                    genai.delete_file(uploaded_file.name)
                    logger.info("Cleaned up uploaded video file.")
                except:
                    pass

            import json
            import re
            
            try:
                text = response.text
                reasoning_text = ""
                json_data = {"narrative_report": text, "exposures": []}
                
                # Attempt to find JSON block using regex if direct parse fails
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                
                if json_match:
                     json_str = json_match.group(0)
                     # Capture text BEFORE the JSON as reasoning
                     reasoning_text = text[:json_match.start()].strip()
                     try:
                        json_data = json.loads(json_str)
                     except:
                        pass
                else:
                    # Try cleaning code blocks manually as fallback
                    clean_text = text.replace("```json", "").replace("```", "").strip()
                    try:
                        json_data = json.loads(clean_text)
                    except:
                        pass
                
                json_data["reasoning_trace"] = reasoning_text
                return json_data
                    
            except Exception as parse_e:
                logger.error(f"Failed to parse LLM JSON: {parse_e}")
                return {"narrative_report": response.text, "exposures": []}

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {"narrative_report": f"LLM Analysis Failed: {e}", "exposures": []}
