"""Make local Kokoro ONNX speech on CUDA or CPU; save WAV without playing it."""

import argparse
import importlib.metadata
import io
from pathlib import Path
import sys

import common
from synthesise import DEFAULT_TEXT, VOICE, validate

MODEL = common.OUTPUT / 'models/kokoro-onnx/kokoro-v1.0.onnx'
VOICES = common.OUTPUT / 'models/kokoro-onnx/voices-v1.0.bin'


def load_voice(device='cpu'):
    import onnxruntime as ort
    from kokoro_onnx import Kokoro

    for resource in (MODEL, VOICES):
        if not resource.is_file():
            raise FileNotFoundError(f'Missing {resource}. Run prepare_models.py first.')
    providers = ['CPUExecutionProvider']
    if device == 'cuda':
        from gpu_runtime import configure_cuda
        configure_cuda()
        if 'CUDAExecutionProvider' not in ort.get_available_providers():
            raise RuntimeError('Install ONNX Runtime GPU or choose CPU speech processing.')
        providers = [('CUDAExecutionProvider', {
            'gpu_mem_limit': 1024 * 1024 * 1024,
            'arena_extend_strategy': 'kSameAsRequested',
            'cudnn_conv_use_max_workspace': '0',
        }), 'CPUExecutionProvider']
    options = ort.SessionOptions()
    options.log_severity_level = 3
    options.enable_mem_pattern = device != 'cuda'
    session = ort.InferenceSession(str(MODEL), sess_options=options, providers=providers)
    if device == 'cuda' and 'CUDAExecutionProvider' not in session.get_providers():
        raise RuntimeError('Kokoro could not load CUDA. Check its CUDA libraries or choose CPU.')
    return Kokoro.from_session(session, str(VOICES))


def synthesise(text, speed=1.0, device='cpu', voice=None):
    import numpy as np
    import soundfile as sf

    text = validate(text, speed)
    voice = voice or load_voice(device)
    try:
        audio, rate = voice.create(text, voice=VOICE, speed=speed, lang='en-us')
    except Exception as error:
        # ONNX's binding exceptions do not inherit Python's RuntimeError.
        raise RuntimeError(f'Kokoro inference failed: {error}') from error
    if audio.ndim != 1 or not np.isfinite(audio).all() or not 0 < len(audio) <= rate * 60:
        raise ValueError('Expected finite mono audio of at most 60 seconds.')
    buffer = io.BytesIO()
    sf.write(buffer, audio, rate, format='WAV', subtype='PCM_16')
    return buffer.getvalue(), len(audio) / rate


def synthesise_reply(text, speed=1.0, device='cpu', voice=None):
    """Speak a chat reply in bounded pieces, retaining the whole reply's audio."""
    import numpy as np
    import soundfile as sf
    import textwrap
    import re

    if not text.strip() or len(text) > 1000:
        raise ValueError('Keep spoken chat replies between 1 and 1000 characters.')
    voice = voice or load_voice(device)
    parts = []
    pieces = [piece for sentence in re.split(r'(?<=[.!?])\s+', text.strip())
              for piece in textwrap.wrap(sentence, width=140)]
    for piece in pieces:
        data, _ = synthesise(piece, speed, device, voice)
        audio, rate = sf.read(io.BytesIO(data), dtype='float32')
        parts.append(audio)
    audio = np.concatenate(parts)
    if len(audio) > rate * 60:
        raise ValueError('Spoken reply exceeds 60 seconds. Increase voice speed or ask for a shorter reply.')
    buffer = io.BytesIO()
    sf.write(buffer, audio, rate, format='WAV', subtype='PCM_16')
    return buffer.getvalue(), len(audio) / rate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--text', default=DEFAULT_TEXT)
    parser.add_argument('--speed', type=float, default=1.0)
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    parser.add_argument('--out', type=Path, default=common.OUTPUT / 'kokoro-onnx.wav')
    parser.add_argument('--check', action='store_true', help='Check metadata and local files without loading models')
    args = parser.parse_args()
    try:
        if args.check:
            ready = True
            for package in ('kokoro-onnx', 'onnxruntime', 'soundfile', 'numpy'):
                try:
                    print(f'{package}: {importlib.metadata.version(package)}')
                except importlib.metadata.PackageNotFoundError:
                    if package == 'onnxruntime':
                        try:
                            print(f'onnxruntime-gpu: {importlib.metadata.version("onnxruntime-gpu")}')
                            continue
                        except importlib.metadata.PackageNotFoundError:
                            pass
                    print(f'{package}: MISSING')
                    ready = False
            for resource in (MODEL, VOICES):
                present = resource.is_file()
                print(f'{resource.name}: {"present" if present else "MISSING"}')
                ready &= present
            print('File presence does not verify inference or CUDA libraries.')
            return 0 if ready else 1
        text = validate(args.text, args.speed)
        common.check_output(args.out, '.wav')
        data, duration = synthesise(text, args.speed, args.device)
        common.save_outputs(args.out, data, {
            'model': str(MODEL), 'backend': 'kokoro-onnx', 'device': args.device,
            'voice': VOICE, 'text': text, 'speed': args.speed,
            'sample_rate_hz': 24000, 'duration_seconds': duration, 'synthetic': True,
        })
        print(f'Saved {args.out} ({duration:.2f}s) and settings. Open the WAV to listen.')
        return 0
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        print(f'Cannot synthesise: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
