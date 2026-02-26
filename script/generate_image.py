#!/usr/bin/env python3
"""Generate an image with OpenAI Images API and save it locally."""

import argparse
import base64
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request
from datetime import datetime

API_URL = "https://api.openai.com/v1/images/generations"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an image using OpenAI API")
    parser.add_argument("prompt", help="Prompt used for image generation")
    parser.add_argument(
        "--model",
        default="gpt-image-1",
        help="Model name (default: gpt-image-1)",
    )
    parser.add_argument(
        "--size",
        default="1024x1024",
        choices=["1024x1024", "1536x1024", "1024x1536", "auto"],
        help="Image size",
    )
    parser.add_argument(
        "--quality",
        default="auto",
        choices=["low", "medium", "high", "auto"],
        help="Image quality",
    )
    parser.add_argument(
        "--background",
        default="auto",
        choices=["transparent", "opaque", "auto"],
        help="Background type",
    )
    parser.add_argument(
        "--format",
        default="png",
        choices=["png", "jpeg", "webp"],
        help="Output image format",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Output file path (default: image/generated-<timestamp>.<format>)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY is not set.", file=sys.stderr)
        return 1

    output_path = args.output
    if not output_path:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = f"image/generated-{ts}.{args.format}"

    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
        "quality": args.quality,
        "background": args.background,
        "output_format": args.format,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            response = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        print(f"API request failed ({err.code}): {body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as err:
        print(f"Network error: {err}", file=sys.stderr)
        return 1

    images = response.get("data") or []
    if not images:
        print("Error: no image data returned.", file=sys.stderr)
        return 1

    b64_data = images[0].get("b64_json")
    if not b64_data:
        print("Error: b64_json not found in API response.", file=sys.stderr)
        return 1

    image_bytes = base64.b64decode(b64_data)
    out = pathlib.Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(image_bytes)

    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
