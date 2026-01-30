import librosa
import numpy as np

class SpeechDetector:
    def __init__(self, threshold=0.01):
        self.threshold = threshold

    def detect(self, audio_path):
        y, sr = librosa.load(audio_path, sr=16000)

        energy = np.mean(np.abs(y))
        speech_present = energy > self.threshold

        return {
            "speech_present": bool(speech_present),
            "energy_level": float(round(energy, 5))
        }
