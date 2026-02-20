
import openai
import sys
from PIL import Image
import base64
import os

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_and_crop_image(image_path):
    """
    Analyzes an image to detect Instagram UI and crops it iteratively.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        sys.exit(1)

    client = openai.OpenAI(api_key=api_key)
    crop_amount_px = 100

    while True:
        print(f"Analyzing image: {image_path}")
        base64_image = encode_image(image_path)

        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Is there any Instagram UI visible in this image? Answer with only 'yes' or 'no'. If yes, also specify which sides need to be cropped to remove the UI. Use a comma-separated list of the words: top, bottom, left, right. For example: 'yes, top, bottom'."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=100,
            )

            analysis = response.choices[0].message.content.strip().lower()
            print(f"OpenAI response: {analysis}")

            if analysis.startswith('no'):
                print("No more UI detected. Cropping complete.")
                break

            if not analysis.startswith('yes'):
                print("Could not determine if UI is present. Stopping.")
                break

            img = Image.open(image_path)
            width, height = img.size
            
            left, top, right, bottom = 0, 0, width, height

            if 'left' in analysis:
                left += crop_amount_px
                print(f"Cropping {crop_amount_px}px from the left.")
            if 'top' in analysis:
                top += crop_amount_px
                print(f"Cropping {crop_amount_px}px from the top.")
            if 'right' in analysis:
                right -= crop_amount_px
                print(f"Cropping {crop_amount_px}px from the right.")
            if 'bottom' in analysis:
                bottom -= crop_amount_px
                print(f"Cropping {crop_amount_px}px from the bottom.")

            # Prevent invalid crop box
            if left >= right or top >= bottom:
                print("Error: Crop dimensions are invalid. The image might be too small or the crop amount too large. Stopping.")
                break

            cropped_img = img.crop((left, top, right, bottom))
            cropped_img.save(image_path)
            print(f"Image cropped and saved as {image_path}")

        except Exception as e:
            print(f"An error occurred: {e}")
            break

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python autocrop_instagram.py <path_to_screenshot>")
        sys.exit(1)

    screenshot_path = sys.argv[1]
    if not os.path.exists(screenshot_path):
        print(f"Error: File not found at {screenshot_path}")
        sys.exit(1)
    
    analyze_and_crop_image(screenshot_path)
