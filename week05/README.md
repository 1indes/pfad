# 8 October 2026 — images, frames and representations

This is the `week05` folder for the lesson taught on 8 October, after the
1 October holiday. The folder number follows the course content rather than the
calendar week.

**Dates to remember:** the mid-term quiz is in class on Thursday 22 October;
Assignment 3 (interactive experience) is due Sunday 1 November at 23:59
Hong Kong time. The assignment brief and submission instructions follow separately.

Start at the repository root (`pfad`), switch to `2026`, and pull the latest
material. These scripts declare their own dependencies for `uv`; they do not
need the Week 4 Worker environment. The first run needs internet to download
the libraries. Images are written to `week05/out/`, even if you run a script
from another folder.

```bash
git switch 2026
git pull
uv run week05/tiny_image.py
uv run week05/image_array.py
uv run week05/noise.py
uv run week05/make_gif.py
```

| Script | Inspect | Predict a change, then run again |
| --- | --- | --- |
| [tiny_image.py](tiny_image.py) | Four RGB tuples become `out/tiny-image.png`. | Set `pixels[0][1] = (255, 255, 255)` before `putdata`. Which square turns white? |
| [image_array.py](image_array.py) | A NumPy array becomes RGB and grayscale PNGs. | Change the red region. Compare array `(H, W, C)`, Pillow `(W, H)`, and modes `RGB` and `L`. |
| [noise.py](noise.py) | Seeded Python random values become `out/noise.png`. | Change `SEED`, then `WIDTH`. The upper bound in `randrange(256)` is excluded. |
| [make_gif.py](make_gif.py) | Three complete still frames become `out/moving-dot.gif`. | Reverse `POSITIONS`, then change `DURATION_MS`. Separate frame order from playback speed. |
| [logo_ascii.py](logo_ascii.py) | One source becomes ten text widths, a slider and a GIF. | Follow the tutorial below with your own image. |
| [request_image.py](request_image.py) | A JSON image request; an optional API response. | Add one observable material or composition constraint to the prompt. |

## Inspect an API request

This command prints the request data. It does not contact the image service
and does not need a key:

```bash
uv run week05/request_image.py --prompt "An orange circle centered on cream paper"
```

For an enabled classroom API account, copy the root `.env.example` to `.env`
once. From the repository root in PowerShell:

```powershell
Copy-Item .env.example .env
```

On macOS/Linux, use `cp .env.example .env`. If `.env` already exists, edit it
instead of copying over it. Set `EASEL_KEY=your-classroom-api-key` in `.env`.
This same root file is used by Week 06's song example. Both scripts use
`python-dotenv`; `uv run` installs it from their script dependencies. With an
existing Python environment, install it using `python -m pip install python-dotenv`.

The scripts locate `.env` relative to their source files, so the working
directory does not matter. Existing environment variables take precedence.
`.env` is ignored by Git; `.env.example` contains empty placeholders only.
Then add `--send`:

```bash
uv run week05/request_image.py --send
```

That sends one text-only generation request and saves `out/api-image.png`.
Do not put a key in the source, a screenshot or a commit. No student account or
paid call is needed for this tutorial. The ASCII image-edit comparison below
uses a source image, so it is a different request from this text-only example.

## One mark, several representations

We have two marks from the introductions: a pixel yarn-ball (Mark 18) and an arrow with a separate underscore (Mark 38). They are examples of student work, not final course branding. Their later ASCII-on-screen and wool treatments are **experiments**; the lecturer will replace the examples when the final two images are ready. Do not call them the chosen A/B logos yet.

The question today is: what survives when an image becomes a small grid of text? Changing the number of columns changes how much shape you can describe. It does **not** add genuine detail to the original pixels.

## 1. Predict, run, inspect

Open `assets/mark-18.png`. Identify the ball and its trailing yarn. Predict whether it will still be recognisable at 20 text columns.

Run the local Python example from the repository root:

```bash
uv run week05/logo_ascii.py
```

It uses `ascii-magic` to make **ten** text versions (12 to 66 columns at the same character-width ratio), writes a short looping GIF of changing text resolution, and makes `out/logo-ascii.html`. Open the HTML file in a browser: move the **columns** slider to compare sparse and dense versions, then press **Play**. The slider chooses precomputed text frames; Python and `ascii-magic` produce them first. The GIF is a separate file, not a video stream. The GIF uses the included DejaVu Sans Mono font (license in `assets/DejaVuSansMono-LICENSE.txt`) so spaces and character positions stay aligned. On a phone, swipe sideways within the text panel to see the widest frames at a readable size. First run downloads dependencies; no GPU, API key or account is needed.

Try changing the source:

```bash
uv run week05/logo_ascii.py --image week05/assets/mark-38.png
uv run week05/logo_ascii.py --image path/to/your-own-square-mark.png
```

For your own image, use artwork you have permission to publish. Do not upload another person's submission, a student photo, or a private image to an external image service. The example uses only local files.

Questions to write in your notes: At which width does the trailing strand disappear? Do dark/light character choices and cropping change the answer? Is a high number of characters the same as a high-resolution source photograph?

## 2. Compare two transformations

We have tried two opposite directions: start from the yarn-ball mark, convert it into ASCII, then use that ASCII image as a visual input for an *image edit* that stages the characters on a screen. Start from the arrow-and-underscore mark and edit its material into wool, keeping its two pieces distinct. These are exploratory outputs, not exact reproductions or the final choice.

Compare the actual [56-column ASCII input](assets/mark-18-ascii-edit-input.png) with the [draft CRT edit](assets/mark-18-crt-draft.png). This exact input is from an earlier, denser ten-size conversion of Mark 18; its character ramp differs from the smaller classroom script above. For the second case, compare the [original arrow-plus-underscore mark](assets/mark-38.png) with the [guided wool edit used in the slides](assets/mark-38-wool-guided.jpg). The input image matters when you judge what the model changed.

If the instructor has preflighted an image-edit client, use your exported ASCII image as the **input image** and describe what should change around it: "Put this ASCII mark on a dark CRT screen; retain the ball, trailing strand and character arrangement; no extra letters." Keep the input, prompt, output and model/settings together. This is an edit with an image input, **not** the text-only image-generation request from last week. No student account or paid call is required for this tutorial; use the prepared classroom example if the service is unavailable.

Compare the exact input with the edit. Can you still read the original ASCII characters? If not, the model made an approximate image of text, not a faithful copy of your file. If exact glyphs or a wordmark matter, composite the original text layer deterministically instead of relying on the model to spell it. For the arrow case, check that the arrow and underscore remain separate, rather than turning into a different symbol.

## 3. Make a small GitHub icon (optional)

Pick **your own** image, not the class's draft mark. The script writes `out/avatar-square.png` as one option. Check it at tiny size and in GitHub's circular preview. A dense text image may become unreadable as an avatar; a simpler silhouette often works better. If you want to use it, open GitHub **Settings → Public profile → Profile picture → Upload a photo** and choose your file yourself. You can change it back. This is a portfolio experiment, not a submission or a graded requirement.

Notice the three different decisions: which image is the source, which transformation you run, and which version *you* choose to publish as an icon.

## Optional local-model demo

[Run Stable Diffusion with Diffusers](diffusion/README.md) shows a separate `uv`
environment, accelerator-aware PyTorch installation, a device check, and a
Python pipeline that saves an image plus its settings. Follow this only if you
want to explore local models; it is not required for the tutorial. Pre-download
the libraries and weights, and expect CPU execution to be slow. The core examples
above still need no GPU or model download.

## Check the examples

From the repository root:

```bash
uv run week05/test_examples.py
uv run week05/test_logo_ascii.py
```

These checks inspect the actual pixels, frame order and local ASCII outputs.
The API check uses a prepared response and never calls the live service.

The frozen [2025 Week 5 archive](https://github.com/sd5913/pfad/tree/2025/week05)
has older model and webcam demonstrations. They are optional instructor
references; this tutorial does not require a GPU, PyTorch, a model download or
a camera.
