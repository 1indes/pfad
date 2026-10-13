# Week 6 — sound and speech

Sound is a changing signal. A recording stores samples; a transcription model
turns those samples into a guess at words. A speech-synthesis model goes the
other way, turning text into a waveform.

The optional [Python speech examples](speech/README.md) connect these two
representations:

1. **Text → sound:** Kokoro saves a short synthetic voice as a WAV.
2. **Sound → text:** faster-whisper transcribes that WAV locally.
3. **Microphone → near-live text:** explicitly opt in to a finite recording,
   processed in chunks. A file-based alternative works without a microphone.

Start with the first two. Change one speech-speed value and listen to the result
before trying the microphone. These are lesson examples and optional practice,
not a new assignment or assessed quiz.

The speech tools have a **separate Python 3.12 environment**. They are not needed
for other weeks, the Week 4 Worker, or the rest of the sound lesson. Setup and first
use download substantial libraries and model files, so prepare before class.

Only use your own or consented recordings. Transcriptions can be wrong, and
synthetic speech should be labelled when shared. See the [setup, limitations,
privacy notes and verification status](speech/README.md).
