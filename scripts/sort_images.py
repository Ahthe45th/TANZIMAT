import os
import cv2

projectfolder = os.path.expanduser('~/Downloads/allscreenshots/')
SEARCH_RESULTS_DIR = os.path.join(projectfolder, "search_results")
ORIGINALS_DIR = os.path.join(projectfolder, "cropped_images")

def prompt_user_and_process_images():
    for filename in os.listdir(SEARCH_RESULTS_DIR):
        if filename.endswith("_result.png"):
            image_path = os.path.join(SEARCH_RESULTS_DIR, filename)

            img = cv2.imread(image_path)

            if img is None:
                print(f"Could not load image: {filename}")
                continue

            cv2.imshow("Review Image", img)
            print(f"Keep original for '{filename}'? (Y to keep): ", end="")

            # Wait for key input (0 = wait indefinitely)
            cv2.waitKey(1000)  # Shows the window briefly

            user_input = input().strip().lower()
            cv2.destroyAllWindows()

            if user_input != 'y':
                original_filename = filename.split("_result.png")[0] + ".jpg"
                original_path = os.path.join(ORIGINALS_DIR, original_filename)
                if os.path.exists(original_path):
                    os.remove(original_path)
                    print(f"Deleted original image: {original_filename}")
                else:
                    print(f"Original image not found: {original_filename}")

if __name__ == "__main__":
    prompt_user_and_process_images()

    # Clean up the directories
    for filename in os.listdir(SEARCH_RESULTS_DIR):
        file_path = os.path.join(SEARCH_RESULTS_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')
    
    input("You must extract the images cuz they gonna be deleted")
    for filename in os.listdir(ORIGINALS_DIR):
        file_path = os.path.join(ORIGINALS_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')
