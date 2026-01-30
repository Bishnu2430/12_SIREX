import logging
logger = logging.getLogger(__name__)

try:
    import librosa, numpy as np
except:
    librosa = None

class SoundClassifier:
    def classify(self, audio_path):
        if librosa is None:
            return {"environment_type": "unknown", "spectral_centroid": 0.0, "zero_crossing_rate": 0.0}
        try:
            y, sr = librosa.load(audio_path, sr=16000)
            spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
            zero_crossing = float(np.mean(librosa.feature.zero_crossing_rate(y)))
            
            if spectral_centroid > 3000:
                env = "traffic_or_outdoor"
            elif zero_crossing < 0.05:
                env = "indoor_quiet"
            else:
                env = "crowd_or_speech_environment"

            return {
                "environment_type": env,
                "spectral_centroid": round(spectral_centroid, 2),
                "zero_crossing_rate": round(zero_crossing, 4)
            }
        except Exception as e:
            logger.error(f"Sound classification failed: {e}")
            return {"environment_type": "unknown", "spectral_centroid": 0.0, "zero_crossing_rate": 0.0}