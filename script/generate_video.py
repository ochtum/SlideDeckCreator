#!/usr/bin/env python3
"""Generate a video with OpenAI Videos API and save it locally."""

import argparse
import json
import mimetypes
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime

API_BASE = "https://api.openai.com/v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a video using OpenAI Videos API"
    )
    parser.add_argument("prompt", help="Prompt used for video generation")
    parser.add_argument(
        "--model",
        default="sora-2",
        choices=["sora-2", "sora-2-pro"],
        help="Video model",
    )
    parser.add_argument(
        "--size",
        default="720x1280",
        choices=["720x1280", "1280x720", "1024x1792", "1792x1024"],
        help="Output size",
    )
    parser.add_argument(
        "--seconds",
        default="4",
        choices=["4", "8", "12"],
        help="Video length in seconds",
    )
    parser.add_argument(
        "--input-reference",
        default="",
        help="Path to input reference image (jpeg/png/webp)",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=10,
        help="Polling interval in seconds",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Timeout in seconds for waiting completion",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Output file path (default: video/generated-<timestamp>.mp4)",
    )
    return parser.parse_args()


def make_multipart(fields: dict[str, str], file_field: tuple[str, str] | None) -> tuple[bytes, str]:
    boundary = f"----CodexBoundary{uuid.uuid4().hex}"
    chunks: list[bytes] = []

    for key, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8")
        )
        chunks.append(value.encode("utf-8"))
        chunks.append(b"\r\n")

    if file_field:
        field_name, file_path = file_field
        path = pathlib.Path(file_path)
        content = path.read_bytes()
        mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="{path.name}"\r\n'
            ).encode("utf-8")
        )
        chunks.append(f"Content-Type: {mime}\r\n\r\n".encode("utf-8"))
        chunks.append(content)
        chunks.append(b"\r\n")

    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(chunks)
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def api_json_request(method: str, path: str, api_key: str) -> dict:
    req = urllib.request.Request(
        urllib.parse.urljoin(API_BASE, path),
        method=method,
        headers={
            "Authorization": f"Bearer {api_key}",
        },
    )

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def create_video_job(
    api_key: str,
    prompt: str,
    model: str,
    size: str,
    seconds: str,
    input_reference: str,
) -> dict:
    fields = {
        "prompt": prompt,
        "model": model,
        "size": size,
        "seconds": seconds,
    }
    file_field = ("input_reference", input_reference) if input_reference else None
    body, content_type = make_multipart(fields, file_field)

    req = urllib.request.Request(
        urllib.parse.urljoin(API_BASE, "/videos"),
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": content_type,
        },
    )

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download_video_content(api_key: str, video_id: str, output_path: str) -> None:
    req = urllib.request.Request(
        urllib.parse.urljoin(API_BASE, f"/videos/{video_id}/content"),
        method="GET",
        headers={
            "Authorization": f"Bearer {api_key}",
        },
    )

    with urllib.request.urlopen(req) as resp:
        content = resp.read()

    out = pathlib.Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(content)


def main() -> int:
    args = parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY is not set.", file=sys.stderr)
        return 1

    if args.input_reference and not pathlib.Path(args.input_reference).is_file():
        print(
            f"Error: input reference file not found: {args.input_reference}",
            file=sys.stderr,
        )
        return 1

    output_path = args.output
    if not output_path:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = f"video/generated-{ts}.mp4"

    try:
        job = create_video_job(
            api_key=api_key,
            prompt=args.prompt,
            model=args.model,
            size=args.size,
            seconds=args.seconds,
            input_reference=args.input_reference,
        )
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        print(f"API request failed ({err.code}): {body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as err:
        print(f"Network error: {err}", file=sys.stderr)
        return 1

    video_id = job.get("id")
    if not video_id:
        print("Error: video id missing in create response.", file=sys.stderr)
        return 1

    status = job.get("status", "unknown")
    progress = job.get("progress")
    progress_text = f", progress={progress}%" if progress is not None else ""
    print(f"job_id={video_id}, status={status}{progress_text}", file=sys.stderr)

    start = time.time()
    while status in {"queued", "in_progress"}:
        if time.time() - start > args.timeout:
            print("Error: timed out while waiting for video completion.", file=sys.stderr)
            return 1

        time.sleep(args.poll_interval)

        try:
            job = api_json_request("GET", f"/videos/{video_id}", api_key)
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", errors="replace")
            print(f"Status check failed ({err.code}): {body}", file=sys.stderr)
            return 1
        except urllib.error.URLError as err:
            print(f"Network error: {err}", file=sys.stderr)
            return 1

        status = job.get("status", "unknown")
        progress = job.get("progress")
        progress_text = f", progress={progress}%" if progress is not None else ""
        print(f"status={status}{progress_text}", file=sys.stderr)

    if status != "completed":
        error = job.get("error")
        print(f"Error: video generation ended with status={status}", file=sys.stderr)
        if error:
            print(f"details: {error}", file=sys.stderr)
        return 1

    try:
        download_video_content(api_key=api_key, video_id=video_id, output_path=output_path)
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        print(f"Download failed ({err.code}): {body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as err:
        print(f"Network error: {err}", file=sys.stderr)
        return 1

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
