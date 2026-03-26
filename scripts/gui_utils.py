import subprocess
import os
import sys

# Ensure DISPLAY is set for GUI tools
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':1'

def run_rofi(args, input_str=None):
    """Low-level helper to run rofi with given arguments."""
    try:
        cmd = ["rofi"] + args
        if input_str is not None:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            stdout, _ = process.communicate(input=input_str)
            return stdout.strip() if stdout else None
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout.strip() if result.stdout else None
    except Exception as e:
        print(f"Rofi error: {e}")
        return None

def get_rofi_input(prompt, initial_value=""):
    """Gets a string input from the user via rofi."""
    args = ["-dmenu", "-p", prompt]
    if initial_value:
        args.extend(["-filter", initial_value])
    return run_rofi(args)

def get_rofi_menu(prompt, items, index=False, fuzzy=True):
    """
    Shows a menu of items and returns the selected item string.
    If index=True, returns the integer index of the selected item.
    """
    args = ["-dmenu", "-p", prompt]
    if fuzzy:
        args.append("-i")
    if index:
        args.extend(["-format", "i", "-no-custom"])
    
    input_str = "\n".join(items)
    result = run_rofi(args, input_str=input_str)
    
    if index and result is not None:
        try:
            return int(result)
        except ValueError:
            return None
    return result

def strip_status(selected_text, prefixes=None):
    """Removes common status prefixes like [DONE] or [ ] from a string."""
    if not selected_text:
        return selected_text
    
    if prefixes is None:
        prefixes = ["[DONE] ", "[ ] ", "[X] ", "[O] "]
    
    for prefix in prefixes:
        if selected_text.startswith(prefix):
            return selected_text[len(prefix):].strip()
    return selected_text.strip()

def get_zenity_input(prompt, title="Input Required"):
    """Gets input via zenity entry dialog."""
    try:
        cmd = ["zenity", "--entry", "--title", title, "--text", prompt]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.strip() if result.stdout else None
    except Exception as e:
        print(f"Zenity input error: {e}")
        return None

def notify(title, message, urgency="normal"):
    """Sends a desktop notification."""
    try:
        subprocess.run(["notify-send", "-u", urgency, title, message])
    except Exception as e:
        print(f"Notification error: {e}")
