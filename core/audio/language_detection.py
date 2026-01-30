import whisper

class LanguageDetector:
    def __init__(self, model_size="base"):
        self.model = whisper.load_model(model_size)

    def detect(self, audio_path):
        result = self.model.transcribe(audio_path)
        return {
            "language": result.get("language", "unknown")
        }
