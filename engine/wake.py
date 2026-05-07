"""
engine/wake.py — Tony Stark wake sound player.
Place wake_sound.mp3 in the project root.
"""
import os
import sys
import logging
import threading

logger = logging.getLogger("Wake")

# Resolve path relative to project root (two levels up from engine/)
_PROJECT_ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WAKE_SOUND_PATH = os.path.join(_PROJECT_ROOT, "wake_sound.mp3")


def play_wake_sound():
    """
    Play wake_sound.mp3 non-blocking in a daemon thread.
    Tries pygame first, then macOS afplay, then system default.
    """
    def _play():
        if not os.path.exists(WAKE_SOUND_PATH):
            logger.warning(f"Wake sound not found: {WAKE_SOUND_PATH}")
            return

        # ── Try pygame ──────────────────────────────────────────
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(WAKE_SOUND_PATH)
            pygame.mixer.music.play()
            import time
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
            logger.info("Wake sound played via pygame.")
            return
        except Exception as e:
            logger.debug(f"pygame unavailable ({e}), trying system player.")

        # ── macOS afplay ────────────────────────────────────────
        if sys.platform == "darwin":
            import subprocess
            try:
                subprocess.Popen(["afplay", WAKE_SOUND_PATH])
                logger.info("Wake sound played via afplay.")
                return
            except Exception as e:
                logger.warning(f"afplay failed: {e}")

        # ── Linux mpg123 ────────────────────────────────────────
        elif sys.platform.startswith("linux"):
            import subprocess
            try:
                subprocess.Popen(["mpg123", "-q", WAKE_SOUND_PATH])
                logger.info("Wake sound played via mpg123.")
                return
            except Exception as e:
                logger.warning(f"mpg123 failed: {e}")

        # ── Windows ─────────────────────────────────────────────
        elif sys.platform == "win32":
            import subprocess
            try:
                subprocess.Popen(["start", "", WAKE_SOUND_PATH], shell=True)
                logger.info("Wake sound played via Windows start.")
                return
            except Exception as e:
                logger.warning(f"Windows player failed: {e}")

        logger.error("All wake sound playback methods failed.")

    threading.Thread(target=_play, daemon=True).start()
