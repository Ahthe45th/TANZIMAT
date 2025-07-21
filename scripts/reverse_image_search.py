import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

projectfolder = os.path.expanduser('~/Downloads/allscreenshots/')
# --- CONFIGURATION ---
INPUT_FOLDER = os.path.join(projectfolder, "cropped_images")
OUTPUT_FOLDER = os.path.join(projectfolder, "search_results")
WAIT_TIME = 10  # seconds

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# --- CHROME/CHROMIUM OPTIONS ---
chrome_options = Options()
# Leave visible so you can solve CAPTCHA manually
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1280,960")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-background-networking")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-sync")
chrome_options.add_argument("--disable-translate")
chrome_options.binary_location = "/usr/bin/chromium"  # Adjust if needed

# --- MANUALLY INSTALLED CHROMEDRIVER ---
driver = webdriver.Chrome(
    service=Service("/usr/local/bin/chromedriver"),
    options=chrome_options
)

wait = WebDriverWait(driver, WAIT_TIME)

# --- MAIN FUNCTION ---
def reverse_image_search(image_path, output_path):
    try:
        # Step 1: Open Google Lens upload page
        driver.get("https://lens.google.com/upload")
        time.sleep(2)

        # Step 2: Check for CAPTCHA or block page
        page_text = driver.page_source.lower()
        current_url = driver.current_url.lower()

        if (
            "recaptcha" in page_text
            or "verify you are human" in page_text
            or "sorry/index" in current_url
            or "sorry" in current_url
        ):
            print("⚠️ CAPTCHA or block page detected.")
            input("👉 Please solve the CAPTCHA in the browser. Press ENTER once done to continue...")

        # Step 3: Upload image
        upload_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='file']")))
        upload_input.send_keys(os.path.abspath(image_path))
        print("Sent image")

        page_text = driver.page_source.lower()
        current_url = driver.current_url.lower()

        if (
            "recaptcha" in page_text
            or "verify you are human" in page_text
            or "sorry/index" in current_url
            or "sorry" in current_url
        ):
            print("⚠️ CAPTCHA or block page detected.")
            input("👉 Please solve the CAPTCHA in the browser. Press ENTER once done to continue...")
        # Step 4: Wait for canvas result
        print("Waiting for canvas")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "canvas")))

        page_text = driver.page_source.lower()
        current_url = driver.current_url.lower()

        if (
            "recaptcha" in page_text
            or "verify you are human" in page_text
            or "sorry/index" in current_url
            or "sorry" in current_url
        ):
            print("⚠️ CAPTCHA or block page detected.")
            input("👉 Please solve the CAPTCHA in the browser. Press ENTER once done to continue...")

        print("Sleeping")
        time.sleep(3)  # Allow time to fully render

        page_text = driver.page_source.lower()
        current_url = driver.current_url.lower()

        if (
            "recaptcha" in page_text
            or "verify you are human" in page_text
            or "sorry/index" in current_url
            or "sorry" in current_url
        ):
            print("⚠️ CAPTCHA or block page detected.")
            input("👉 Please solve the CAPTCHA in the browser. Press ENTER once done to continue...")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "canvas")))         
        time.sleep(10)  # Allow time to fully render
        driver.execute_script("window.scrollBy(0, 50);")  # scrolls down 300px
        time.sleep(2)
        driver.execute_script("window.scrollBy(0, 50);")
        # Step 5: Screenshot and save
        driver.save_screenshot(output_path)
        print(f"✅ Saved: {os.path.basename(output_path)}")

    except Exception as e:
        print(f"❌ Error with {os.path.basename(image_path)}: {e}")

# --- BATCH PROCESS ALL IMAGES ---
for filename in os.listdir(INPUT_FOLDER):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        in_path = os.path.join(INPUT_FOLDER, filename)
        out_path = os.path.join(OUTPUT_FOLDER, f"{os.path.splitext(filename)[0]}_result.png")
        reverse_image_search(in_path, out_path)

driver.quit()
print("✅ Done. All images processed.")
