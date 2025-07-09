import subprocess
import os
import json
import random
import string
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('tanzimat.env')
# Utilities
def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def random_email():
    return f"{random_string(7)}@example.com"

def pick_multiline_text():
    result = subprocess.run([
        "zenity", "--text-info", "--editable",
        "--title=Enter Profile Info", "--width=400", "--height=300"
    ], capture_output=True, text=True)
    return result.stdout.strip()

def pick_image_from_rofi(directory):
    # Get all image files in the directory
    img_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
    image_files = [str(p) for p in Path(directory).rglob('*') if p.suffix.lower() in img_extensions]

    if not image_files:
        print("No image files found.")
        return None

    # Create the Rofi menu
    #rofi = subprocess.run(
    #    ['rofi', '-dmenu', '-p', 'Pick image'],
    #    input='\n'.join(image_files),
    #    text=True,
    #    capture_output=True
    #)

    selected = image_files[0]
    print(selected)
    #subprocess.run(['feh', selected])

    return selected if selected else None


# Main Flow
multiline_text = pick_multiline_text()
if not multiline_text:
    print("No text entered. Exiting.")
    exit()

image_path = pick_image_from_rofi(IMAGE_DIR)
if not image_path or not os.path.exists(image_path):
    print("No image selected. Exiting.")
    exit()

# Step 1: Send multiline text
form1 = {'details': multiline_text}
response1 = requests.post(UPLOAD_URL1, data=form1)
if not response1.ok:
    print("Failed to post profile details.")
    exit()

data_object = response1.json()['data']

# Step 2: Fill out form data
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

response2 = requests.post(UPLOAD_URL2, data=form2)
print(response2.json())
if not response2.ok:
    print("Failed to store profile data.")
    exit()

# Step 3: Upload image
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
os.remove(image_path)  # Clean up the image file after upload
print("Profile created and image uploaded successfully.")
