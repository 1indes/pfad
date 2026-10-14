"""Smoke check the files students are asked to run from this week's folder."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import wave

WEEK = Path(__file__).resolve().parent


class Week06Resources(unittest.TestCase):
    def test_sound_scripts_make_small_pcm_files(self):
        for script in ('noise.py', 'tone.py'):
            with self.subTest(script=script), tempfile.TemporaryDirectory() as temp:
                out = Path(temp) / script.replace('.py', '.wav')
                subprocess.run([sys.executable, script, '--out', temp],
                               cwd=WEEK / 'sound', check=True, capture_output=True, text=True)
                with wave.open(str(out)) as wav:
                    self.assertEqual((wav.getnchannels(), wav.getsampwidth(),
                                      wav.getframerate(), wav.getnframes()),
                                     (1, 2, 22050, 44100))

    def test_browser_sketches_and_speech_app_are_in_pfad(self):
        for path in ('browser/piano.js', 'browser/harmonics.js',
                     'browser/voice_surface.js', 'speech/speech_webrtc.py',
                     'speech/speech_webrtc_requirements.txt', 'sound/request_song.py'):
            with self.subTest(path=path):
                self.assertTrue((WEEK / path).is_file(), path)


if __name__ == '__main__':
    unittest.main()
