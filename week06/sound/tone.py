# /// script
# dependencies = []
# ///
"""Save a finite sine tone. Change one parameter and compare the result."""
import argparse
import math
from pathlib import Path

from wav_support import check_settings, fade_edges, save_wav

SAMPLE_RATE = 22050
SECONDS = 2
AMPLITUDE = 0.08
FREQUENCY = 220


def make_samples(seconds=SECONDS, sample_rate=SAMPLE_RATE,
                 amplitude=AMPLITUDE, frequency=FREQUENCY):
    check_settings(seconds, sample_rate, amplitude)
    if not math.isfinite(frequency) or not 0 < frequency < sample_rate / 2:
        raise ValueError('Frequency must be positive and below half the sample rate.')
    samples = [amplitude * math.sin(2 * math.pi * frequency * i / sample_rate)
               for i in range(int(sample_rate * seconds))]
    return fade_edges(samples, sample_rate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path(__file__).parent / 'out')
    args = parser.parse_args()
    samples = make_samples()
    path = save_wav(args.out / 'tone.wav', samples, SAMPLE_RATE)
    print(f'{len(samples)} samples, {SAMPLE_RATE} samples/s, {FREQUENCY} Hz')
    print(f'saved {path} ({len(samples) / SAMPLE_RATE:g} seconds)')
    print('Lower device volume before opening the WAV in your audio player.')


if __name__ == '__main__':
    main()
