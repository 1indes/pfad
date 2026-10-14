# Optional local speech examples

For the **browser voice bot**, follow [CONVERSATION.md](CONVERSATION.md):
faster-whisper `base.en`, LM Studio (MiniCPM5 on the prepared laptop), and Kokoro
ONNX. The Start/Stop mic control stays beside the chat input. Recognition fills
that box while you speak; Enter sends the edited message and stops the mic before
the reply. Logs are in a collapsible sidebar panel. CPU is the portable default
for Windows, Macs and AMD laptops; NVIDIA CUDA is optional. TensorRT stays an
optional experiment. The older Ollama
reply option is retained but needs its own running server and `qwen3:4b` model.

The rest of this page describes the original **console exercises**, including
PyTorch Kokoro. Their `requirements.txt` is heavier than the browser bot's
`conversation_requirements.txt`. They can share this separate Python 3.12
environment if both requirement sets are installed; neither belongs in the root
Week 4 environment. Actual verification and remaining resources are listed in
the [environment report](../ENVIRONMENT.md).

**Kokoro: text → WAV. Whisper: WAV or microphone → text.** These are short,
English-language CPU examples for Week 6. No API key, server or paid service is
needed. This is inference with pretrained models; we are not training a voice.

## 1. Prepare a separate environment

From the `pfad` repository root, with a recent `uv`, enter `week06/speech`.
Create `.venv` once; skip `uv venv` if it is already prepared.
Windows PowerShell:

```powershell
cd week06/speech
uv venv --no-project --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe --torch-backend cpu -r requirements.txt
```

macOS/Linux:

```bash
cd week06/speech
uv venv --no-project --python 3.12 .venv
uv pip install --python .venv/bin/python --torch-backend cpu -r requirements.txt
```

The commands below use `uv run --no-project --python .venv/bin/python` for
macOS/Linux. On Windows, replace `.venv/bin/python` with
`.venv/Scripts/python.exe`. No environment activation is required. For example:

```powershell
uv run --no-project --python .venv/Scripts/python.exe synthesise.py --check
```

Run all remaining commands from `week06/speech`. Use `--no-project` every time:
the root `pyproject.toml` belongs to the Week 4 Python 3.13 Worker. Kokoro 0.9.4
requires Python below 3.13. The separate `.venv` keeps speech dependencies out
of that project and the rest of the course. `--torch-backend` is an install
option, not a `uv run` option.
CPU works on Windows and macOS. Optional NVIDIA speech acceleration is covered
in [the ONNX guide](CONVERSATION.md#optional-nvidia-acceleration); macOS speech
remains CPU while LM Studio can use Metal independently.

The installation includes PyTorch, Misaki and spaCy's English language resource
from its [official release](https://github.com/explosion/spacy-models/releases/tag/en_core_web_sm-3.8.0).
The scripts check for that resource before creating Kokoro's pipeline, preventing
an unexpected language-package installation during synthesis. Top-level speech
packages are pinned; this is **not a fully resolved, inference-tested lockfile**.

Kokoro's pronunciation fallback needs **eSpeak NG**. An installed
`espeakng-loader` bundle supplies the library/data on supported platforms, and
the preflight recognizes it. If that bundle is unavailable, install eSpeak NG:

- Ubuntu/Debian: `sudo apt-get install espeak-ng`
- macOS with Homebrew: `brew install espeak-ng`
- Windows: use the [official phonemizer installation instructions](https://bootphon.github.io/phonemizer/install.html),
  including the eSpeak NG library setting if required. The scripts accept
  `PHONEMIZER_ESPEAK_LIBRARY` when `espeak-ng` is not on `PATH`.

Only the microphone example needs PortAudio and an input device. The sounddevice
wheels bundle PortAudio on Windows/macOS; Linux may need
`sudo apt-get install libportaudio2`. See the [sounddevice installation guide](https://python-sounddevice.readthedocs.io/en/0.5.3/installation.html).
Use a local terminal: a remote server's microphone is not your browser's microphone.

## 2. Check before class

```bash
uv run --no-project --python .venv/bin/python synthesise.py --help
uv run --no-project --python .venv/bin/python transcribe.py --help
uv run --no-project --python .venv/bin/python synthesise.py --check
uv run --no-project --python .venv/bin/python transcribe.py --check
uv run --no-project --python .venv/bin/python transcribe.py --check --microphone
```

Help, imports and `--check` never load a model, download files, infer speech or
open an audio device. Preflight reads package metadata and checks expected files
in the local Hugging Face `main` cache snapshot. It respects `HF_HUB_CACHE`,
`HUGGINGFACE_HUB_CACHE` and `HF_HOME`. Exit code 1 and `MISSING` are expected on a
fresh setup before weights have been downloaded. File presence is not a model
integrity, library compatibility, pronunciation or microphone test.

The **first actual synthesis/transcription** below can download public weights
from Hugging Face and take much longer than later runs. Allow time and disk space
for packages, model caches and language data; do a short rehearsal before class.
No exact laptop speed is promised. Cache filenames are inspected, but model
revisions and transitive dependencies are not fully pinned. Save the settings
JSON when comparing results, and retain the prepared environment for class.

## 3. Text → sound with Kokoro

```bash
uv run --no-project --python .venv/bin/python synthesise.py
```

This saves `week06/out/kokoro.wav` and `week06/out/kokoro.json`. Open the WAV in an
audio player; the script never autoplays. The default sentence uses the preset
American-English voice `af_heart` at speed `1.0`. The waveform is mono, 24,000
samples per second, saved as 16-bit PCM. All generated chunks are joined in order.
The JSON records the text, voice, speed, sample rate, duration and package versions.

Predict what will change when you alter only the speed, then try:

```bash
uv run --no-project --python .venv/bin/python synthesise.py --speed 0.85 --out ../out/kokoro-slow.wav
```

Listen to both files. Is the slower version easier to follow? Does its delivery
still fit a short interface cue? Keep the sentence and voice fixed so the change
is meaningful. Next, try a short sentence of your own with a new output name:

```bash
uv run --no-project --python .venv/bin/python synthesise.py --text "Your drawing has been saved." --out ../out/drawing-saved.wav
```

Text is limited to 500 characters, speed to 0.5–2.0, and saved audio to 60 seconds.
Synthesis can still take longer than the audio's duration. `Ctrl+C` stops the
script and leaves no new output bundle. Existing WAV/JSON files are never
overwritten; choose another `--out` filename for each experiment.

## 4. Sound → text with faster-whisper

Feed the synthetic result back into a recognition model:

```bash
uv run --no-project --python .venv/bin/python transcribe.py --audio ../out/kokoro.wav
```

The text appears in the terminal and is saved in `week06/out/transcript.txt`,
with `transcript.json` settings. Compare it against the original sentence.
Recognition and synthesis are different tasks; one does not perfectly undo the
other. Names, numbers, accents, quiet speech and background sound can cause errors.
Never treat a guessed transcript as an authoritative record.

You can substitute a consented recording: use an uncompressed **16-bit PCM WAV**,
mono or stereo, 8–192 kHz, no more than 60 seconds. File input is decoded,
downmixed and resampled by faster-whisper. This deliberately narrow file exercise
avoids format confusion; the underlying library supports more formats. Choose a
new `--out ../out/another-transcript.txt` to preserve the first result.

The demo uses `base.en`, CPU, English, a one-beam decode and voice activity
detection. Silence may yield no text, but the detector is not a guarantee against
hallucinated words. We consume the segment generator: simply calling
`model.transcribe(...)` does not finish transcription.

If `../out/models/faster-whisper-base.en` is prepared, the scripts reuse it instead
of downloading another model. CPU uses float32 for local model directories
because int8 on the converted float16 checkpoint repeated punctuation in this
environment; the standard Hub `base.en` identifier uses int8. `--model DIRECTORY`
selects another local CTranslate2 model. `--device cuda` opts into NVIDIA float16
inference; see the optional runtime setup in [CONVERSATION.md](CONVERSATION.md).

## 5. Opt in to a finite near-live transcript

Only record yourself or people who have agreed to this recording and its use.
Check your OS microphone permission, then deliberately opt in:

```bash
uv run --no-project --python .venv/bin/python transcribe.py --microphone --chunks 3 --seconds 5
```

This records **15 seconds continuously** at 16 kHz, mono, float32, then ends audio
capture automatically. A callback copies each five-second chunk into a bounded
queue while the main loop transcribes. Recording continues during inference;
text arrives chunk by chunk and can lag on slower computers. The queue can hold
all requested audio, never more than 60 seconds. Waiting for a failed microphone
also has a timeout. No microphone audio file is saved; transcript text and settings
are saved as `week06/out/microphone.txt` and `microphone.json` after completion.

**Stop at any time with Ctrl+C** in the terminal. The input stream closes; an
unfinished transcript is not saved. Already displayed words remain in terminal
history. The finite recording limit concerns captured audio, not model download
or inference time. The microphone is opened only after the model is loaded.

This is **chunked near-live recognition, not native streaming or a production
caption system**. Chunk boundaries may cut words and there is no overlap repair,
speaker identification or correction of previous chunks. Timestamps indicate
captured intervals, not word alignment. Errors and dropped input are reported
rather than silently described as complete. Try the same sentence with different
chunk lengths, preserving each transcript: does shorter chunking actually feel
more useful, and what happened to words at the boundary?

The limits are 1–12 chunks, 1–15 seconds per chunk, at most 60 seconds total.
If 16 kHz capture is unsupported or OS access is denied, use `--audio`; do not
merely change the array's declared rate. List available devices separately with:

```bash
uv run --no-project --python .venv/bin/python python -m sounddevice
```

## Offline use, privacy and recovery

After a successful warm-up of each model, add `--offline` to prevent Hugging Face
and Transformers downloads. Missing resources then fail; `--offline` does not
create them. First-time package installation and online warm-up require internet.
The scripts have no audio/text upload or hosted inference call. Package/model
requests still reveal ordinary connection information to download providers.

Outputs are local. JSON includes the text supplied to synthesis or the source
filename for transcription; transcripts may contain personal information.
Default output folders and local recordings are ignored by git, which is not an
access-control mechanism. Review any files before committing or sharing them.
Custom relative `--out` paths are relative to your terminal's current directory;
default paths always resolve to `week06/out`, independent of that directory.

Use preset synthetic voices and label synthetic speech when sharing it. Do not
imitate someone or use reference recordings without their explicit consent.
Stop if a device reports overflow; retry with less contention or use the WAV
fallback. A passing `--check` does not prove OS permissions or hardware work.

## Other TTS choices to explore later

Keep Kokoro for the shared exercise. These are alternatives by purpose, not a
universal quality ranking, and none is installed or tested by this lesson:

- **[Piper](https://github.com/OHF-Voice/piper1-gpl):** CPU-oriented local interface
  voices, with separate ONNX voice models. The current engine is GPL-3.0-or-later;
  individual voice model cards have their own terms. Older MIT-engine tutorials
  do not describe the current codebase.
- **[Chatterbox](https://github.com/resemble-ai/chatterbox):** expressive dialogue
  and consented voice references. Upstream includes newer model variants than
  the published `chatterbox-tts` 0.1.7 documentation; verify the chosen API and
  checkpoint before a demo. Larger models need more preparation and resources.
- **[Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS):** multilingual voice design
  and delivery controls. Choose the actual checkpoint: VoiceDesign, CustomVoice
  and Base have different capabilities. Downloads are substantially larger than
  Kokoro; do not assume classroom-speed CPU inference.
- **[KittenTTS](https://github.com/KittenML/KittenTTS):** distinguish legacy
  `kittentts` 0.8.1 / [mini-0.8](https://huggingface.co/KittenML/kitten-tts-mini-0.8)
  from the newer `kittenml` / [KittenTTS 2](https://huggingface.co/KittenML/kitten-tts-2).
  They have different APIs, sizes and weight licenses. The old nano size claim
  is not a description of KittenTTS 2. No Kitten installation is required here.

Compare the same sentence for pronunciation, controllability, delay and resource
use. Always check both the software license and the selected model's terms;
a hosted service is a separate product with separate privacy/usage conditions.

## Verification and sources

Run the offline suite from the repo root, with ordinary Python 3.12 and no speech
packages installed:

```bash
uv run --no-project --python 3.12 week06/speech/test_speech.py
```

Tests cover input limits, WAV metadata, sample rates, chunk ordering and bounded
capture, cancellation/device failure/timeout cleanup, lazy results, preserving
all synthesis chunks, output safety, cache inspection, and import/help/preflight
without site packages. Model/device boundaries use small fakes, not real weights
or a microphone. CI runs these offline checks only.

**Status, 14 October 2026:** Offline tests pass. Actual Kokoro **ONNX** synthesis
and faster-whisper file recognition work on CPU and CUDA using prepared local
weights. Chromium checks exercise synthetic microphone input, capture beyond
12 seconds, STOP, editable text, actual LM Studio/MiniCPM replies and generated
audio. Original **PyTorch** Kokoro weights are still missing here, so that
original synthesis path was not exercised with real weights. Physical mic and
speaker performance, cross-platform installation and long-session stability
still need rehearsal. See [ENVIRONMENT.md](../ENVIRONMENT.md) for details and
short-test timings; these do not establish classroom accuracy or latency.

Sources checked 13 October 2026:
[faster-whisper 1.2.1](https://github.com/SYSTRAN/faster-whisper/tree/v1.2.1),
[Whisper](https://github.com/openai/whisper),
[Kokoro 0.9.4](https://pypi.org/project/kokoro/0.9.4/),
[Kokoro-82M model card](https://huggingface.co/hexgrad/Kokoro-82M),
[sounddevice 0.5.3](https://python-sounddevice.readthedocs.io/en/0.5.3/).
Whisper code/weights use MIT; Kokoro-82M weights use Apache-2.0. These labels do
not replace reading a chosen model's card and dependency licenses.
