import array
import math
import pygame

SAMPLE_RATE = 22050


def _tone(notes, volume=0.4):
    """Build a Sound from a list of (frequency, ms) notes, no audio files needed."""
    samples = array.array("h")
    for freq, dur in notes:
        n = int(SAMPLE_RATE * dur / 1000)
        for i in range(n):
            fade = 1 - i / n  # fade out so it doesn't click
            value = math.sin(2 * math.pi * freq * i / SAMPLE_RATE) * fade
            samples.append(int(value * volume * 32767))
    return pygame.mixer.Sound(buffer=samples.tobytes())


class Sounds:
    def __init__(self):
        self.enabled = True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
            self.bounce = _tone([(220, 70)])
            self.win = _tone([(523, 120), (659, 120), (784, 250)])
            self.timeout = _tone([(300, 200), (220, 200), (150, 400)])
        except pygame.error:
            # no audio device, just play silently
            self.enabled = False

    def play(self, name):
        if self.enabled:
            getattr(self, name).play()
