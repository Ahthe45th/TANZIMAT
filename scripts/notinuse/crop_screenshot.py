import cv2
import numpy as np
import os
import logging

# --- LOGGING CONFIGURATION ---
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "crop_screenshot.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def crop_instagram_photo_only(image_path, output_path, debug=False):
    logging.info(f"Starting crop_instagram_photo_only for {image_path}")
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        logging.error(f"Image not found at {image_path}")
        raise FileNotFoundError("Image not found.")

    height, width = img.shape[:2]
    logging.info(f"Original image size: {width}x{height}")

    # Step 1: Manually crop content section (tuned for portrait post layout)
    top = int(height * 0.20)
    bottom = int(height * 0.75)
    cropped = img[top:bottom, :]
    logging.info(f"Cropped image to rows {top} to {bottom}")

    # Step 2: Remove bottom white bar if any (e.g., caption or background)
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY)
    row_sums = (255 - thresh).sum(axis=1)

    last_content_row = len(row_sums) - next((i for i, val in enumerate(reversed(row_sums)) if val > 1000), 0)
    clean_cropped = cropped[:last_content_row, :]
    logging.info(f"Trimmed bottom to row: {last_content_row}")

    # Save final output
    try:
        cv2.imwrite(output_path, clean_cropped)
        logging.info(f"Saved cropped image to {output_path}")
    except Exception as e:
        logging.error(f"Error saving cropped image to {output_path}: {e}")
        raise

    if debug:
        logging.info(f"Original size: {img.shape}")
        logging.info(f"Cropped area: rows {top} to {bottom}")
        logging.info(f"Trimmed bottom to row: {last_content_row}")
    
    logging.info("Finished crop_instagram_photo_only.")
    return clean_cropped

# Example usage
if __name__ == "__main__":
    input_image = "input.jpeg"             # replace with your file
    output_image = "final_photo_only.png"
    try:
        crop_instagram_photo_only(input_image, output_image, debug=True)
    except Exception as e:
        logging.critical(f"Script failed: {e}")
