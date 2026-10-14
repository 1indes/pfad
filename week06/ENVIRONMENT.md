# Week 6 environment check

Checked **14 October 2026** on the instructor's Windows laptop. This records
what was exercised locally; it is not a guarantee for every student's machine.

## Examples

| Example | Result here | Missing or still to check |
| --- | --- | --- |
| `sound/noise.py`, `sound/tone.py` | Tests create valid 2-second PCM WAVs; standard library only | Listen at low volume on the classroom speakers |
| `sound/request_song.py` | Offline JSON preview works; instructor's live run completed and saved two M4A tracks | An enabled classroom API key (`EASEL_KEY` or `EASEL_API_KEY`) is needed; actual listening still to check |
| Browser piano | JS checks and Chromium rendering/control checks pass | Actual speaker listening; keys are **1-8** |
| Browser harmonics | JS checks and Chromium rendering/control checks pass | Actual speaker listening |
| Browser voice surface | Chromium synthetic demo, fake mic, denial handling, STOP/track cleanup pass | Physical microphone rehearsal; p5 CDN is needed at first page load |
| Original `speech/synthesise.py` | Offline boundary tests pass; installed packages/eSpeak detected | Original PyTorch Kokoro model/config/`af_heart.pt` are absent, so actual PyTorch synthesis was not run |
| `speech/synthesise_onnx.py` | Actual CPU and CUDA synthesis creates valid WAVs using local files | Physical speaker listening; ONNX assets are distinct from PyTorch weights |
| `speech/transcribe.py --audio` | Actual CUDA float16 and CPU float32 recognition pass on synthetic English WAVs | CPU int8 on the converted checkpoint repeated punctuation; local directories now use float32 |
| Console `--microphone` | Device enumeration and mocked capture/cleanup tests pass | Physical capture not exercised by the automated checks; default input is an NDI virtual device |
| `speech/speech_webrtc.py` | Typed prompt and fake browser mic -> Whisper -> editable text -> actual MiniCPM5 -> actual Kokoro audio pass | Real-device quality, browser audible playback and long-session stability need rehearsal |

The browser bot now continues capture until STOP, rather than ending recognition
after three chunks. The console microphone exercise remains finite by design.
The chatbot's mic control shares the bottom composer, speech fills its editable
draft, Enter sends, and sending stops capture. Logs and advanced setup are
collapsible sidebar sections. Pip's personality prompt requests playful replies
of a few sentences. MiniCPM5 receives its documented no-thinking assistant prefill
to prevent reasoning from consuming the answer's token budget.
The bot defaults to CPU speech and offers NVIDIA CUDA separately. It does not
install TensorRT, WhisperLive or FireRedASR.

## Environment and cached models

- Separate `week06/speech/.venv`: Python 3.12.10. The root Python 3.13 environment
  belongs to Week 4 and cannot substitute for the original Kokoro exercise.
- RTX 3060 Laptop GPU: 6144 MiB; NVIDIA driver 616.92. The advertised driver
  CUDA capability is 13.4; the installed toolkit is 13.3.
- Existing OpenAI Whisper checkpoints: `base.en.pt`, `base.pt`, `tiny.en.pt`,
  `small.pt`, `large-v3.pt` under the user's `.cache/whisper`.
- Reused `base.en.pt` (~138.5 MiB), converting its weights once into
  `week06/out/models/faster-whisper-base.en`. No Whisper weight download was
  needed. Small public tokenizer/vocabulary/config resources were fetched.
- An existing faster-distil-whisper-large-v3 Hub cache (~1.5 GB) was found and
  left unused; base.en is the smaller English default.
- Existing MiniCPM5-2B Q4_K_M (~1.45 GiB) was reused from the LM Studio model
  directory. LM Studio is serving locally on port 1234, identifier `minicpm5-2b`,
  context 2048 and parallelism 1. No Gemma download is needed for this demo.
- Kokoro ONNX was absent, so only the missing official ONNX model (~310.5 MiB)
  and voices (~26.9 MiB) were downloaded into `week06/out/models/kokoro-onnx`.
  Subsequent preparation reused them after validation.
- `espeakng-loader` supplies Windows pronunciation library/data. A separate
  eSpeak executable is not required when that bundle is present.
- Existing LM Studio CUDA 12 cuBLAS and global Python CUDA 13/cuDNN 9 libraries
  were reused. CTranslate2 and ONNX Runtime GPU need different CUDA generations
  in the tested versions. The launcher does not install a toolkit.
- Global `HF_HOME` points to `D:\hub`, which does not exist. The browser launcher
  sets its own process-local cache and offline flags; global settings were not
  changed. The converted model and ONNX assets have explicit local paths.
- Ollama is installed but was not running; `qwen3:4b`, used by the older optional
  Ollama branch, is absent. LM Studio/MiniCPM is the verified reply path.

The prepared instructor environment contains both original console and browser
dependencies, including CPU PyTorch. Both CPU and GPU ONNX Runtime distributions
were present during the checks, and the active module exposed working CUDA.
For a clean student installation, install one ONNX Runtime distribution using
the [bot guide](speech/CONVERSATION.md). Portable dependencies omit PyTorch;
fresh macOS/AMD/Linux installations have not been tested on this Windows laptop.

## Resource measurements

In a separate short, warm GPU speech check, both speech models together used
about 815 MiB total GPU memory. For 2.35 seconds of synthetic audio, Kokoro took
roughly 0.17-0.29 seconds and Whisper took 0.14-0.20 seconds. These are small
synthetic checks, not a general benchmark or a full conversation latency.

The full browser application with MiniCPM and both CUDA speech models initially
showed **5864-5870 MiB total GPU use out of 6144 MiB**. Longer paragraph synthesis
could exceed Kokoro's 1 GiB memory arena. The final bot splits replies at sentence
boundaries into pieces of at most 140 characters and joins all generated audio;
its final full-stack snapshot was **5424 MiB out of 6144 MiB**. This includes other
GPU processes, does not isolate each model, and is not a sampled peak. The full
stack completed the checked turns, with finite remaining VRAM. Kokoro's
CUDA memory arena/workspace settings are bounded where the provider supports
them; they do not cap total process or GPU memory. Choose CPU speech if needed,
keep LM Studio context/parallelism modest, and restart after model/device changes
if cached resources build up.

## Verification evidence

From the repository root:

```text
python week06/test_resources.py             # 2 passing tests
python week06/speech/test_speech.py         # 28 passing tests
python week06/speech/test_local_reply.py    # 7 passing tests
node week06/browser/test_sketches.cjs       # passes
```

Offline tests use fakes for model/device boundaries. Separate local Chromium
checks exercised browser sketches and the conversation app against actual LM
Studio and speech weights. The conversation check captured beyond 12 seconds,
checked recognized words in the live chat input, edited and sent a second turn
with Enter while capturing, and verified that all tracked mic streams ended.
Both replies have audio players; the second player's playback was checked using
`paused == false` and advancing `currentTime`. Desktop/mobile renders and the
pinned mic control at a shorter desktop height were checked. Its microphone source
was a synthetic WAV. Source parsing,
CLI help/preflight and actual CPU/CUDA file inference were also checked.
Screenshots, WAVs and local browser harnesses are kept under ignored `week06/out`.

## Remaining preparation

Use the ONNX bot for the prepared demo. If teaching the original PyTorch
`synthesise.py` specifically, run `prepare_models.py --backend both` with the
original requirements installed to obtain its separate missing weights. This
requires another model download; it was avoided because those weights are not
used by the ONNX bot.

Select the physical microphone, rehearse speech and playback, and check browser
permission/autoplay before class. API credentials are needed only for optional
live `request_song.py`. TensorRT, WhisperLive and FireRedASR remain optional
research paths, documented in [CONVERSATION.md](speech/CONVERSATION.md).
