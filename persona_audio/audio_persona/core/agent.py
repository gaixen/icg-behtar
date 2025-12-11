"""Main realtime audio agent"""
import asyncio
import base64
import json
from typing import Optional

import websockets
from config.websocket_config import WebSocketConfig
from core.audio_manager import AudioStreamManager
from core.event_handler import EventHandler
from utils.logger import Logger


class RealtimeAudioAgent:
    """Main agent class coordinating audio conversation"""

    def __init__(self, api_key: str, system_prompt: str):
        """
        Initialize the audio agent

        Args:
            api_key: OpenAI API key
            system_prompt: System instructions for the agent
        """
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.ws: Optional[websockets.WebSocketClientProtocol] = None

        self.logger = Logger.setup("RealtimeAudioAgent")
        self.audio_manager = AudioStreamManager()
        self.event_handler = EventHandler(self.audio_manager, self.logger)

    async def connect(self):
        """Establish WebSocket connection and configure session"""
        self.ws = await websockets.connect(
            WebSocketConfig.URL,
            additional_headers=WebSocketConfig.get_headers(self.api_key),
        )
        self.logger.info("Connected to OpenAI Realtime API")

        config = WebSocketConfig.get_session_config(self.system_prompt)
        await self.ws.send(json.dumps(config))
        self.logger.info("Session configured with custom prompt")

    async def send_audio_loop(self):
        """Continuously send audio from microphone to API"""
        try:
            while True:
                audio_data = self.audio_manager.read_audio_chunk()
                audio_base64 = base64.b64encode(audio_data).decode()

                message = {"type": "input_audio_buffer.append", "audio": audio_base64}

                await self.ws.send(json.dumps(message))
                await asyncio.sleep(0.01)
        except Exception as e:
            self.logger.error(f"Error sending audio: {e}")

    async def receive_audio_loop(self):
        """Continuously receive and process events from API"""
        try:
            async for message in self.ws:
                event = json.loads(message)
                await self.event_handler.handle(event)
        except Exception as e:
            self.logger.error(f"Error receiving audio: {e}")

    async def run(self):
        """Start the audio conversation agent"""
        try:
            self.logger.info("Starting audio agent")
            await self.connect()
            self.audio_manager.start_streams(self.logger)

            await asyncio.gather(self.send_audio_loop(), self.receive_audio_loop())
        except KeyboardInterrupt:
            self.logger.info("Session stopped by user")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Clean up resources"""
        self.audio_manager.cleanup()
        if self.ws:
            await self.ws.close()
        self.logger.info("Session ended")
