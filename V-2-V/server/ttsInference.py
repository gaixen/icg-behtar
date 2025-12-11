import io
import re

import numpy as np
import soundfile as sf
import torch
from transformers import AutoProcessor, BarkModel


class EmotionTTS:
    def __init__(self, model_name="suno/bark-small", device=None):
        print(f"Loading Bark model: {model_name}")
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model = BarkModel.from_pretrained(model_name).to(self.device)

    def _parse_emotion(self, markup_text: str):
        emotion = "neutral"
        match = re.search(r"<emotion:([a-zA-Z]+)>", markup_text)
        if match:
            emotion = match.group(1)
        text = re.sub(r"<[^>]+>", "", markup_text).strip()
        return text, emotion

    def synthesize(self, markup_text: str) -> bytes:
        """Generate emotion-rich speech from markup text and return raw WAV bytes."""
        text, emotion = self._parse_emotion(markup_text)

        # Emotion to Bark preset mapping
        emotion_map = {
            "happy": "v2/en_speaker_3",
            "sad": "v2/en_speaker_9",
            "angry": "v2/en_speaker_7",
            "neutral": "v2/en_speaker_1",
        }
        voice_preset = emotion_map.get(emotion, "v2/en_speaker_1")

        inputs = self.processor(
            text, voice_preset=voice_preset, return_tensors="pt"
        ).to(self.device)
        with torch.no_grad():
            audio_array = self.model.generate(**inputs)
        audio_array = audio_array.cpu().numpy().squeeze()

        # Convert float32 audio to WAV bytes
        buffer = io.BytesIO()
        sf.write(buffer, audio_array, 24000, format="WAV")
        buffer.seek(0)
        return buffer.read()


# tts = EmotionTTS()
# audio_bytes = tts.synthesize("<emotion:sad> Hello, how are you today?")
# with open("test_bark_sad.wav", "wb") as f:
#     f.write(audio_bytes)
# print("Saved test_bark.wav")
