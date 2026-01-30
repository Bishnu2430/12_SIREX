try:
    import librosa
except:
    librosa = None

def load_audio(path, sr=16000):
    if librosa:
        audio, _ = librosa.load(path, sr=sr)
        return audio
    return None