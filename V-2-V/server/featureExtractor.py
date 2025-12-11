import io

import librosa
import numpy as np
import soundfile as sf


def extract_features(audio_bytes, sample_rate=16000):
    audio, _ = sf.read(io.BytesIO(audio_bytes), dtype="float32")
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    f0, voiced_flag, _ = librosa.pyin(audio, fmin=80, fmax=300)
    f0 = np.nan_to_num(f0)
    energy = np.sqrt(np.mean(audio**2))
    tempo, _ = librosa.beat.beat_track(y=audio, sr=sample_rate)

    features = {
        "f0_mean": float(np.mean(f0)),
        "f0_std": float(np.std(f0)),
        "energy": float(energy),
        "tempo": float(tempo),
    }
    return features
