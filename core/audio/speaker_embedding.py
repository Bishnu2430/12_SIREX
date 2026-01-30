import numpy as np
import librosa

class SpeakerEmbedder:
    def extract(self, audio_path):
        y, sr = librosa.load(audio_path, sr=16000)

        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
        embedding = np.mean(mfcc, axis=1)

        return embedding
