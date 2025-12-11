import asyncio

import websockets
from emotionAnalyzer import classify_emotion
from featureExtractor import extract_features
from markupGenerator import generate_markup
from PhonemeRecognizer import PhonemeRecognizer
from ttsInference import EmotionTTS

recognizer = PhonemeRecognizer()
tts_model = EmotionTTS()


async def process_audio_chunk(audio_bytes):
    features = extract_features(audio_bytes)
    emotion = classify_emotion(features)
    recog = recognizer.recognize(audio_bytes)
    markup = generate_markup(recog["phonemes"], emotion)
    tts_audio = tts_model.synthesize(markup)
    return tts_audio


async def handle_connection(websocket):
    print("Client connected.")
    try:
        async for message in websocket:
            # Each message = raw PCM audio bytes from client
            response_audio = await asyncio.to_thread(process_audio_chunk, message)
            await websocket.send(response_audio)
    except websockets.ConnectionClosed:
        print("Client disconnected.")


async def main():
    async with websockets.serve(handle_connection, "0.0.0.0", 8765, max_size=2**24):
        print("server running on ws://0.0.0.0:8765")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
