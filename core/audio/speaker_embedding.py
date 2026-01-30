import logging, numpy as np
logger = logging.getLogger(__name__)

try:
    import librosa
except:
    librosa = None

class SpeakerEmbedder:
    def extract(self, audio_path):
        if librosa is None:
            return np.random.rand(40)
        try:
            y, sr = librosa.load(audio_path, sr=16000)
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
            embedding = np.mean(mfcc, axis=1)
            return embedding
        except:
            return np.random.rand(40)