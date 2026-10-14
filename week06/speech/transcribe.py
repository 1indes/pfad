"""Transcribe a short WAV or explicitly opt into finite, chunked microphone capture."""

import argparse
from pathlib import Path
from queue import Empty, Full, Queue
import math
import sys
import wave

import common

RATE = 16000


def capture_frames(chunks, seconds):
    if not 1 <= chunks <= 12 or not math.isfinite(seconds) or not 1 <= seconds <= 15 or chunks * seconds > 60:
        raise ValueError('Use 1-12 chunks, 1-15 seconds each, and at most 60 seconds total.')
    return round(seconds * RATE)


def validate_wav(path):
    try:
        with wave.open(str(path), 'rb') as audio:
            if (audio.getsampwidth() != 2 or audio.getnchannels() not in (1, 2)
                    or not 8000 <= audio.getframerate() <= 192000):
                raise ValueError('Use a nonempty, 16-bit PCM WAV, mono/stereo, 8-192 kHz, at most 60 seconds long.')
            duration = audio.getnframes() / audio.getframerate()
            if not 0 < duration <= 60:
                raise ValueError('Use a nonempty WAV at most 60 seconds long.')
            return duration
    except (wave.Error, EOFError) as error:
        raise ValueError('Use an uncompressed 16-bit PCM WAV file.') from error


def load_model(offline, model_name=None, device='cpu'):
    common.configure_network(offline)
    from faster_whisper import WhisperModel
    if device == 'cuda':
        from gpu_runtime import configure_cuda
        configure_cuda()
    selected = model_name or common.whisper_model()
    return WhisperModel(selected, device=device,
                        compute_type=common.whisper_compute_type(selected, device), local_files_only=offline)


def transcribe_audio(model, audio):
    # A filename is decoded/resampled by faster-whisper. An array must already be mono 16 kHz.
    segments, _ = model.transcribe(audio, language='en', beam_size=1,
                                  vad_filter=True, condition_on_previous_text=False)
    return ' '.join(segment.text.strip() for segment in segments).strip()


def microphone_lines(model, chunks, seconds):
    import sounddevice as sd

    frames = capture_frames(chunks, seconds)
    blocks = Queue(maxsize=chunks)  # At most 60 seconds of audio, even when inference is slow.
    problems = []
    captured = 0

    def capture(indata, count, timing, status):
        nonlocal captured
        if status or count != frames:
            problems.append(str(status) if status else 'Unexpected audio block length')
            try:
                blocks.put_nowait(None)
            except Full:
                pass
            raise sd.CallbackAbort
        try:
            blocks.put_nowait(indata[:, 0].copy())
        except Full:
            problems.append('Audio queue overflow')
            raise sd.CallbackAbort
        captured += 1
        if captured >= chunks:
            raise sd.CallbackStop

    print(f'Recording {chunks * seconds:g} seconds continuously. Ctrl+C stops. Text may lag.', flush=True)
    lines = []
    try:
        with sd.InputStream(samplerate=RATE, channels=1, dtype='float32', blocksize=frames, callback=capture):
            for number in range(chunks):
                try:
                    audio = blocks.get(timeout=seconds + 5)
                except Empty as error:
                    raise RuntimeError('Microphone timed out. Check its permission/device or use --audio.') from error
                if problems:
                    raise RuntimeError('Microphone error: ' + '; '.join(problems))
                text = transcribe_audio(model, audio)
                start, end = number * frames / RATE, (number + 1) * frames / RATE
                line = f'[{start:.2f}-{end:.2f}s] {text or "[no speech detected]"}'
                lines.append(line)
                print(line, flush=True)
    except sd.PortAudioError as error:
        raise RuntimeError(f"Cannot open/read the microphone: {error}. Check permission/device or use --audio.") from error
    finally:
        sd.stop()
    return lines


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument('--audio', type=Path, help='Consented 16-bit PCM WAV, up to 60 seconds; no microphone')
    inputs.add_argument('--microphone', action='store_true', help='Opt in to recording yourself/consenting people')
    parser.add_argument('--chunks', type=int, default=3)
    parser.add_argument('--seconds', type=float, default=5)
    parser.add_argument('--out', type=Path, help='New .txt path; a .json settings file is also saved')
    parser.add_argument('--check', action='store_true', help='Offline dependency/cache preflight; never opens the microphone')
    parser.add_argument('--offline', action='store_true', help='Require already cached model files')
    parser.add_argument('--model', help='Local CTranslate2 model directory; defaults to local base.en conversion or Hub base.en')
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    args = parser.parse_args(argv)
    if args.check:
        ready = (common.preflight('whisper', args.microphone, model_path=args.model)
                 if args.model else common.preflight('whisper', args.microphone))
        return 0 if ready else 1
    if args.audio is None and not args.microphone:
        parser.error('Choose --audio FILE or explicitly opt in with --microphone.')
    try:
        frames = capture_frames(args.chunks, args.seconds)
        duration = validate_wav(args.audio) if args.audio else args.chunks * frames / RATE
        path = args.out or common.OUTPUT / ('microphone.txt' if args.microphone else 'transcript.txt')
        common.check_output(path, '.txt')
        common.require_dependencies('whisper', args.microphone)
        compute_type = common.whisper_compute_type(args.model or common.whisper_model(), args.device)
        print(f'Loading {args.model or common.whisper_model()} on {args.device} ({compute_type}). '
              'First run may download weights; --offline forbids that.', flush=True)
        model = (load_model(args.offline, args.model, args.device)
                 if args.model or args.device != 'cpu' else load_model(args.offline))
        if args.microphone:
            lines = microphone_lines(model, args.chunks, args.seconds)
        else:
            lines = [transcribe_audio(model, str(args.audio)) or '[no speech detected]']
            print(lines[0])
        settings = {'model':args.model or common.whisper_model(), 'language':'en', 'device':args.device, 'compute_type':compute_type,
                    'source':'microphone' if args.microphone else str(args.audio), 'duration_seconds':duration,
                    'chunks':args.chunks if args.microphone else None, 'capture_rate_hz':RATE if args.microphone else None,
                    'versions':common.versions('whisper', args.microphone)}
        common.save_outputs(path, ('\n'.join(lines) + '\n').encode('utf-8'), settings)
        print(f'Saved {path} and {path.with_suffix(".json")}. Microphone audio is not saved.')
        return 0
    except KeyboardInterrupt:
        print('\nStopped. No transcript files saved; already printed text remains in this terminal.')
        return 130
    except (OSError, ValueError, RuntimeError, ImportError) as error:
        print(f'Cannot transcribe: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
