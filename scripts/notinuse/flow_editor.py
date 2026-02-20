#!/usr/bin/env python3
import subprocess
from pathlib import Path
import os

# Define paths
SCRIPT_DIR = Path(__file__).resolve().parent
FLOW_DIR = SCRIPT_DIR.parent / "flows"
EDITOR_FILE = Path.home() / ".selected_editor"

def get_editor():
    """Get the user's preferred editor, with a fallback."""
    if EDITOR_FILE.exists():
        editor = EDITOR_FILE.read_text().strip()
        if editor:
            return editor
    # Fallback to common editors
    return os.environ.get("EDITOR", "vim")

def rofi(prompt: str, options: list[str]) -> str:
    """Show a rofi menu and return the selected value."""
    joined = "\n".join(options)
    result = subprocess.run(
        ["rofi", "-dmenu", "-p", prompt],
        input=joined,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()

def main():
    """Main function to select and edit a flow."""
    if not FLOW_DIR.exists():
        subprocess.run(["notify-send", "Flow Editor", "Flows directory not found."])
        return

    flows = [f.name for f in FLOW_DI.glob("*.json")]
    if not flows:
        subprocess.run(["notify-send", "Flow Editor", "No flows found to edit."])
        return

    choice = rofi("Edit flow", flows)
    if not choice:
        print("No flow selected.")
        return

    file_to_edit = FLOW_DIR / choice
    editor = get_editor()

    subprocess.run([editor, str(file_to_edit)])
    print(f"Closed {editor} for {file_to_edit}.")

if __name__ == "__main__":
    main()
