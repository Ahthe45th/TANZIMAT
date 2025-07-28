import subprocess
import os
import json
import random
import string
import requests
from pathlib import Path
from dotenv import load_dotenv
import logging

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, 'tanzimat.env')

load_dotenv(env_path)

# --- LOGGING CONFIGURATION ---
LOG_DIR = os.path.join(script_dir, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "menupload.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def notify(msg):
    subprocess.run(["notify-send", "[Profile Uploader]", msg])
    logging.info(f"Notification: {msg}")

IMAGE_DIR = os.getenv("UNAPLOADED_MEN_DIR")
UPLOAD_URL1 = "https://expatelitesingles.com/api/sirri_api/set_perfil_data"
UPLOAD_URL2 = "https://expatelitesingles.com/api/sirri_api/store_data"
UPLOAD_URL3 = "https://expatelitesingles.com/api/sirri_api/uploadFile"

# Utilities
def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def random_email():
    return f"{random_string(7)}@example.com"

def pick_multiline_text_yad():
    try:
        env = os.environ.copy()
        env["DISPLAY"] = ":0"
        if "DBUS_SESSION_BUS_ADDRESS" not in env:
            env["DBUS_SESSION_BUS_ADDRESS"] = f'unix:path=/run/user/{os.getuid()}/bus'

        result = subprocess.run(['zenity', '--text-info', '--editable', '--title', 'Multiline Input', '--width', '400', '--height', '300', '--filename=/dev/stdin'], input="Caption:", capture_output=True, text=True).stdout.strip().strip()

        #if result.returncode != 0:
        #    logging.warning("Yad was cancelled or failed.")
        #    return ""

        return result
    except Exception as e:
        logging.error(f"Yad failed: {e}")
        return ""

def pick_multiline_text():
    try:
        env = os.environ.copy()
        env["DISPLAY"] = ":0"  # or whatever your display is
        if "DBUS_SESSION_BUS_ADDRESS" not in env:
            # Try to load it manually if not present
            try:
                bus_address = subprocess.check_output(
                    ["grep", "-z", "DBUS_SESSION_BUS_ADDRESS", f"/proc/$(pgrep -u $USER gnome-session)/environ"],
                    shell=True
                ).decode().split("DBUS_SESSION_BUS_ADDRESS=", 1)[1].strip('\x00\n')
                env["DBUS_SESSION_BUS_ADDRESS"] = bus_address
            except Exception as e:
                logging.warning("Could not retrieve DBUS_SESSION_BUS_ADDRESS")

        result = subprocess.run([
            "zenity", "--editable", "--text-info",
            "--title=Enter Profile Info", "--width=400", "--height=300"
        ], capture_output=True, text=True, check=True, env=env)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Zenity failed: {e}. stderr: {e.stderr}")
        return ""


def pick_image_from_rofi(directory):
    logging.info(f"Picking image from directory: {directory}")
    img_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
    image_files = [str(p) for p in Path(directory).rglob('*') if p.suffix.lower() in img_extensions]

    if not image_files:
        logging.warning("No image files found.")
        print("No image files found.")
        return None

    selected = image_files[0]
    logging.info(f"Selected image: {selected}")
    print(selected)

    return selected if selected else None


def main():
    logging.info("Starting menupload.py script.")
    multiline_text = pick_multiline_text_yad()
    if not multiline_text:
        notify("No text entered. Exiting.")
        logging.warning("No text entered. Exiting.")
        exit()
    notify("Profile text captured.")

    image_path = pick_image_from_rofi(IMAGE_DIR)
    if not image_path or not os.path.exists(image_path):
        notify("No image selected or image not found. Exiting.")
        logging.error(f"No image selected or image not found: {image_path}. Exiting.")
        exit()
    notify(f"Image selected: {os.path.basename(image_path)}")

    # Step 1: Send multiline text
    notify("Sending profile details...")
    form1 = {'details': multiline_text}
    try:
        response1 = requests.post(UPLOAD_URL1, data=form1)
        response1.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        notify(f"Failed to post profile details: {e}")
        logging.error(f"Failed to post profile details: {e}")
        exit()
    notify("Profile details sent successfully.")
    logging.info("Profile details sent successfully.")

    data_object = response1.json()['data']

    # Step 2: Fill out form data
    notify("Generating form data...")
    email = random_email()
    password = random_string(12)
    package = random.choice(["Bronze", "Silver", "Gold", "Emerald", "Platinum", "Diamond"])
    zodiac = random.choice(["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"])
    rel_pref = random.choice(["Christian", "Muslim", "Hindu", "Spiritual", "Atheist"])
    rel_status = random.choice(["Single", "Divorced"])

    form2 = {
        "EMAIL": email,
        "password": password,
        "confirmpassword": password,
        "gender1": "Male",
        "package1": package,
        "religion1": "Christian",
        "zodiacsign1": zodiac,
        "relationshippreferencereligion4": rel_pref,
        "relationshipstatus1": rel_status,
        "futurespouse1": multiline_text
    }

    for x in data_object:
        form2[x] = data_object[x]

    notify("Storing profile data...")
    try:
        response2 = requests.post(UPLOAD_URL2, data=form2)
        response2.raise_for_status()
    except requests.exceptions.RequestException as e:
        notify(f"Failed to store profile data: {e}")
        logging.error(f"Failed to store profile data: {e}")
        exit()
    print(response2.json())
    notify("Profile data stored successfully.")
    logging.info("Profile data stored successfully.")

    # Step 3: Upload image
    notify("Uploading image...")
    try:
        with open(image_path, 'rb') as f:
            random_name = f"{random_string(10)}.png"
            files = {
                'file': (random_name, f, 'image/png')
            }
            data = {
                'fileName': random_name,
                'name': email,
                'gender': 'Female'
            }

            response = requests.post(UPLOAD_URL3, files=files, data=data)
            response.raise_for_status()
        os.remove(image_path)  # Clean up the image file after upload
        notify("Image uploaded and local file removed.")
        logging.info("Image uploaded and local file removed.")
    except FileNotFoundError:
        notify(f"Image file not found: {image_path}")
        logging.error(f"Image file not found: {image_path}")
        exit()
    except requests.exceptions.RequestException as e:
        notify(f"Failed to upload image: {e}")
        logging.error(f"Failed to upload image: {e}")
        exit()
    except Exception as e:
        notify(f"An unexpected error occurred during image upload: {e}")
        logging.critical(f"An unexpected error occurred during image upload: {e}")
        exit()

    notify("Profile created and image uploaded successfully.")
    logging.info("menupload.py script finished successfully.")

if __name__ == '__main__':
    try:
        notify("Men upload script")
        main()
    except Exception as e:
        logging.critical(f"Script failed: {e}")
        subprocess.run(["notify-send", "Menu Upload Error", f"Script failed: {e}"])
