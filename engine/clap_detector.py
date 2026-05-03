"""
Clap Detector — Doraemon Activation Engine
==========================================
Supports:
  - Single clap  → wake / activate agent
  - Double clap  → activate + open briefing URLs
  - Triple clap  → mute / standby toggle

Thresholds and timing are configurable via .env or constructor args.
"""

import pyaudio
import numpy as np
import time
import logging
import threading
import asyncio
from typing import Callable, Optional

logger = logging.getLogger("ClapDetector")

# ── Audio config ──────────────────────────────────────────────
CHUNK        = 1024
FORMAT       = pyaudio.paInt16
CHANNELS     = 1
RATE         = 44100
THRESHOLD    = 1500   # Amplitude peak — raise if false positives, lower if misses
CLAP_WINDOW  = 0.45   # Max seconds between claps to count as a sequence
COOLDOWN     = 1.5    # Seconds to ignore claps after a sequence fires


class ClapDetector:
    """
    Non-blocking audio clap detector.
    Runs in a daemon thread; fires async callbacks via the provided event loop.
    """

    def __init__(
        self,
        on_single_clap:  Optional[Callable] = None,
        on_double_clap:  Optional[Callable] = None,
        on_triple_clap:  Optional[Callable] = None,
        threshold:       int   = THRESHOLD,
        clap_window:     float = CLAP_WINDOW,
        cooldown:        float = COOLDOWN,
        loop:            Optional[asyncio.AbstractEventLoop] = None,
    ):
        self.on_single_clap = on_single_clap
        self.on_double_clap = on_double_clap
        self.on_triple_clap = on_triple_clap
        self.threshold      = threshold
        self.clap_window    = clap_window
        self.cooldown       = cooldown
        self.loop           = loop or asyncio.get_event_loop()

        self._p             = pyaudio.PyAudio()
        self._stream        = None
        self._running       = False
        self._thread        = None

        # State machine
        self._clap_times: list[float] = []
        self._last_fire    = 0.0

    # ── Public API ────────────────────────────────────────────

    def start(self):
        """Start listening in a background daemon thread."""
        self._running = True
        self._thread  = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("ClapDetector: listening started.")

    def stop(self):
        """Stop listening and release audio resources."""
        self._running = False
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
        self._p.terminate()
        logger.info("ClapDetector: stopped.")

    # ── Internal ─────────────────────────────────────────────

    def _listen_loop(self):
        self._stream = self._p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )
        logger.info(f"ClapDetector: audio stream open (threshold={self.threshold})")

        while self._running:
            try:
                raw     = self._stream.read(CHUNK, exception_on_overflow=False)
                samples = np.frombuffer(raw, dtype=np.int16)
                peak    = int(np.max(np.abs(samples)))

                if peak > self.threshold:
                    now = time.time()

                    # Ignore if still in cooldown
                    if (now - self._last_fire) < self.cooldown:
                        continue

                    # Drop clap times that are too old
                    self._clap_times = [
                        t for t in self._clap_times
                        if (now - t) < self.clap_window
                    ]
                    self._clap_times.append(now)

                    # Wait briefly to see if more claps follow
                    time.sleep(self.clap_window)

                    count = len(self._clap_times)
                    self._clap_times.clear()
                    self._last_fire = time.time()

                    logger.info(f"ClapDetector: {count}-clap sequence detected.")
                    self._dispatch(count)

            except OSError as e:
                logger.warning(f"ClapDetector audio error (continuing): {e}")
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"ClapDetector unexpected error: {e}")
                break

    def _dispatch(self, count: int):
        """Fire the appropriate async callback on the event loop."""
        cb = None
        if count == 1 and self.on_single_clap:
            cb = self.on_single_clap
        elif count == 2 and self.on_double_clap:
            cb = self.on_double_clap
        elif count >= 3 and self.on_triple_clap:
            cb = self.on_triple_clap
        else:
            # Default: single handler covers any unregistered count
            if self.on_single_clap:
                cb = self.on_single_clap

        if cb:
            if asyncio.iscoroutinefunction(cb):
                asyncio.run_coroutine_threadsafe(cb(), self.loop)
            else:
                self.loop.call_soon_threadsafe(cb)


# ── Convenience factory ───────────────────────────────────────

def start_clap_detection(
    on_single_clap:  Optional[Callable] = None,
    on_double_clap:  Optional[Callable] = None,
    on_triple_clap:  Optional[Callable] = None,
    loop:            Optional[asyncio.AbstractEventLoop] = None,
) -> ClapDetector:
    """
    Create and start a ClapDetector with optional per-clap-count callbacks.
    Returns the detector so the caller can stop() it later.
    """
    detector = ClapDetector(
        on_single_clap=on_single_clap,
        on_double_clap=on_double_clap,
        on_triple_clap=on_triple_clap,
        loop=loop,
    )
    detector.start()
    return detector