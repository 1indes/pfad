"""Make a short synthetic English voice with Kokoro; save WAV and settings, never autoplay."""

import argparse
import io
import math
from pathlib import Path
import sys

import common

RATE = 24000
VOICE = 'af_heart'
DEFAULT_TEXT = 'Sound can guide attention. A spoken cue can make an interface easier to use.'


def validate(text, speed):
    text = text.strip()
    if not text or len(text) > 500:
        raise ValueError('Use 1-500 characters of text.')
    if not math.isfinite(speed) or not 0.5 <= speed <= 2:
        raise ValueError('Use a finite --speed between 0.5 and 2.0.')
    return text


def audio_parts(pipeline, text, speed):
    # Kokoro yields several chunks for longer text. Keep every one, in order.
    parts = [audio.cpu().numpy() for _, _, audio in pipeline(text, voice=VOICE, speed=speed) if audio is not None]
    if not parts or not any(len(part) for part in parts):
        raise ValueError('The model returned no audio. Try a short English sentence.')
    return parts


def synthesise(text, speed, offline):
    common.configure_network(offline)
    from kokoro import KPipeline
    import numpy as np
    import soundfile as sf

    pipeline = KPipeline(lang_code='a', repo_id=common.MODELS['kokoro'][0], device='cpu')
    audio = np.concatenate(audio_parts(pipeline, text, speed))
    if audio.ndim != 1 or not np.isfinite(audio).all() or len(audio) > RATE * 60:
        raise ValueError('Expected finite mono audio of at most 60 seconds. Shorten the text.')
    buffer = io.BytesIO()
    sf.write(buffer, audio, RATE, format='WAV', subtype='PCM_16')
    return buffer.getvalue(), len(audio) / RATE


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--text', default=DEFAULT_TEXT)
    parser.add_argument('--speed', type=float, default=1.0)
    parser.add_argument('--out', type=Path, default=common.OUTPUT / 'kokoro.wav', help='New .wav path; also saves .json settings')
    parser.add_argument('--check', action='store_true', help='Offline dependency/cache preflight; no model loading')
    parser.add_argument('--offline', action='store_true', help='Use cached models; language package must already be installed')
    args = parser.parse_args(argv)
    if args.check:
        return 0 if common.preflight('kokoro') else 1
    try:
        text = validate(args.text, args.speed)
        common.check_output(args.out, '.wav')
        # Require spaCy's English resource before KPipeline, which could otherwise install it implicitly.
        common.require_dependencies('kokoro')
        print('Loading Kokoro on CPU. First run may download weights; --offline forbids that.', flush=True)
        data, duration = synthesise(text, args.speed, args.offline)
        settings = {'model':common.MODELS['kokoro'][0], 'text':text, 'voice':VOICE, 'speed':args.speed,
                    'language':'a', 'device':'cpu', 'sample_rate_hz':RATE, 'duration_seconds':duration,
                    'synthetic':True, 'versions':common.versions('kokoro')}
        common.save_outputs(args.out, data, settings)
        print(f'Saved {args.out} ({duration:.2f}s) and {args.out.with_suffix(".json")}. Open the WAV to listen.')
        return 0
    except KeyboardInterrupt:
        print('\nStopped. No output files saved.')
        return 130
    except (OSError, ValueError, RuntimeError, ImportError) as error:
        print(f'Cannot synthesise: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
