# /// script
# dependencies = ["Pillow>=11,<13", "numpy>=2,<3", "python-dotenv>=1,<2"]
# ///
"""Run with: uv run week05/test_examples.py"""

import base64
import contextlib
import io
import json
import os
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

HERE = Path(__file__).resolve().parent


class ExampleTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.folder = Path(self.directory.name)

    def copy_script(self, name):
        self.assertTrue((HERE / name).is_file(), f"Missing weekly example: {name}")
        return Path(shutil.copy(HERE / name, self.folder / name))

    def run_script(self, name):
        script = self.copy_script(name)
        subprocess.run([sys.executable, str(script)], cwd=HERE.parent,
                       check=True, capture_output=True, text=True)

    def test_tiny_image_preserves_all_four_pixel_positions(self):
        self.run_script("tiny_image.py")
        with Image.open(self.folder / "out/tiny-image.png") as image:
            self.assertEqual(image.size, (120, 120))
            for point, colour in [((30, 30), (255, 0, 0)),
                                  ((90, 30), (0, 255, 0)),
                                  ((30, 90), (0, 0, 255)),
                                  ((90, 90), (255, 255, 0))]:
                self.assertEqual(image.getpixel(point), colour)

    def test_noise_is_reproducible_and_has_rgb_variation(self):
        self.run_script("noise.py")
        with Image.open(self.folder / "out/noise.png") as image:
            self.assertEqual(image.size, (256, 256))
            self.assertEqual(image.mode, "RGB")
            self.assertGreater(len(image.getcolors(256 * 256)), 1000)
            first = image.tobytes()
        self.run_script("noise.py")
        with Image.open(self.folder / "out/noise.png") as image:
            self.assertEqual(image.tobytes(), first)

    def test_gif_dot_moves_in_order_with_constant_duration(self):
        self.run_script("make_gif.py")
        with Image.open(self.folder / "out/moving-dot.gif") as image:
            self.assertEqual(image.n_frames, 3)
            self.assertEqual(image.info["loop"], 0)
            for index, x in enumerate((14, 32, 50)):
                image.seek(index)
                self.assertEqual(image.info["duration"], 200)
                frame = image.convert("RGB")
                self.assertEqual(frame.getpixel((x, 24)), (232, 120, 53))
                for other in {14, 32, 50} - {x}:
                    self.assertEqual(frame.getpixel((other, 24)), (255, 255, 255))

    def test_array_image_keeps_rows_columns_and_modes(self):
        self.run_script("image_array.py")
        with Image.open(self.folder / "out/array-image.png") as image:
            self.assertEqual(image.size, (100, 100))
            self.assertEqual(image.mode, "RGB")
            self.assertEqual(image.getpixel((49, 49)), (255, 0, 0))
            self.assertEqual(image.getpixel((50, 49)), (0, 0, 0))
        with Image.open(self.folder / "out/array-gray.png") as image:
            self.assertEqual(image.mode, "L")
            self.assertEqual(image.getpixel((49, 49)), 76)

    def run_request(self, arguments, environment, response=None):
        script = self.copy_script("request_image.py")
        output = io.StringIO()
        with patch.dict(os.environ, environment, clear=True), \
                patch.object(sys, "argv", [str(script), *arguments]), \
                patch("urllib.request.urlopen") as send, \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            if response is None:
                send.side_effect = AssertionError("Unexpected network request")
            else:
                send.return_value = io.BytesIO(json.dumps(response).encode())
            runpy.run_path(str(script), run_name="__main__")
        return output.getvalue(), send

    def test_api_preview_runs_without_a_key_or_network(self):
        output, _ = self.run_request([], {})
        payload = json.loads(output)
        self.assertEqual(payload["response_format"], "b64_json")
        self.assertEqual(payload["n"], 1)
        self.assertIn("orange circle", payload["prompt"])
        self.assertFalse((self.folder / "out").exists())

    def test_api_send_decodes_image_and_keeps_key_out_of_output(self):
        png = io.BytesIO()
        Image.new("RGB", (2, 2), (255, 0, 0)).save(png, format="PNG")
        output, send = self.run_request(
            ["--send", "--prompt", "A red square"], {"EASEL_KEY": "test-only-key"},
            {"created": 0, "data": [{"b64_json": base64.b64encode(png.getvalue()).decode()}]},
        )
        request = send.call_args.args[0]
        self.assertEqual(json.loads(request.data)["prompt"], "A red square")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-only-key")
        self.assertNotIn("test-only-key", output)
        with Image.open(self.folder / "out/api-image.png") as image:
            self.assertEqual(image.getpixel((0, 0)), (255, 0, 0))

    def test_api_send_requires_key_before_contacting_service(self):
        with self.assertRaises(SystemExit) as error:
            self.run_request(["--send"], {})
        self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
