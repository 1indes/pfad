# /// script
# dependencies = ["python-dotenv>=1,<2"]
# ///
"""Preview an image request; use --send with an enabled classroom API account."""

import argparse
import base64
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", default="An orange circle on cream paper")
    parser.add_argument("--send", action="store_true", help="Send the request using EASEL_KEY")
    args = parser.parse_args()
    payload = {
        "model": "qwen-image-2.1",
        "prompt": args.prompt,
        "size": "1024x1024",
        "n": 1,
        "response_format": "b64_json",
    }
    if not args.send:
        print(json.dumps(payload, indent=2))
        return

    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    key = os.environ.get("EASEL_KEY")
    if not key:
        parser.error("--send requires EASEL_KEY in the root .env or environment; see .env.example")
    headers = {
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
    }
    request = Request("https://easel.ait4x.org/v1/images/generations",
                      data=json.dumps(payload).encode(), headers=headers)
    with urlopen(request, timeout=600) as response:
        result = json.load(response)
    image = base64.b64decode(result["data"][0]["b64_json"])
    out = Path(__file__).resolve().parent / "out"
    out.mkdir(exist_ok=True)
    (out / "api-image.png").write_bytes(image)
    print("saved", out / "api-image.png")


if __name__ == "__main__":
    main()
