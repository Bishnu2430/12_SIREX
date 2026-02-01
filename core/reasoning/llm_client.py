import os
import logging
import time
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
            
            # REMOVED Google Search Tool to reduce quota usage
            # If you need search, add it back but be aware of rate limits
            
            # Use stable model name
            model_name = config.LLM_MODEL
            
            # Fix model name - use stable version
            if not model_name or "2.5" in model_name:
                logger.warning(f"Invalid model '{model_name}', using gemini-1.5-flash instead")
                model_name = "gemini-1.5-flash"
            
            # Remove any "models/" prefix if present
            if model_name.startswith("models/"):
                model_name = model_name.replace("models/", "")
            
            # Initialize WITHOUT search tool to reduce quota
            self.model = genai.GenerativeModel(model_name)
            logger.info(f"LLM Client initialized with {model_name}")
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

            # Retry logic with exponential backoff
            max_retries = 3
            retry_delay = 2
            response = None
            
            for attempt in range(max_retries):
                try:
                    # Using JSON mode if model supports it
                    generation_config = {"response_mime_type": "application/json"}
                    try:
                        response = self.model.generate_content(content, generation_config=generation_config)
                    except:
                        # Fallback without JSON mode
                        response = self.model.generate_content(content)
                    
                    # Success - break retry loop
                    break
                    
                except Exception as api_error:
                    error_msg = str(api_error)
                    
                    # Check if it's a rate limit error
                    if "quota" in error_msg.lower() or "limit" in error_msg.lower() or "429" in error_msg:
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                            logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"Rate limit exhausted after {max_retries} attempts")
                            raise Exception(f"Gemini API quota exhausted. Please check your API key limits or try again later.")
                    else:
                        # Non-rate-limit error, don't retry
                        raise
            
            # Cleanup uploaded file
            if uploaded_file:
                try:
                    genai.delete_file(uploaded_file.name)
                    logger.info("Cleaned up uploaded video file.")
                except:
                    pass

            import json
            import re
            
                return json_data
                    
            except Exception as parse_e:
                logger.error(f"Failed to parse LLM JSON: {parse_e}")
                return {"narrative_report": response.text, "exposures": []}

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {"narrative_report": f"LLM Analysis Failed: {e}", "exposures": []}
