"""WebSocket event handling"""
import base64
import logging

from core.audio_manager import AudioStreamManager


class EventHandler:
    """Handles WebSocket events from the API"""

    def __init__(self, audio_manager: AudioStreamManager, logger: logging.Logger):
        """
        Initialize event handler

        Args:
            audio_manager: Audio stream manager instance
            logger: Logger for recording events
        """
        self.audio_manager = audio_manager
        self.logger = logger

    async def handle(self, event: dict):
        """
        Process incoming WebSocket events

        Args:
            event: Event dictionary from WebSocket
        """
        event_type = event.get("type")

        if event_type == "response.audio.delta":
            self._handle_audio_delta(event)
        elif event_type == "input_audio_buffer.speech_started":
            self.logger.info("Speech detected")
        elif event_type == "input_audio_buffer.speech_stopped":
            self.logger.info("Speech ended")
        elif event_type == "error":
            self._handle_error(event)

    def _handle_audio_delta(self, event: dict):
        """
        Process audio response from API

        Args:
            event: Audio delta event
        """
        audio_data = base64.b64decode(event.get("delta", ""))
        self.audio_manager.write_audio_chunk(audio_data)

    def _handle_error(self, event: dict):
        """
        Log API errors

        Args:
            event: Error event
        """
        error = event.get("error", {})
        self.logger.error(f"API Error: {error.get('message', 'Unknown error')}")
