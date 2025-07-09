import requests
import subprocess
import os
import random
import string
from dotenv import load_dotenv

load_dotenv('tanzimat.env')
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
