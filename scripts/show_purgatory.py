import requests
import subprocess
import os
import random
import string

def show_rofi_menu(options, prompt="Select an option:"):
    rofi_input = "\n".join(options)
    result = subprocess.run(["rofi", "-dmenu", "-p", prompt], input=rofi_input, text=True, capture_output=True)
    return result.stdout.strip()

def make_id(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def handle_image_upload(email):
    try:
        file_path = subprocess.run(["zenity", "--file-selection", '--title=Choose an image'], capture_output=True, text=True).stdout.strip()
        if not file_path:
            show_rofi_menu(["No file selected."], prompt="Info")
            return

        url = 'https://expatelitesingles.com/api/sirri_api/uploadFile'
        random_filename = f"{make_id(10)}.png"

        with open(file_path, 'rb') as f:
            files = {'file': (random_filename, f, 'image/png')}
            form_data = {
                'fileName': random_filename,
                'name': email,
                'gender': 'Female'
            }

            show_rofi_menu(["Uploading image..."], prompt="Status")
            response = requests.post(url, files=files, data=form_data)
            response.raise_for_status()
            data = response.json()

            if data.get("responsecode") not in [500, 400]:
                show_rofi_menu(["Image uploaded successfully!"], prompt="Success")
                # Assuming we should proceed with activation after upload
                handle_activation(email)
            else:
                if data.get("responsecode") == 400:
                    show_rofi_menu(["Picture upload failed. Continue in account."], prompt="Warning")
                else:
                    show_rofi_menu([f"Error: {data.get('message', 'Unknown error')}"], prompt="Error")

    except FileNotFoundError:
        show_rofi_menu(["Error: 'zenity' command not found. Please install it to use this feature."], prompt="Error")
    except requests.exceptions.RequestException as e:
        show_rofi_menu([f"Error during upload: {e}"], prompt="Error")
    except Exception as e:
        show_rofi_menu([f"An unexpected error occurred: {e}"], prompt="Error")

def handle_auto_message(email):
    try:
        url = "https://expatelitesingles.com/api/sirri_api/auto_messages_email"
        formdata = {'EMAIL': email}
        response = requests.post(url, data=formdata)
        response.raise_for_status()
        data = response.json()
        if data.get("responsecode") == 200:
            matches = data.get("matches", [])
            show_rofi_menu([f"Auto Messaged. Matches: {len(matches)}"], prompt="Success")
        else:
            show_rofi_menu([f"Error in auto-messaging: {data.get('message')}"], prompt="Error")
    except requests.exceptions.RequestException as e:
        show_rofi_menu([f"Error during auto-message: {e}"], prompt="Error")

def handle_activation(email):
    try:
        url = f"https://expatelitesingles.com/api/sirri_api/activate/{email}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get("responsecode") == 200:
            pass
    except requests.exceptions.RequestException as e:
        show_rofi_menu([f"Error during activation: {e}"], prompt="Error")

    handle_auto_message(email)

def main():
    os.environ['DISPLAY'] = ':0'
    try:
        response = requests.get("https://staging.expatelitesingles.com/api/sirri_api/get_purgatory")
        response.raise_for_status()
        data = response.json()

        if "acc" in data and data["acc"]:
            options = [f"{item['EMAIL']}" for item in data["acc"]]
            chosen_email = show_rofi_menu(options, prompt="Choose an email:")
            if chosen_email:
                pic_response = requests.get(f"https://expatelitesingles.com/api/profilepic/1?EMAIL={chosen_email}")
                
                if pic_response.status_code == 200 and pic_response.content:
                    handle_activation(chosen_email)
                else:
                    choice = show_rofi_menu(["Continue Without Pic", "Pick an Image", "Quit"], prompt="No profile pic found. What to do?")
                    if choice == "Continue Without Pic":
                        handle_activation(chosen_email)
                    elif choice == "Pick an Image":
                        handle_image_upload(chosen_email)
                    # If "Quit" or window closed, do nothing

        else:
            show_rofi_menu(["No accounts found in purgatory."], prompt="Info")

    except requests.exceptions.RequestException as e:
        show_rofi_menu([f"Error fetching data: {e}"])
    except (KeyError, TypeError) as e:
        show_rofi_menu([f"Error parsing response: {e}"])

if __name__ == "__main__":
    main()
