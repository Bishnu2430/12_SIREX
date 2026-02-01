import logging
logger = logging.getLogger(__name__)

try:
    import librosa, numpy as np
except:
    librosa = None

class SpeechDetector:
    def __init__(self, threshold=0.01):
        self.threshold = threshold

    def detect(self, audio_path):
        if librosa is None:
            return {"speech_present": 0, "energy_level": 0.0}
        try:
            y, sr = librosa.load(audio_path, sr=16000)
            energy = float(np.mean(np.abs(y)))
            speech_present = 1 if energy > self.threshold else 0
            return {"speech_present": speech_present, "energy_level": round(energy, 5)}
        except Exception as e:
            logger.error(f"Speech detection failed: {e}")
            return {"speech_present": 0, "energy_level": 0.0}