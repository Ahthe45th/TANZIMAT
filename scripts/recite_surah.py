#!/usr/bin/env python3

import subprocess
import os
import json
import random
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Adjusted path to find quran_data.json in the 'dist' folder, assuming 'dist' is a sibling to 'scripts'
QURAN_DATA_FILE = os.path.join(SCRIPT_DIR, 'quran_data.json')

# Set DISPLAY environment variable for rofi, if not already set
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':1'

def get_rofi_input(prompt, options=None):
    """Gets user input using rofi -dmenu."""
    rofi_command = ["rofi", "-dmenu", "-p", prompt]
    if options:
        # For options, rofi -dmenu with -format i (index) is used to get the index directly.
        rofi_command.extend(["-format", "i", "-no-custom"])
        try:
            rofi_process = subprocess.run(rofi_command, input="\n".join(options), capture_output=True, text=True, check=True)
            selected_index = int(rofi_process.stdout.strip())
            if 0 <= selected_index < len(options):
                return options[selected_index]
            else:
                raise ValueError("Selected index out of range.")
        except ValueError:
            print("Error: Rofi returned an invalid index or no selection. Please ensure a valid option is chosen.")
            sys.exit(1)
    else:
        rofi_process = subprocess.run(rofi_command, capture_output=True, text=True, check=True)
        return rofi_process.stdout.strip()

def notify(title, message):
    """Sends a desktop notification."""
    try:
        subprocess.run(["notify-send", title, message], check=True)
    except FileNotFoundError:
        print(f"Notification: {title} - {message} (notify-send not found)")
    except subprocess.CalledProcessError as e:
        print(f"Failed to send notification: {e}")

def load_quran_data():
    """Loads Quran data from the JSON file."""
    try:
        with open(QURAN_DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        notify("Recite Surah Error", f"Quran data file not found at: {QURAN_DATA_FILE}")
        print(f"Error: Quran data file not found at {QURAN_DATA_FILE}. Please ensure it exists.")
        sys.exit(1)
    except json.JSONDecodeError:
        notify("Recite Surah Error", f"Could not decode {QURAN_DATA_FILE}. Ensure it's valid JSON.")
        print(f"Error: Could not decode {QURAN_DATA_FILE}. Ensure it's valid JSON.")
        sys.exit(1)



def display_ayats_zenity(ayats_data, surah_name, surah_num, start_ayah, end_ayah):
    """Displays the selected ayats in a Zenity window, allowing choice of language."""
    language_options = ["Arabic", "English", "Both"]
    try:
        #lang_choice = get_rofi_input("Choose display language:", language_options)
        lang_choice = "Both"
    except subprocess.CalledProcessError:
        print("Rofi cancelled. Exiting.")
        sys.exit(0)

    content = f"# Recitation from Surah {surah_name} ({surah_num}), Ayats {start_ayah}-{end_ayah}\n\n"
    
    arabic_ayats = ayats_data['arabic_ayats']
    english_ayats = ayats_data['english_ayats']

    for i in range(len(arabic_ayats)):
        content += f"**Ayah {start_ayah + i}:**\n"
        if lang_choice in ["Arabic", "Both"]:
            content += f"Arabic: {arabic_ayats[i]}\n"
        if lang_choice in ["English", "Both"]:
            content += f"English: {english_ayats[i]}\n"
        content += "\n" # Add an empty line between ayats

    try:
        # Pass content via stdin for multi-line text-info dialog
        subprocess.run([
            "zenity", "--text-info",
            "--title=Quran Recitation", # Updated title
            f"--width={800}", f"--height={600}"
        ], input=content.encode('utf-8'), check=True) # Encode content for stdin
    except FileNotFoundError:
        print("Zenity not found. Please install zenity to display recommended ayats in a GUI window.")
        # Fallback to stdout, but need to adapt it for the new data structure
        print(f"\n--- Recitation from Surah {surah_name} ({surah_num}), Ayats {start_ayah}-{end_ayah} ---")
        for i in range(len(arabic_ayats)):
            print(f"Ayah {start_ayah + i}:")
            if lang_choice in ["Arabic", "Both"]:
                print(f"Arabic: {arabic_ayats[i]}")
            if lang_choice in ["English", "Both"]:
                print(f"English: {english_ayats[i]}")
            print("-----------------------------------------------------------------\n")
    except subprocess.CalledProcessError as e:
        print(f"Zenity command failed: {e}")
        # Fallback to stdout
        print(f"\n--- Recitation from Surah {surah_name} ({surah_num}), Ayats {start_ayah}-{end_ayah} ---")
        for i in range(len(arabic_ayats)):
            print(f"Ayah {start_ayah + i}:")
            if lang_choice in ["Arabic", "Both"]:
                print(f"Arabic: {arabic_ayats[i]}")
            if lang_choice in ["English", "Both"]:
                print(f"English: {english_ayats[i]}")
            print("-----------------------------------------------------------------\n")

def main():
    quran_data = load_quran_data()
    if not quran_data:
        sys.exit(1)

    mode_options = ["1. Manual Recitation", "2. Recommended Recitation"]
    try:
        #mode_choice_str = get_rofi_input("Choose mode:", mode_options)
        # Extract the number from the string, e.g., "1. Manual Recitation" -> 1
        #mode_choice = int(mode_choice_str.split('.')[0].strip())
        mode_choice = 2
    except ValueError:
        notify("Recite Surah", "Invalid mode choice. Exiting.")
        print("Invalid mode choice. Exiting.")
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("Rofi cancelled. Exiting.")
        sys.exit(0) # User cancelled rofi

    selected_ayats_data = {}
    surah_name = ""
    surah_num = 0
    start_ayah_display = 0
    end_ayah_display = 0

    if mode_choice == 1: # Manual Recitation
        try:
            surah_options = [f"{s['surah_number']}. {s['name']}" for s in quran_data]
            selected_surah_option = get_rofi_input("Select Surah:", surah_options)
            surah_number = int(selected_surah_option.split('.')[0].strip())

            surah = quran_data[surah_number - 1]
            surah_name = surah["name"]
            surah_num = surah["surah_number"]

            num_ayats_in_surah = len(surah['arabic_ayats']) # Use arabic_ayats for length check

            start_ayah_str = get_rofi_input(f"Enter Starting Ayah for {surah_name} (1-{num_ayats_in_surah}):")
            start_ayah = int(start_ayah_str)
            if not (1 <= start_ayah <= num_ayats_in_surah):
                notify("Recite Surah Error", "Invalid Starting Ayah.")
                print("Invalid Starting Ayah.")
                sys.exit(1)

            end_ayah_str = get_rofi_input(f"Enter Ending Ayah for {surah_name} ({start_ayah}-{num_ayats_in_surah}):")
            end_ayah = int(end_ayah_str)
            if not (start_ayah <= end_ayah <= num_ayats_in_surah):
                notify("Recite Surah Error", "Invalid Ending Ayah.")
                print("Invalid Ending Ayah.")
                sys.exit(1)

            selected_ayats_data = {
                "arabic_ayats": surah["arabic_ayats"][start_ayah - 1:end_ayah],
                "english_ayats": surah["english_ayats"][start_ayah - 1:end_ayah]
            }
            start_ayah_display = start_ayah
            end_ayah_display = end_ayah

        except ValueError:
            notify("Recite Surah", "Invalid number input. Exiting.")
            print("Invalid number input. Exiting.")
            sys.exit(1)
        except subprocess.CalledProcessError:
            print("Rofi cancelled. Exiting.")
            sys.exit(0)

    elif mode_choice == 2: # Recommended Recitation
        try:
            num_ayats_str = get_rofi_input("Enter number of Ayats to recommend:")
            num_ayats_to_recommend = int(num_ayats_str)
            if num_ayats_to_recommend <= 0:
                notify("Recite Surah Error", "Number of Ayats must be positive.")
                print("Number of Ayats must be positive.")
                sys.exit(1)

            # Randomly select a surah that has at least num_ayats_to_recommend
            suitable_surahs = [s for s in quran_data if len(s["arabic_ayats"]) >= num_ayats_to_recommend]
            if not suitable_surahs:
                notify("Recite Surah Error", f"No suitable surah found with at least {num_ayats_to_recommend} ayats.")
                print(f"Error: No suitable surah found with at least {num_ayats_to_recommend} ayats.")
                sys.exit(1)

            surah = random.choice(suitable_surahs)
            
            surah_name = surah["name"]
            surah_num = surah["surah_number"]

            # Randomly select a starting ayah index, ensuring enough ayats follow
            max_start_ayah_index = len(surah["arabic_ayats"]) - num_ayats_to_recommend
            start_ayah_index = random.randint(0, max_start_ayah_index)
            
            selected_ayats_data = {
                "arabic_ayats": surah["arabic_ayats"][start_ayah_index : start_ayah_index + num_ayats_to_recommend],
                "english_ayats": surah["english_ayats"][start_ayah_index : start_ayah_index + num_ayats_to_recommend]
            }
            start_ayah_display = start_ayah_index + 1
            end_ayah_display = start_ayah_index + num_ayats_to_recommend

        except ValueError:
            notify("Recite Surah", "Invalid number input. Exiting.")
            print("Invalid number input. Exiting.")
            sys.exit(1)
        except subprocess.CalledProcessError:
            print("Rofi cancelled. Exiting.")
            sys.exit(0)
    else:
        notify("Recite Surah", "Invalid mode choice. Exiting.")
        print("Invalid mode choice. Exiting.")
        sys.exit(1)
    
    if selected_ayats_data:
        display_ayats_zenity(selected_ayats_data, surah_name, surah_num, start_ayah_display, end_ayah_display)
        if mode_choice == 1:
            notify("Recite Surah", f"Displayed ayats from Surah {surah_name} ({surah_num}).")
        elif mode_choice == 2:
            notify("Recite Surah", f"Recommended ayats from Surah {surah_name} ({surah_num}) displayed.")
    else:
        notify("Recite Surah", "No ayats selected. Exiting.")


if __name__ == "__main__":
    main()
