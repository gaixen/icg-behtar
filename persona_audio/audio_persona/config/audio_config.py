"""Audio stream configuration constants"""
import pyaudio


class AudioConfig:
    """Audio stream configuration"""

    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 24000
