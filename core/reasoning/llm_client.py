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
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found. LLM analysis will be disabled.")
            self.model = None
            return

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            logger.info("LLM Client initialized with Gemini 1.5 Flash")
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
                mime_type, _ = mimetypes.guess_type(image_path)
                
                is_video = mime_type and mime_type.startswith('video')
                
                if is_video:
                    try:
                        logger.info(f"Uploading video for analysis: {image_path}")
                        uploaded_file = genai.upload_file(image_path)
                        
                        # Wait for video processing
                        while uploaded_file.state.name == "PROCESSING":
                            time.sleep(2)
                            uploaded_file = genai.get_file(uploaded_file.name)
                            
                        if uploaded_file.state.name == "FAILED":
                            raise ValueError("Video processing failed.")
                            
                        logger.info(f"Video processing complete: {uploaded_file.uri}")
                        content.append(uploaded_file)
                    except Exception as vid_e:
                        logger.warning(f"Failed to process video: {vid_e}")
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
            try:
                text = response.text.replace("```json", "").replace("```", "").strip()
                return json.loads(text)
            except json.JSONDecodeError:
                return {"narrative_report": response.text, "exposures": []}

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {"narrative_report": f"LLM Analysis Failed: {e}", "exposures": []}
