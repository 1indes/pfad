# /// script
# dependencies = []
# ///
"""Save two seconds of seeded noise. Nothing plays automatically."""
import argparse
from pathlib import Path
import random

from wav_support import check_settings, fade_edges, save_wav

SAMPLE_RATE = 22050
SECONDS = 2
AMPLITUDE = 0.08
SEED = 7


def make_samples(seconds=SECONDS, sample_rate=SAMPLE_RATE,
                 amplitude=AMPLITUDE, seed=SEED):
    check_settings(seconds, sample_rate, amplitude)
    rng = random.Random(seed)
    samples = [rng.uniform(-amplitude, amplitude)
               for _ in range(int(sample_rate * seconds))]
    return fade_edges(samples, sample_rate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path(__file__).parent / 'out')
    args = parser.parse_args()
    samples = make_samples()
    path = save_wav(args.out / 'noise.wav', samples, SAMPLE_RATE)
    print(f'{len(samples)} samples, {SAMPLE_RATE} samples/s, mono 16-bit PCM')
    print(f'saved {path} ({len(samples) / SAMPLE_RATE:g} seconds)')
    print('Lower device volume before opening the WAV in your audio player.')


if __name__ == '__main__':
    main()
