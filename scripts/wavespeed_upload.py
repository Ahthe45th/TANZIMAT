import requests
import os

from wavespeed import Client

WAVESPEED_API_KEY=""

def upload_file(file_path):
    url = "https://api.wavespeed.ai/api/v3/media/upload/binary"

    headers = {
        "Authorization": f"Bearer {WAVESPEED_API_KEY}"
    }

    filename = os.path.basename(file_path)

    with open(file_path, "rb") as f:
        files = {
            "file": (filename, f)
        }

        response = requests.post(
            url,
            headers=headers,
            files=files
        )

    response.raise_for_status()
    return response.json()["data"]["download_url"]

client = Client(api_key=WAVESPEED_API_KEY)

jpegfiles = [os.path.join("/home/mehmet/Downloads/DYABvideos/", x) for x in os.listdir("/home/mehmet/Downloads/DYABvideos/") if x.endswith('.jpeg')]

for jpeg in jpegfiles:
    audiopth = jpeg.replace(".jpeg", ".ogg")
    
    audiourl = upload_file(audiopth)
    print(audiourl)
    jpegurl = upload_file(jpeg)
    print(jpegurl)

    output = client.run("wavespeed-ai/infinitetalk", {
        "audio": audiourl,
        "image": jpegurl,
        "resolution": "480p",
        "seed": -1
    })

    os.remove(audiopth)
    os.remove(jpeg)
