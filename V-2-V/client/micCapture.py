# import time
# import os
# import wave
import queue
import threading

import numpy as np
import sounddevice as sd


class MIC:
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_ms: int = 200,
        frames_per_buffer: int = 800,
        on_transcript_callback=None,
    ):
        self.sample_rate = sample_rate
        self.chunk_ms = chunk_ms
        self.chunk_samples = int(self.sample_rate * self.chunk_ms / 1000)
        self.frames_per_buffer = frames_per_buffer
        self.audio_q = queue.Queue()
        self._stop_flag = threading.Event()
        self._buffer = np.array([], dtype=np.int16)

    def _callback(self, indata, frames, time, status):
        if status:
            print("MicCapture status:", status)
        samples = (indata[:, 0] * 32767).astype(np.int16)
        self._buffer = np.concatenate((self._buffer, samples))
        while len(self._buffer) >= self.chunk_samples:
            chunk = self._buffer[: self.chunk_samples]
            self._buffer = self._buffer[self.chunk_samples :]
            self.audio_q.put(chunk.tobytes())

    def start(self):
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            callback=self._callback,
        )
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        with self._stream:
            while not self._stop_flag.is_set():
                sd.sleep(100)

    def stop(self):
        self._stop_flag.set()
        if self._thread.is_alive():
            self._thread.join()

    def get_chunk(self, block=True, timeout=None):
        try:
            return self.audio_q.get(block=block, timeout=timeout)
        except queue.Empty:
            return None


if __name__ == "__main__":
    mic = MIC()
    mic.start()
    try:
        while True:
            chunk = mic.get_chunk()
            if chunk is not None:
                print(f"{len(chunk)} bytes captured!!")
    except KeyboardInterrupt:
        mic.stop()
        print("Stopped.")
