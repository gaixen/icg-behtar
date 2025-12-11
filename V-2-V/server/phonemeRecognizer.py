import io

import soundfile as sf
import whisper
from phonemizer import phonemize


class PhonemeRecognizer:
    """ASR + phoneme extractor."""

    def __init__(self, model_name="base"):
        self.model = whisper.load_model(model_name)

    def recognize(self, audio_bytes):
        audio, _ = sf.read(io.BytesIO(audio_bytes))
        result = self.model.transcribe(audio)
        text = result["text"]
        phonemes = phonemize(text, language="en-us", backend="espeak")
        return {"text": text, "phonemes": phonemes}
