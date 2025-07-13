import os
import re
import openai
import pyperclip
import subprocess
import logging

from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, 'tanzimat.env')

load_dotenv(env_path)

# --- LOGGING CONFIGURATION ---
LOG_DIR = os.path.join(script_dir, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "prompt_generator.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

openai.api_key = os.getenv("OPENAI_API_KEY")  # Set this in your shell or .bashrc
CHARACTER_FILE = os.getenv("CHARACTERS_PTH")

def load_characters():
    logging.info(f"Loading characters from {CHARACTER_FILE}")
    try:
        with open(CHARACTER_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        pattern = r"[Character: (.*?)](.*?)(?=[Character: |\Z)"
        characters = {match[0].strip(): match[1].strip() for match in re.findall(pattern, content, re.DOTALL)}
        logging.info(f"Loaded {len(characters)} characters.")
        return characters
    except FileNotFoundError:
        logging.error(f"Character file not found: {CHARACTER_FILE}")
        return {}
    except Exception as e:
        logging.error(f"Error loading characters: {e}")
        return {}

def add_character():
    logging.info("Adding new character.")
    name = input("Enter character name: ").strip()
    print("Enter character description (end with empty line):")
    lines = []
    while True:
        line = input()
        if not line.strip():
            break
        lines.append(line)
    description = "\n".join(lines)
    try:
        with open(CHARACTER_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n[Character: {name}]\n{description}\n")
        print(f"\n✅ Character '{name}' added.\n")
        logging.info(f"Character '{name}' added successfully.")
    except Exception as e:
        logging.error(f"Error adding character '{name}': {e}")

def generate_prompt():
    logging.info("Generating prompt.")
    characters_dict = load_characters()
    if not characters_dict:
        print("❌ No characters loaded. Please add characters first.")
        logging.warning("No characters loaded for prompt generation.")
        return

    print("Available characters:", ", ".join(characters_dict.keys()))
    selected = input("Enter character names (comma-separated): ")
    selected_names = [name.strip() for name in selected.split(",") if name.strip() in characters_dict]

    if not selected_names:
        print("❌ No valid characters selected.")
        logging.warning("No valid characters selected for prompt generation.")
        return

    setting = input("Scene setting: ")
    emotion = input("Emotion to evoke: ")
    direction = input("Visual direction: ")
    purpose = input("Scene purpose: ")

    descriptions = [characters_dict[name] for name in selected_names]

    user_prompt = f"""
Characters:
{chr(10).join(['- ' + name for name in selected_names])}
Scene:
- Setting: {setting}
- Emotion: {emotion}
- Direction: {direction}
- Scene purpose: {purpose}

Generate a Leonardo.ai image prompt that naturally integrates the following character descriptions without naming them. The descriptions are:

{chr(10).join(descriptions)}

Ensure the final prompt reads as a single unified visual scene without listing characters.
"""

    system_prompt = """
You are an AI assistant tasked with generating Leonardo.ai-compatible image prompts for visual scenes. Characters are described in rich physical and cultural detail. Do the following:

- Fully integrate each character’s visual and cultural description into the scene.
- Never mention the character's name.
- Write one hyper-realistic, cinematic image prompt suitable for Leonardo.ai.
- The setting, mood, and direction must flow naturally.
- Maintain a modest, elegant tone, rooted in identity and aspiration.
- Output only the image prompt. Nothing else.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ]
        )

        result = response["choices"][0]["message"]["content"].strip()
        pyperclip.copy(result)
        print("\n✅ Prompt copied to clipboard:\n")
        print(result)
        logging.info("Prompt generated and copied to clipboard.")
    except openai.error.OpenAIError as e:
        print(f"❌ OpenAI API error: {e}")
        logging.error(f"OpenAI API error: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        logging.critical(f"An unexpected error occurred during prompt generation: {e}")

def rofi_menu():
    logging.info("Displaying Rofi menu.")
    menu = "Generate Prompt\nAdd Character"
    try:
        result = subprocess.run(
            ["rofi", "-dmenu", "-p", "Choose Action"],
            input=menu,
            capture_output=True,
            text=True,
            check=True
        )
        choice = result.stdout.strip()
        logging.info(f"Rofi menu choice: {choice}")
        if choice == "Generate Prompt":
            generate_prompt()
        elif choice == "Add Character":
            add_character()
        else:
            print("Cancelled or invalid choice.")
            logging.info("Rofi menu cancelled or invalid choice.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Rofi command failed: {e}")
        print(f"Error with Rofi: {e}")
    except Exception as e:
        logging.critical(f"An unexpected error occurred in rofi_menu: {e}")
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    logging.info("Starting prompt_generator.py script.")
    if not os.path.exists(CHARACTER_FILE):
        try:
            open(CHARACTER_FILE, "w").close()
            logging.info(f"Created empty character file: {CHARACTER_FILE}")
        except Exception as e:
            logging.critical(f"Error creating character file: {e}")
    rofi_menu()
    logging.info("prompt_generator.py script finished.")
