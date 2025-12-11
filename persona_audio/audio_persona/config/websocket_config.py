"""WebSocket API configuration"""


class WebSocketConfig:
    """WebSocket connection and session configuration"""

    URL = (
        "wss://api.openai.com/v1/realtime?model=gpt-4o-mini-realtime-preview-2024-12-17"
    )

    @staticmethod
    def get_headers(api_key: str) -> dict:
        """Generate WebSocket connection headers"""
        return {"Authorization": f"Bearer {api_key}", "OpenAI-Beta": "realtime=v1"}

    @staticmethod
    def get_session_config(system_prompt: str) -> dict:
        """Generate session configuration"""
        return {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": system_prompt,
                "voice": "echo",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {"type": "server_vad"},
            },
        }
