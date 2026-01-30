import logging
logger = logging.getLogger(__name__)

try:
    import whisper
except:
    whisper = None

class LanguageDetector:
    def __init__(self, model_size="base"):
        if whisper is None:
            self.model = None
            return
        try:
            self.model = whisper.load_model(model_size)
        except:
            self.model = None

    def detect(self, audio_path):
        if self.model is None:
            return {"language": "unknown"}
        try:
            result = self.model.transcribe(audio_path)
            return {"language": result.get("language", "unknown")}
        except:
            return {"language": "unknown"}