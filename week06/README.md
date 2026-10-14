# Week 6 — sound, music and speech

## Start with sound you can change

The [sound folder](sound/) contains the complete Python files used on the slides.
They need only the Python standard library. From the PFAD checkout:

```bash
cd week06/sound
python noise.py
python tone.py
```

Both create two-second, mono PCM files in `out/`; neither plays automatically.
Keep `wav_support.py` beside them. Open a file at low speaker volume and change
one value in the source. `request_song.py` is an **optional instructor API
example**: it previews JSON offline by default; sending a live request requires
separate credentials and can use paid credits.

## Play with sound in the browser

The slides embed the same [p5.js sketches](browser/) stored here:

- [Keyboard piano](browser/piano.html) (`piano.js`): click a key or press A–K.
- [Harmonics](browser/harmonics.html) (`harmonics.js`): adjust the base and
  multiplier; compare the two tones with their sum.
- [Voice surface](browser/voice_surface.html) (`voice_surface.js`): click DEMO
  for synthetic data, or explicitly grant MIC permission to see a flowing 3D
  frequency surface. Nothing is recorded, sent, transcribed or played back.

The standalone HTML uses p5.js 1.11.3 from a CDN. For microphone permission,
serve `week06/browser/` on **localhost** (or use an HTTPS page):

```bash
cd week06/browser
python -m http.server 8000
# open http://localhost:8000/voice_surface.html
```

For the keyboard/harmonics sketches, opening the HTML files locally may work;
localhost is the reliable route. Set speaker volume low. None of the sketches
starts sound or capture on page load. Click Stop or press Escape; leaving a
slide also stops it. If microphone permission fails or you prefer not to speak,
click DEMO. The surface is a visualization, not a speech recognizer.

## Optional speech path

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
