"""Audio stream management"""
import logging
from typing import Optional

import pyaudio
from config.audio_config import AudioConfig


class AudioStreamManager:
    """Manages PyAudio streams for input and output"""

    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.input_stream: Optional[pyaudio.Stream] = None
        self.output_stream: Optional[pyaudio.Stream] = None

    def start_streams(self, logger: logging.Logger):
        """
        Initialize and start audio input/output streams

        Args:
            logger: Logger instance for recording stream status
        """
        self.input_stream = self.audio.open(
            format=AudioConfig.FORMAT,
            channels=AudioConfig.CHANNELS,
            rate=AudioConfig.RATE,
            input=True,
            frames_per_buffer=AudioConfig.CHUNK,
        )

        self.output_stream = self.audio.open(
            format=AudioConfig.FORMAT,
            channels=AudioConfig.CHANNELS,
            rate=AudioConfig.RATE,
            output=True,
            frames_per_buffer=AudioConfig.CHUNK,
        )

        logger.info("Audio streams started")

    def read_audio_chunk(self) -> bytes:
        """
        Read one chunk of audio from input stream

        Returns:
            Audio data as bytes
        """
        return self.input_stream.read(AudioConfig.CHUNK, exception_on_overflow=False)

    def write_audio_chunk(self, audio_data: bytes):
        """
        Write audio chunk to output stream

        Args:
            audio_data: Audio data to play
        """
        self.output_stream.write(audio_data)

    def cleanup(self):
        """Close streams and terminate PyAudio"""
        if self.input_stream:
            self.input_stream.close()
        if self.output_stream:
            self.output_stream.close()
        self.audio.terminate()
