#!/home/mehmet/miniconda3/envs/idris/bin/python
import os
import json

from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

#ENV_PATH = os.path.expanduser(
#    "~/Proyectos/TANZIMAT/scripts/tanzimat.env"
#)


#load_dotenv(ENV_PATH)

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key="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")

INPUT_DIR = Path("./Reflections")
OUTPUT_DIR = Path("./Reflectionsjson")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


PROMPT = """
You are a data normalization engine.

Your task is to convert the following daily reflection text into a clean JSON dictionary.

Rules:

1. Output ONLY valid JSON.
2. Keys must be snake_case.
3. All fields numeric.
4. yes/si/true/done = 1
5. no/false/empty = 0
6. sleep must be number else 0
7. prayer must be number else 0
8. keep date
9. no extra text

Text:
"""


def normalize(text: str) -> dict:

    response = client.responses.create(
        model="openai/gpt-5.4",
        input=PROMPT + "\n" + text,
        temperature=0,
    )

    content = response.output[0].content[0].text

    return json.loads(content)


for file in INPUT_DIR.iterdir():

    if not file.name.startswith("daily_reflection"):
        continue

    if not file.is_file():
        continue

    print("Processing:", file.name)

    with open(file, "r", encoding="utf-8") as f:
        text = f.read()

    try:
        data = normalize(text)

        out_name = file.stem + ".json"
        out_path = OUTPUT_DIR / out_name

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print("Saved:", out_path)

    except Exception as e:
        print("Error:", file.name, e)
