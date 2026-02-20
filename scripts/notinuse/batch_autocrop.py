
import os
import subprocess
import shutil
import sys

def batch_crop_images():
    """
    Runs the autocrop_instagram.py script on all images in a source
    directory and saves the results to a destination directory.
    """
    home_dir = os.path.expanduser("~")
    
    source_dir = os.path.join(home_dir, "Downloads", "allscreenshots", "screenshots")
    dest_dir = os.path.join(home_dir, "Downloads", "allscreenshots", "cropped_ai")
    script_path = os.path.join(home_dir, "Proyectos", "TANZIMAT", "scripts", "autocrop_instagram.py")

    # Create destination directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)
    print(f"Destination directory '{dest_dir}' is ready.")

    if not os.path.exists(script_path):
        print(f"Error: The autocrop script was not found at '{script_path}'")
        sys.exit(1)

    try:
        filenames = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
    except FileNotFoundError:
        print(f"Error: Source directory '{source_dir}' not found.")
        sys.exit(1)

    if not filenames:
        print(f"No files found in '{source_dir}'.")
        return

    print(f"Found {len(filenames)} files to process.")

    for filename in filenames:
        source_path = os.path.join(source_dir, filename)
        dest_path = os.path.join(dest_dir, filename)

        print(f"--- Processing {filename} ---")

        # Copy the file to the destination directory first
        try:
            shutil.copy2(source_path, dest_path)
            print(f"Copied '{filename}' to '{dest_dir}'.")
        except Exception as e:
            print(f"Error copying '{filename}': {e}")
            continue # Skip to the next file

        # Now, run the cropping script on the file in the destination directory
        try:
            command = ["python", script_path, dest_path]
            print(f"Running autocrop script on '{dest_path}'...")
            
            result = subprocess.run(
                command, 
                check=True, 
                capture_output=True, 
                text=True,
                timeout=300 # 5 minute timeout per image
            )
            print(f"Successfully processed '{filename}'.")
            # To see the full output for every successful run, uncomment the line below
            # print(result.stdout)

        except subprocess.CalledProcessError as e:
            print(f"ERROR: Autocrop script failed for '{filename}'.")
            print("STDOUT:")
            print(e.stdout)
            print("STDERR:")
            print(e.stderr)
        except subprocess.TimeoutExpired:
            print(f"ERROR: Script timed out for '{filename}'. The process took too long.")
        except Exception as e:
            print(f"An unexpected error occurred while processing '{filename}': {e}")
        
        print(f"--- Finished {filename} ---
")

if __name__ == "__main__":
    batch_crop_images()
