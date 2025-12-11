import queue
import threading

import numpy as np
import sounddevice as sd
from micCapture import MIC


class AudioPlayback:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.play_q = queue.Queue()
        self._stop_flag = threading.Event()

    def _callback(self, outdata, frames, time, status):
        if status:
            print("AudioPlayback status:", status)
        try:
            data = self.play_q.get_nowait()
            samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32767.0
            if len(samples) < frames:
                samples = np.pad(samples, (0, frames - len(samples)))
            outdata[:, 0] = samples[:frames]
        except queue.Empty:
            outdata.fill(0)

    def start(self):
        self._stream = sd.OutputStream(
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

    def put_chunk(self, chunk: bytes):
        self.play_q.put(chunk)


if __name__ == "__main__":
    mic = MIC()
    player = AudioPlayback()
    mic.start()
    player.start()
    print("Loopback test...")
    try:
        while True:
            chunk = mic.get_chunk()
            if chunk:
                player.put_chunk(chunk)
    except KeyboardInterrupt:
        mic.stop()
        player.stop()
