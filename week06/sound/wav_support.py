"""Small standard-library helpers for the Week 6 WAV examples."""
import math
from pathlib import Path
import struct
import wave


def check_settings(seconds, sample_rate, amplitude):
    if not math.isfinite(seconds) or not 0 < seconds <= 10:
        raise ValueError('Use a finite duration between 0 and 10 seconds.')
    if not isinstance(sample_rate, int) or sample_rate <= 0:
        raise ValueError('Sample rate must be a positive integer.')
    if not math.isfinite(amplitude) or not 0 <= amplitude <= 0.25:
        raise ValueError('Use an amplitude between 0 and 0.25 for this example.')
    if int(seconds * sample_rate) < 2:
        raise ValueError('This example needs at least two samples.')


def fade_edges(samples, sample_rate):
    """10 ms at each end reduces sudden jumps and audible clicks."""
    fade = max(1, min(round(0.01 * sample_rate), len(samples) // 2))
    return [value * min(1, i / fade, (len(samples) - 1 - i) / fade)
            for i, value in enumerate(samples)]


def save_wav(path, samples, sample_rate):
    """Convert normalized values to little-endian signed 16-bit mono PCM."""
    if not samples or any(not math.isfinite(x) or abs(x) > 1 for x in samples):
        raise ValueError('WAV values must be finite, nonempty and within -1 to 1.')
    pcm = b''.join(struct.pack('<h', round(value * 32767)) for value in samples)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(pcm)
    return path
