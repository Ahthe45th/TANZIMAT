
import subprocess
import os

# Path to the display_reminder.py script
DISPLAY_SCRIPT = "/home/mehmet/Proyectos/TANZIMAT/display_reminder.py"
TEST_MESSAGE = "This is a test reminder."

def main():
    print("Testing display_reminder.py...")
    try:
        # Call the graphical display script with a test message
        result = subprocess.run(["python3", DISPLAY_SCRIPT, TEST_MESSAGE], capture_output=True, text=True)

        if result.returncode == 0:
            print("Test successful: Reminder was acknowledged.")
        else:
            print(f"Test failed: Script exited with code {result.returncode}.")
            print(f"Stderr: {result.stderr}")

    except FileNotFoundError:
        print(f"Error: The script '{DISPLAY_SCRIPT}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
