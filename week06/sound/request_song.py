#!/usr/bin/env python3
# /// script
# dependencies = ["python-dotenv>=1,<2"]
# ///
"""Easel song API lesson: OFFLINE preview unless --send is explicitly supplied.

Instructor-only, serialized demonstration: Suno's latest-attempt status is SHARED.
--send can spend credits. Never rerun it to recover a timeout or CAPTCHA.
Contract verified in Easel commit 7c2a419e1eb2143a071d31ae45f2f105fcbf6b81.
See ../README.md for defaults, setup and recovery guidance.
"""
import argparse
import http.client
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from uuid import UUID

GENERATIONS = "/v1/audio/generations"
STATUS = GENERATIONS + "/status"
DEFAULT_BASE_URL = "https://easel.ait4x.org"
DEFAULT_PROMPT = "Gentle ambient piano with warm strings, a relaxed mood and a simple melody"
DEFAULT_TITLE = "Studio Break"
DEFAULT_DURATION_SECONDS = 30


class SongError(Exception):
    """A safe, readable error that contains no credential or raw response body."""


def build_payload(prompt, *, title="", lyrics="", instrumental=False,
                  weirdness=None, style_influence=None, duration_seconds=None):
    """A deliberately small subset of the verified suno-music request schema."""
    if not (prompt.strip() or lyrics.strip()):
        raise SongError("Provide a nonblank prompt or lyrics.")
    if len(prompt) > 1000 or len(lyrics) > 5000:
        raise SongError("Maximum lengths: prompt 1,000 characters; lyrics 5,000.")
    if instrumental and lyrics.strip():
        raise SongError("Instrumental requests require empty lyrics.")
    payload = {"model": "suno-music", "prompt": prompt, "title": title,
               "make_instrumental": instrumental}
    if lyrics:
        payload["lyrics"] = lyrics
    for name, value, low, high in (
        ("weirdness", weirdness, 0, 100),
        ("style_influence", style_influence, 0, 100),
        ("duration_seconds", duration_seconds, 10, 360),
    ):
        if value is not None:
            if type(value) is not int or not low <= value <= high:
                raise SongError(f"{name} must be an integer from {low} to {high}.")
            payload[name] = value
    return payload


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward a bearer credential to a redirect destination.


class Client:
    """One HTTPS origin, fixed API paths, finite requests and no automatic retries."""
    def __init__(self, base_url, key, timeout=180):
        parsed = urllib.parse.urlsplit(base_url)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ("", "/")):
            raise SongError("EASEL_BASE_URL must be an HTTPS server root, without credentials.")
        if not key.strip() or any(character in key for character in "\r\n"):
            raise SongError("Set a valid EASEL_KEY (or EASEL_API_KEY) in .env or the environment.")
        self.base = base_url.rstrip("/")
        self.key = key
        self.timeout = timeout
        self.opener = urllib.request.build_opener(NoRedirect())

    def _open(self, method, path, payload=None):
        if (not path.startswith("/v1/") or "\\" in path
                or any(ord(character) < 32 for character in path)
                or urllib.parse.urlsplit(path).netloc):
            raise SongError("Unsafe API path: absolute or foreign URLs are not accepted.")
        headers = {"Authorization": "Bearer " + self.key}
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(self.base + path, data=data,
                                         headers=headers, method=method)
        try:
            return self.opener.open(request, timeout=self.timeout)
        except urllib.error.HTTPError as error:
            # Do not print raw server responses: they may echo sensitive inputs.
            retry = error.headers.get("Retry-After", "") if error.headers else ""
            wait = f" Wait at least {retry} seconds." if retry.isdigit() else ""
            raise SongError(f"HTTP {error.code}.{wait} Inspect generation status; "
                            "do not automatically repeat a generation POST.") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise SongError("Request failed or timed out; submission may be ambiguous. "
                            "Inspect status and the Suno library before any new POST.") from None

    def json(self, method, path, payload=None):
        try:
            with self._open(method, path, payload) as response:
                data = json.load(response)
        except (ValueError, UnicodeError):
            raise SongError("The API returned invalid JSON; inspect status before retrying.") from None
        except (OSError, http.client.HTTPException):
            raise SongError("Response was interrupted; submission may be ambiguous. "
                            "Inspect status and the Suno library; do not repeat the POST.") from None
        if not isinstance(data, dict):
            raise SongError("Expected a JSON object from the API.")
        return data

    def content(self, path):
        try:
            with self._open("GET", path) as response:
                kind = response.headers.get("Content-Type", "").split(";", 1)[0]
                if not (kind.startswith("audio/") or kind in (
                        "video/mp4", "video/webm", "application/ogg", "application/octet-stream")):
                    raise SongError("The content endpoint did not return audio bytes.")
                data = response.read(64 * 1024 * 1024 + 1)
        except (OSError, http.client.HTTPException):
            raise SongError("Audio transfer was interrupted. Inspect the track ID and "
                            "retrieve its saved content; do not generate again.") from None
        if not data or len(data) > 64 * 1024 * 1024:
            raise SongError("Audio is empty or exceeds this teaching example's 64 MiB limit.")
        return data


def checked_id(value):
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        raise SongError("Missing or invalid UUID in the API response.") from None


def generate_and_save(client, payload, output, *, wait_seconds=300,
                      clock=time.monotonic, sleep=time.sleep):
    """Submit ONCE, poll with a deadline, save all returned songs in real formats."""
    if wait_seconds <= 0:
        raise SongError("The polling budget must be positive.")
    before = client.json("GET", STATUS)
    if before.get("status") in ("pending", "captcha_required"):
        raise SongError("The shared Suno browser has an unconfirmed attempt; do not submit.")
    if before.get("status") not in ("idle", "submitted", "complete", "error", "abandoned"):
        raise SongError("The shared Suno browser state is unknown; inspect it before submitting.")
    result = client.json("POST", GENERATIONS, payload)  # Never retry this operation.
    attempt = checked_id(result.get("attempt_id"))
    print("Attempt:", attempt, "(keep this ID for recovery)")
    deadline = clock() + wait_seconds

    def pause():
        remaining = deadline - clock()
        if remaining <= 0:
            raise SongError(f"Timed out waiting for attempt {attempt}; inspect status, do not resubmit.")
        sleep(min(5, remaining))
        if clock() >= deadline:
            raise SongError(f"Timed out waiting for attempt {attempt}; inspect status, do not resubmit.")

    while True:
        status = result.get("status")
        if status == "captcha_required":
            raise SongError(f"CAPTCHA needs manual operator action for attempt {attempt}. "
                            "Inspect the status response for novnc_url; resume polling, do not resubmit.")
        if status not in ("pending", "submitted", "complete"):
            raise SongError(f"Generation stopped or returned an unexpected state for attempt {attempt}.")
        tracks = result.get("songs")
        if status in ("submitted", "complete") and isinstance(tracks, list) and tracks:
            break
        pause()
        result = client.json("GET", STATUS)
        if result.get("attempt_id") != attempt:
            raise SongError(f"Shared status now belongs to another attempt. Keep {attempt}; do not resubmit.")

    ids = [checked_id(track.get("id")) for track in tracks if isinstance(track, dict)]
    if len(ids) != len(tracks) or len(set(ids)) != len(ids):
        raise SongError("The API returned invalid or duplicate tracks.")
    print("Tracks:", ", ".join(ids), "(poll these IDs independently)")
    output = Path(output)
    files = []
    for track, track_id in zip(tracks, ids):
        path = "/v1/audio/tracks/" + track_id
        while track.get("status") != "complete":
            if track.get("status") == "error":
                raise SongError(f"Track failed: {track_id}.")
            if track.get("status"):
                pause()
            # A generation's initial song entry may contain only its ID.
            track = client.json("GET", path)
            if checked_id(track.get("id")) != track_id:
                raise SongError("Track response ID changed; stopped before downloading.")
            if not track.get("status"):
                raise SongError(f"Track response lacks status: inspect {track_id}; do not resubmit.")
        saved = client.json("POST", path + "/download")
        filename = saved.get("filename")
        if (not isinstance(filename, str) or not filename or filename in (".", "..")
                or "/" in filename or "\\" in filename or ":" in filename
                or any(ord(character) < 32 for character in filename)):
            raise SongError("Unsafe or missing audio filename.")
        # Ignore server-supplied URLs; the verified endpoint is on our chosen origin.
        data = client.content(path + "/content")
        if "size" in saved and saved["size"] != len(data):
            raise SongError("Downloaded audio size does not match save metadata.")
        output.mkdir(parents=True, exist_ok=True)
        destination = output / filename
        with destination.open("xb") as file:  # Never overwrite an earlier student's output.
            file.write(data)
        files.append(destination)
    return files


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="describe the music")
    parser.add_argument("--lyrics", default="")
    parser.add_argument("--title", default=DEFAULT_TITLE, help="song title")
    parser.add_argument("--instrumental", action="store_true")
    parser.add_argument("--weirdness", type=int)
    parser.add_argument("--style-influence", type=int)
    parser.add_argument("--duration-seconds", type=int, default=DEFAULT_DURATION_SECONDS,
                        help="requested length, from 10 to 360 seconds")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "out/songs",
                        help="save all returned tracks here")
    parser.add_argument("--wait-seconds", type=int, default=300,
                        help="polling budget; individual HTTP requests time out after 180 seconds")
    parser.add_argument("--send", action="store_true", help="REAL generation: may spend credits")
    args = parser.parse_args(argv)
    try:
        payload = build_payload(args.prompt, title=args.title, lyrics=args.lyrics,
                                instrumental=args.instrumental, weirdness=args.weirdness,
                                style_influence=args.style_influence,
                                duration_seconds=args.duration_seconds)
        if not args.send:
            print("OFFLINE PREVIEW: no connection, credentials or credits used.")
            print("POST", GENERATIONS)
            print(json.dumps(payload, indent=2))
            return 0
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
        base = os.environ.get("EASEL_BASE_URL", DEFAULT_BASE_URL)
        key = os.environ.get("EASEL_API_KEY") or os.environ.get("EASEL_KEY", "")
        if not key:
            raise SongError("Set EASEL_KEY (or EASEL_API_KEY) in the root .env or environment before --send.")
        client = Client(base, key)
        for path in generate_and_save(client, payload, args.output_dir, wait_seconds=args.wait_seconds):
            print("Saved", path)
        return 0
    except SongError as error:
        print("Stopped:", error, file=sys.stderr)
    except OSError:
        print("Could not save the file; inspect existing output and track IDs before retrying.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
