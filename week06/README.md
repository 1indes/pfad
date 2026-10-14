# Week 6 — sound, music and speech

This week connects numbers to things you can hear: samples make a waveform,
frequency changes pitch, and combinations of waves change timbre. Speech models
then connect sound and text in both directions.

Start from the `pfad` repository root on branch `2026`, and pull the latest
material. Use [the uv reference](../reference/uv.md) if `uv` is not installed.
First-time dependency installation needs internet.

| Path | What you will do | Setup |
| --- | --- | --- |
| [Local sound](#start-with-sound-you-can-change) | Save noise and a sine tone; change one value and listen | `uv run`; no API key, GPU or model downloads |
| [Song API preview](#preview-a-song-request) | Inspect and change a music-generation request | Preview needs no key; live generation is an optional instructor demo |
| [Browser sound](#play-with-sound-in-the-browser) | Play notes, compare harmonics, visualize a voice | Browser, localhost server and internet for p5.js |
| [Local speech](#optional-speech-path) | Synthesize speech, recognize words, try a voice chatbot | Separate Python 3.12 environment and prepared local models |

Work through local sound and the browser sketches first. The song preview is
available to everyone; live API calls and the local speech setup are optional.
The sound and API `uv run` commands work unchanged in Windows PowerShell and
macOS/Linux terminals. The speech guide gives separate commands where interpreter
paths and environment-variable syntax differ.

## Start with sound you can change

The [sound folder](sound/) contains the complete Python files used on the slides.
The local noise and tone examples need only the Python standard library.
Like the previous weeks, run them with `uv run` from the **repository root**:

```bash
uv run week06/sound/noise.py
uv run week06/sound/tone.py
```

Each script declares its dependencies, so `uv` prepares the environment without
activating a `.venv` or installing the root Week 4 project. The song example
declares `python-dotenv`; the noise and tone examples declare no extra packages.

Both create two-second, mono, 16-bit PCM files at 22,050 samples per second:
`week06/sound/out/noise.wav` and `week06/sound/out/tone.wav`. Neither plays
automatically. Keep `wav_support.py` beside the scripts. Open each WAV in an
audio player at low speaker volume, then predict and change one value:

- In `tone.py`, change `FREQUENCY` from `220` to `440`. What happens to pitch?
- Change `AMPLITUDE` from `0.08` to `0.04`. Does pitch change, or only loudness?
- In `noise.py`, keep `SEED` fixed and run twice. Then change it. Why does the
  same seed reproduce the same samples?

Rerunning replaces that script's WAV. To keep a comparison in another folder:

```bash
uv run week06/sound/tone.py --out week06/sound/out/comparison
```

`request_song.py` is an **optional instructor API
example**: it previews JSON offline by default; sending a live request requires
separate credentials and can use paid credits.

## Preview a song request

From the repository root, run:

```bash
uv run week06/sound/request_song.py
```

This prints the request JSON without connecting to the server. No API key is
needed. `uv` installs the declared dependency automatically; a plain `python`
offline preview also works without extra packages. Defaults are a song titled
**Studio Break**, a gentle ambient piano-and-strings prompt, and a requested
duration of **30 seconds**. The model
chooses the final length; vocals are allowed unless you add `--instrumental`.

Change the defaults with command-line options:

```bash
uv run week06/sound/request_song.py --prompt "Playful electronic music for a dancing desk lamp" --title "Desk Disco" --duration-seconds 30 --instrumental
uv run week06/sound/request_song.py --help
```

If your terminal is already in `week06/sound`, use `uv run request_song.py`
instead. The script finds the same root `.env` and output folder from either
location.

### Instructor: send a live request

Live generation requires an enabled classroom account and can spend credits.
The default server is `https://easel.ait4x.org`. Images and songs share
**EASEL_KEY** in a single `.env` file at the **repository root**, loaded with
`python-dotenv`. If you do not already have `.env`, create it from the repository
root in PowerShell:

```powershell
Copy-Item .env.example .env
```

On macOS/Linux, use `cp .env.example .env`. If `.env` already exists, edit it
instead of copying over it. Fill in `EASEL_KEY=your-classroom-api-key` in that
file. The real `.env` is ignored by Git; only the empty `.env.example` is shared.
Then, from the repository root:

```bash
uv run week06/sound/request_song.py --instrumental --send
```

`uv run` installs `python-dotenv` using the script's dependency declaration.
No manual installation or `.venv` activation is needed for these `uv run`
commands. If you prefer plain `python`, install `python-dotenv` in that Python
environment first. Offline previews still need no extra packages.

Both scripts find the root `.env` regardless of the current directory and leave
existing environment variables unchanged. Songs also accept `EASEL_API_KEY`,
which takes precedence over `EASEL_KEY`. To use another song server, set
`EASEL_BASE_URL` in `.env` to its HTTPS root URL, without `/v1`.

The script submits once, polls for completion, and saves all returned songs in
`week06/sound/out/songs/`, regardless of your current directory. Use
`--output-dir PATH` to choose another folder. Open the saved audio to listen;
playback is not automatic.

Run live requests one at a time: the server's latest-attempt status is shared.
If a timeout or CAPTCHA interrupts generation, keep the printed attempt/track
IDs and ask the instructor to inspect the server status and Suno library before
trying again. Repeating `--send` creates another request and may spend credits.

## Play with sound in the browser

The slides embed the same [p5.js sketches](browser/) stored here:

- [Keyboard piano](browser/piano.html) (`piano.js`): click a key or press 1-8.
- [Harmonics](browser/harmonics.html) (`harmonics.js`): adjust the base and
  multiplier; compare the two tones with their sum.
- [Voice surface](browser/voice_surface.html) (`voice_surface.js`): click DEMO
  for synthetic data, or explicitly grant MIC permission to see a flowing 3D
  frequency surface. Nothing is recorded, sent, transcribed or played back.

The standalone HTML uses p5.js 1.11.3 from a CDN. For microphone permission,
serve `week06/browser/` on **localhost** (or use an HTTPS page). From the
repository root:

```bash
uv run --no-project python -m http.server 8000 --directory week06/browser
# open http://localhost:8000/voice_surface.html
```

The same server also serves `http://localhost:8000/piano.html` and
`http://localhost:8000/harmonics.html`. Keep the terminal open while using the
pages; press **Ctrl+C** there when finished.

For the keyboard/harmonics sketches, opening the HTML files locally may work;
localhost is the reliable route. Set speaker volume low. None of the sketches
starts sound or capture on page load. Click Stop or press Escape; leaving a
slide also stops it. If microphone permission fails or you prefer not to speak,
click DEMO. The surface is a visualization, not a speech recognizer.

Try these comparisons:

- Piano: play **1** (C4) and **8** (C5). Compare the displayed frequencies:
  doubling frequency produces an octave.
- Harmonics: start at **220 Hz**, multiplier **2**. Listen to BASE, HARMONIC,
  then TOGETHER, and compare the drawn waves.
- Voice surface: start with DEMO, then optionally use MIC. Compare speaking,
  humming and silence. A frequency pattern is not a transcript of words.

If a page is blank, check the internet connection for the p5.js CDN. If sound
is silent, click inside the sketch, check the tab/device volume and selected
output device, then retry. For microphone errors, use localhost, check browser
permission and the selected input device, or continue with DEMO.

## Optional speech path

Sound is a changing signal. A recording stores samples; a transcription model
turns those samples into a guess at words. A speech-synthesis model goes the
other way, turning text into a waveform.

The recommended [Kokoro ONNX and faster-whisper setup](speech/CONVERSATION.md)
connects these two representations, and then adds a local chat model:

1. **Text → sound:** Kokoro saves a short synthetic voice as a WAV.
2. **Sound → text:** faster-whisper transcribes that WAV locally.
3. **Microphone → near-live text:** explicitly opt in to a finite recording,
   processed in chunks. A file-based alternative works without a microphone.
4. **Local browser voice bot:** [faster-whisper + LM Studio + Kokoro ONNX](speech/CONVERSATION.md),
   with Start/Stop capture, an editable transcript and spoken replies. CPU is
   the portable default; NVIDIA CUDA and TensorRT experiments are optional.

Follow the guide's [text-to-sound-to-text exercise](speech/CONVERSATION.md#try-text-to-sound-and-back)
before trying the microphone. Then follow its LM Studio and browser steps for
the chatbot. The original, heavier [PyTorch Kokoro console exercises](speech/README.md)
are a separate option; their model files differ from Kokoro ONNX's.
These are lesson examples and optional practice, not a new assignment or
assessed quiz.

The speech tools have a **separate Python 3.12 environment**. They are not needed
for other weeks, the Week 4 Worker, or the rest of the sound lesson. Setup and first
use download substantial libraries and model files, so prepare before class.

| Machine | Speech models | LM Studio chat model |
| --- | --- | --- |
| Windows without NVIDIA, including AMD | CPU | CPU or a supported Vulkan backend |
| macOS, including Apple silicon | CPU | Metal on supported Macs |
| Windows with NVIDIA | CPU first; optional CUDA setup in the guide | CUDA when supported |

The speech pipeline has no Metal/MPS or ROCm backend. LM Studio manages its own
acceleration separately. The [speech guide](speech/CONVERSATION.md) uses
`uv venv`, `uv pip install` and `uv run` for both Windows and macOS; NVIDIA CUDA
has its own optional installation and verification steps.

Only use your own or consented recordings. Transcriptions can be wrong, and
synthetic speech should be labelled when shared. See the [setup, limitations,
privacy notes and verification status](speech/README.md).

## Check the examples

From the repository root:

```bash
uv run --no-project --python 3.12 week06/test_resources.py
uv run --no-project --python 3.12 week06/speech/test_speech.py
uv run --no-project --python 3.12 week06/speech/test_local_reply.py
node week06/browser/test_sketches.cjs
```

The Python checks need no speech packages, models, API key or microphone.
The browser source checks need Node.js; they do not play audio or open a mic.
These checks cannot replace listening, a real microphone rehearsal, or testing
your own machine's model/runtime setup. No live API request is made.

See the [14 October environment check](ENVIRONMENT.md) for verified examples,
models reused on disk, missing optional resources and this laptop's GPU limits.
