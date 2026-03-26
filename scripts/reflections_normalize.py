#!/home/jazeelakarima/expatenv/bin/python3
import os
import re
import json
import sys
from pathlib import Path
from typing import Optional

from openai import OpenAI
from dotenv import load_dotenv

ENV_PATH = os.path.expanduser("/etc/reflections.env")
load_dotenv(ENV_PATH)

API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is missing from environment.")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

INPUT_DIR = Path("~/Reflections")
OUTPUT_DIR = Path("~/Reflectionsjson")

PROMPT = """
You are a data normalization engine.

Your task is to convert the following daily reflection text into a clean JSON dictionary.

Rules:

1. Output ONLY valid JSON.
2. Keys must be snake_case.
3. All fields numeric except date, which should be preserved as a date string if present.
4. yes/si/true/done = 1
5. no/false/empty = 0
6. sleep must be number else 0
7. prayer must be number else 0
8. keep date
9. no extra text

Text:
"""


def extract_date_from_filename(file_path: Path) -> Optional[str]:
    """
    Tries to extract a date from the filename.
    Supports patterns like:
    - daily_reflection_2026-03-26.txt
    - daily_reflection_2026_03_26.txt
    - daily_reflection_20260326.txt
    """
    name = file_path.stem

    patterns = [
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{4}_\d{2}_\d{2})",
        r"(\d{8})",
    ]

    for pattern in patterns:
        match = re.search(pattern, name)
        if match:
            raw = match.group(1)

            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
                return raw

            if re.fullmatch(r"\d{4}_\d{2}_\d{2}", raw):
                return raw.replace("_", "-")

            if re.fullmatch(r"\d{8}", raw):
                return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"

    return None


def build_output_path(file_path: Path) -> Path:
    """
    Prefer naming the output by extracted date.
    If no date is found, fall back to source stem.
    """
    file_date = extract_date_from_filename(file_path)

    if file_date:
        return OUTPUT_DIR / f"{file_date}.json"

    return OUTPUT_DIR / f"{file_path.stem}.json"


def extract_response_text(response) -> str:
    """
    Safely pull text out of the model response.
    """
    try:
        if hasattr(response, "output_text") and response.output_text:
            return response.output_text.strip()
    except Exception:
        pass

    try:
        parts = []
        for item in response.output:
            if getattr(item, "type", None) != "message":
                continue

            for content in getattr(item, "content", []):
                text = getattr(content, "text", None)
                if text:
                    parts.append(text)

        combined = "\n".join(parts).strip()
        if combined:
            return combined
    except Exception as e:
        raise ValueError(f"Could not extract text from response: {e}") from e

    raise ValueError("Model response did not contain usable text.")


def normalize(text: str) -> dict:
    response = client.responses.create(
        model="openai/gpt-5.4",
        input=PROMPT + "\n" + text,
    )

    content = extract_response_text(response)

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model did not return valid JSON. Raw output: {content}") from e


def process_file(file_path: Path) -> None:
    if not file_path.is_file():
        print(f"Skipping non-file: {file_path}")
        return

    if not file_path.name.startswith("daily_reflection"):
        print(f"Skipping unrelated file: {file_path.name}")
        return

    out_path = build_output_path(file_path)

    if out_path.exists():
        print(f"Skipping {file_path.name}: destination already exists -> {out_path}")
        return

    print(f"Processing: {file_path.name}")
    print(f"Destination: {out_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    data = normalize(text)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved: {out_path}")


def main() -> int:
    if not INPUT_DIR.exists():
        print(f"Input directory does not exist: {INPUT_DIR}", file=sys.stderr)
        return 1

    if not INPUT_DIR.is_dir():
        print(f"Input path is not a directory: {INPUT_DIR}", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(INPUT_DIR.iterdir())
    if not files:
        print(f"No files found in: {INPUT_DIR}")
        return 0

    had_error = False

    for file_path in files:
        try:
            process_file(file_path)
        except Exception as e:
            had_error = True
            print(f"Error processing {file_path.name}: {e}", file=sys.stderr)

    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
