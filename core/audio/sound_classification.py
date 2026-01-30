import librosa
import numpy as np

class SoundClassifier:
    def classify(self, audio_path):
        y, sr = librosa.load(audio_path, sr=16000)

        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        zero_crossing = np.mean(librosa.feature.zero_crossing_rate(y))

        if spectral_centroid > 3000:
            env = "traffic_or_outdoor"
        elif zero_crossing < 0.05:
            env = "indoor_quiet"
        else:
            env = "crowd_or_speech_environment"

        return {
            "environment_type": env,
            "spectral_centroid": float(spectral_centroid),
            "zero_crossing_rate": float(zero_crossing)
        }
