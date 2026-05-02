import pyaudio
import numpy as np
import time
import logging
import threading
import pygame
from typing import Callable, Optional
import os

# Configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
THRESHOLD = 1500  # Adjust based on mic sensitivity
CLAP_WINDOW = 0.5 # Time between claps in seconds

class ClapDetector:
    def __init__(self, on_clap_callback: Callable[[], None]):
        self.on_clap_callback = on_clap_callback
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_running = False
        self.last_clap_time = 0

        # Initialize pygame for chime
        pygame.mixer.init()

    def _play_chime(self):
        """Plays a subtle activation chime."""
        try:
            # In a real scenario, you'd load a .wav file
            # For now, we'll log it. To actually play a sound, use:
            # pygame.mixer.music.load("activation_chime.wav")
            # pygame.mixer.music.play()
            logging.info("Playing activation chime...")
        except Exception as e:
            logging.error(f"Failed to play chime: {e}")

    def _detect_clap(self):
        logging.info("Clap detection engine active. Waiting for double-clap...")

        self.stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        while self.is_running:
            try:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                samples = np.frombuffer(data, dtype=np.int16)

                # Detect peak amplitude
                peak = np.max(np.abs(samples))

                if peak > THRESHOLD:
                    current_time = time.time()
                    if (current_time - self.last_clap_time) < CLAP_WINDOW:
                        logging.info("Double-clap detected!")
                        self._play_chime()
                        self.on_clap_callback()
                        self.last_clap_time = 0 # Reset after successful double clap
                    else:
                        self.last_clap_time = current_time

            except Exception as e:
                logging.error(f"Error in clap detection loop: {e}")

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._detect_clap, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

def start_clap_detection(callback):
    detector = ClapDetector(callback)
    detector.start()
    return detector
