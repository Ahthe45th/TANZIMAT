import requests
import sys

API_KEY = "sk_d12858a8bfb4f14c6be826dfba9f16e080ab0dfd633f1711"
VOICE_ID = "Xb7hH8MSUJpSbSDYk0k2"  # example voice
TEXT = " ".join(sys.argv[2:])

url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
headers = {
    "xi-api-key": API_KEY,
    "accept": "audio/mpeg",
    "content-type": "application/json"
}
data = {
    "text": TEXT,
    "model_id": "eleven_multilingual_v2"
}
resp = requests.post(url, json=data, headers=headers)
with open(f"{sys.argv[1]}.mp3", "wb") as f:
    f.write(resp.content)
