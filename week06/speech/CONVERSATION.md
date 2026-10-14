# Local browser voice bot

Chat with **Pip**, a playful local studio companion. Type a message or speak in
English; recognized words appear in the chat input. Edit them and press **Enter**
to send. Sending stops the microphone before Kokoro ONNX speaks the reply.
The default is **CPU** speech processing, using faster-whisper `base.en` and
Kokoro ONNX. NVIDIA CUDA is optional; TensorRT is an optional later experiment.

## Choose the portable setup first

Run these commands from `week06/speech`. Keep this Python 3.12 environment
separate from the repository's Week 4 Python 3.13 project.
From the repository root, first run `cd week06/speech`.
Create `.venv` once; skip `uv venv` if you already prepared it. No activation
is required: every speech command selects this interpreter explicitly.

Windows PowerShell:

```powershell
uv venv --no-project --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r conversation_requirements.txt
uv run --no-project --python .venv/Scripts/python.exe prepare_models.py
uv run --no-project --python .venv/Scripts/python.exe synthesise_onnx.py --check
uv run --no-project --python .venv/Scripts/python.exe transcribe.py --check
```

macOS or Linux:

```bash
uv venv --no-project --python 3.12 .venv
uv pip install --python .venv/bin/python -r conversation_requirements.txt
uv run --no-project --python .venv/bin/python prepare_models.py
uv run --no-project --python .venv/bin/python synthesise_onnx.py --check
uv run --no-project --python .venv/bin/python transcribe.py --check
```

Installation and preparation need internet. The runtime uses prepared local
files only. The portable bot needs no PyTorch, spaCy, PortAudio or TensorRT:
browser WebRTC supplies microphone audio, and Kokoro ONNX bundles eSpeak NG via
`espeakng-loader`. The older console exercises have their own dependencies in
[README.md](README.md). These requirement files are not complete dependency
lockfiles. Windows CPU/CUDA was exercised here; macOS and Linux installations
still need a rehearsal on those systems.

### Reuse model files

`prepare_models.py` first reuses `../out/models/faster-whisper-base.en` if complete.
If absent, it can convert an existing `~/.cache/whisper/base.en.pt`; this optional
conversion requires PyTorch and Transformers from the original `requirements.txt`.
It reuses the large checkpoint and downloads only the small tokenizer/config files.
Without that checkpoint it prepares the standard Systran `base.en` model.
Use `--cache-dir` for an existing Hugging Face cache; missing files are downloaded.

Kokoro's two ONNX assets are stored in `../out/models/kokoro-onnx`. Preparation
checks sizes and available release SHA256 digests and reuses existing files.
It contacts the release API to check those assets but does not download weights
again when they are valid. `--backend torch` or `both` also prepares the separate
PyTorch Kokoro weights; the browser bot does not need them.

Use `--whisper-checkpoint`, `--whisper-out` and `--onnx-out` for preparation at
other paths. The browser expects the default output paths, so put prepared models
there for this example. The console recognizer accepts `--model DIRECTORY`.
Models and generated outputs under `week06/out` are ignored by git.

## Try text to sound and back

After preparing the portable environment and models, try both directions before
adding a microphone or chat server. From `week06/speech` on Windows:

```powershell
uv run --no-project --python .venv/Scripts/python.exe synthesise_onnx.py --text "Your drawing has been saved." --out ../out/onnx-hello.wav
uv run --no-project --python .venv/Scripts/python.exe transcribe.py --audio ../out/onnx-hello.wav --offline --out ../out/onnx-hello.txt
```

macOS/Linux, from the same folder:

```bash
uv run --no-project --python .venv/bin/python synthesise_onnx.py --text "Your drawing has been saved." --out ../out/onnx-hello.wav
uv run --no-project --python .venv/bin/python transcribe.py --audio ../out/onnx-hello.wav --offline --out ../out/onnx-hello.txt
```

These commands reuse the prepared environment and models; no LM Studio server
or API key is needed.
Open `../out/onnx-hello.wav` in an audio player and compare the transcript with
the supplied sentence. Try another synthesis with `--speed 0.85` and a new
`--out` filename. Speech outputs are not overwritten; use a new output name for
each run. JSON files alongside the results record the settings.

## Load a small model in LM Studio

Install LM Studio and load an instruction/chat model suitable for your computer.
This laptop uses its existing **MiniCPM5-2B Q4_K_M** (~1.45 GiB on disk), without
another language-model download. Start LM Studio's local server on port 1234.
If `lms` is on your PATH, the tested settings are:

```text
lms server start --port 1234
lms load minicpm5-2b --context-length 2048 --parallel 1 --identifier minicpm5-2b --yes
```

LM Studio controls its own acceleration: Metal on supported Macs, CUDA on NVIDIA,
or a supported CPU/Vulkan backend where available. This is separate from the
browser's speech-processing selection. Use the actual identifier of your loaded
model. No LM Studio model download or load happens automatically on page load.
For the NVIDIA instructor setup, append `--gpu max` to the load command.

## Run and talk

Windows, from `week06/speech`:

```powershell
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
uv run --no-project --python .venv/Scripts/python.exe python -m streamlit run speech_webrtc.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

macOS/Linux, from `week06/speech`:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --no-project --python .venv/bin/python python -m streamlit run speech_webrtc.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

The existing Windows `./run_conversation.ps1` launcher is also available; it
selects the same `.venv` and prepared cache. Keep the server terminal open and
press **Ctrl+C** there to stop it. Keep LM Studio running in its own application.

Open **http://localhost:8501** on this laptop. In the sidebar, press **Find loaded
models**, and choose the model loaded in LM Studio. MiniCPM is preferred when
present. Type a message in the bottom chat box and press **Enter**, or use
**Start mic** beside that box. The first Start loads the cached speech model and
requests browser microphone permission. The mic control stays beside the input
as the chat grows. CPU is the default; runtime options live under **Advanced
settings**. To select a physical microphone instead of a virtual device, enable
**Show microphone device picker** there and use its **SELECT DEVICE** control.

The browser keeps processing until **Stop mic** or sending, in 3-second chunks.
Words appear in the editable message box during recognition; Enter also works
while the mic is active. For careful editing, press Stop mic first, then edit and
send. The message box holds up to 500 characters. A collapsed **Transcription log**
in the sidebar retains only the latest 20 chunks. The bot keeps at most eight
recent conversation messages.
Reply audio appears with playback controls and requests autoplay once; browser
autoplay settings may require pressing Play. Each assistant message keeps its own
player, so subsequent replies start correctly and earlier audio can be replayed.
Starting the mic or sending another message pauses existing reply audio.
**Clear chat** clears the conversation, draft and logs, and stops capture.
Stop capture before changing speech devices or server settings.

The editable **Assistant personality** prompt introduces Pip as curious, witty,
warm and useful, usually answering in three to five sentences. Replies have a
256-token budget and a 1000-character limit; Kokoro speaks them in phrases of at
most 140 characters to limit GPU activation memory, retaining the full reply,
up to 60 seconds. MiniCPM5's documented empty-thought
assistant prefill disables its reasoning for this voice-chat path. The LM Studio
OpenAI endpoint otherwise ignores `enable_thinking`, and a short token budget can
be exhausted before an answer appears. Other models do not receive that prefill.

Text goes only to the selected loopback server when you send a message. Incoming
microphone audio is processed in memory; no microphone WAV is saved. Replies and
transcripts live in the browser session. Package installation/model preparation
uses external download services. Use your own or consented recordings, check
transcripts, and label synthetic speech when sharing it.

## Optional NVIDIA acceleration

### Windows with NVIDIA

The same app has a **NVIDIA CUDA** speech option. Macs and AMD machines should
keep CPU; this faster-whisper implementation does not offer MPS or ROCm.
LM Studio can still accelerate its language model independently.

On the tested Windows setup, install the GPU ONNX runtime *after* the portable
requirements. Avoid leaving both ONNX Runtime distributions installed because
they provide the same Python module:

```powershell
uv pip uninstall --python .venv/Scripts/python.exe onnxruntime onnxruntime-gpu
uv pip install --python .venv/Scripts/python.exe --no-deps -r conversation_nvidia_requirements.txt
```

This optional file pins ONNX Runtime GPU 1.31.0, tested here with CUDA 13 and
cuDNN 9. CTranslate2 4.8.3 separately needs CUDA 12 cuBLAS and cuDNN 9.
`gpu_runtime.py` locates existing Windows LM Studio CUDA vendor libraries and
global Python PyTorch libraries. It changes the running process's DLL search
path only. If needed, set `SPEECH_CUDA_DLL_DIRS` to library directories separated
by your platform's PATH separator. On another machine, supply compatible CUDA
libraries or keep CPU. Installing a CUDA toolkit alone does not guarantee all
the required runtime libraries are available.

Restart the app after runtime changes and select **NVIDIA CUDA** under Advanced
settings; the next Start mic loads that speech model. CUDA provider failures are
reported; Kokoro does not silently switch the whole session to CPU. Some ONNX
graph operations can still run on CPU.
To return to portable ONNX Runtime, uninstall both distributions and reinstall
`conversation_requirements.txt`.

The console scripts also offer explicit acceleration:

```powershell
uv run --no-project --python .venv/Scripts/python.exe synthesise_onnx.py --device cuda --text "Hello. This is a local voice assistant." --out ../out/my-cuda-voice.wav
uv run --no-project --python .venv/Scripts/python.exe transcribe.py --device cuda --audio ../out/my-cuda-voice.wav --offline --out ../out/my-cuda-transcript.txt
```

Check the NVIDIA driver with `nvidia-smi` and verify Kokoro's active providers:

```powershell
uv run --no-project --python .venv/Scripts/python.exe python -c "from synthesise_onnx import load_voice; load_voice('cuda'); print('Kokoro CUDA session ready')"
```

This opens the local Kokoro model without speaking; it fails if the CUDA
provider cannot initialize. The two console commands exercise actual synthesis
and recognition. `--check` alone only inspects packages/files and does not prove
GPU execution. If CUDA fails, keep CPU speech and leave LM Studio acceleration
enabled independently.

### macOS and other platforms

On macOS, keep the portable CPU ONNX Runtime and CPU speech selection; do not
install `conversation_nvidia_requirements.txt`. Apple silicon can use Metal
for the LM Studio model while Whisper and Kokoro run on CPU. This example does
not offer CUDA on Macs or ROCm speech on AMD GPUs.

For NVIDIA Linux, the same optional ONNX Runtime replacement commands use
`.venv/bin/python`, but supply compatible CUDA/cuDNN libraries using your Linux
installation: `gpu_runtime.py` only discovers Windows DLLs. That installation
path has not been verified here.

Default console speech devices remain CPU. Standard Hub `base.en` uses CPU int8;
local model directories use CPU float32 because the converted float16 checkpoint
produced repeated punctuation with int8 in this environment. CUDA uses float16.

## Findings on the 6 GB laptop

Verified 14 October 2026 on Windows with an RTX 3060 Laptop GPU (6144 MiB):

- Cached MiniCPM5 + CUDA faster-whisper + CUDA Kokoro ONNX complete browser turns.
- Fake microphone capture continues beyond 12 seconds, STOP works, and edited
  text is sent by Enter for a second conversational reply with playable audio.
- CPU Kokoro ONNX synthesis and CPU float32 Whisper transcribe local test audio.
- A short 2.35-second synthetic utterance took roughly 0.17-0.29 seconds for warm
  CUDA Kokoro synthesis and 0.14-0.20 seconds for warm CUDA recognition in a
  separate short check. This excludes LLM generation and browser overhead.
- With phrase-sized synthesis, a final full-stack GPU snapshot was **5424 MiB out
  of 6144 MiB**; earlier configurations showed 5864-5870 MiB. These include
  LM Studio and other GPU processes and are not measured peaks.
  The stack works in these checks, with limited headroom. Keep context at 2048,
  parallelism at 1, replies short, and use CPU speech if memory is tight.

These synthetic checks do not establish real microphone quality, accent accuracy,
audible playback or long-session stability. Rehearse with the physical classroom
mic and speakers. See the complete [environment report](../ENVIRONMENT.md).

## Streaming and TensorRT experiments

The bot processes independent short chunks. It is not native streaming ASR:
boundaries can cut words and Whisper can hallucinate, especially on repeated or
quiet audio. Capture continues until Stop mic or sending; this does not imply
continuous LLM conversation, automatic turn detection or interruption of a spoken
reply.

Keep [faster-whisper](https://github.com/SYSTRAN/faster-whisper) as the shared
default. [WhisperLive](https://github.com/collabora/WhisperLive) is a possible
later streaming layer with partial/committed text and local model paths. Its
dependencies differ from this environment; use another environment, reuse the
prepared base.en directory, and check device detection. Its server currently
checks CUDA through PyTorch, while this bot's GPU recognition works with CPU
PyTorch or no PyTorch at all.

TensorRT Whisper exists, but is not installed or required here. WhisperLive's
[TensorRT guide](https://github.com/collabora/WhisperLive/blob/main/TensorRT_whisper.md)
uses a separate Docker/engine-building path. The older
[PINTO implementation](https://github.com/PINTO0309/whisper-onnx-tensorrt) targets
old CUDA/TensorRT versions and recommends 16 GB VRAM.
[NVIDIA whisper_trt](https://github.com/NVIDIA-AI-IOT/whisper_trt) targets Jetson;
it is not a ready Windows replacement. Benchmark any TensorRT experiment on the
same audio against faster-whisper before adding it to teaching material.

[FireRedASR](https://github.com/FireRedTeam/FireRedASR) and its successor
[FireRedASR2S](https://github.com/FireRedTeam/FireRedASR2S) offer other recognition
models. They are larger and focus on Mandarin/dialects as well as English;
Windows is not a verified deployment target. `2S` denotes a second-generation
system, not streaming ASR. For this English-only exercise, base.en is the simpler
resource fit. None of these optional alternatives was downloaded or installed.
