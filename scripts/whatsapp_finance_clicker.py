import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- Configuration ---
# Expand the '~' to the user's actual home directory
PROFILE_PATH = os.path.expanduser('~/.mozilla/firefox/7cnhxgsr.WHATSAPP')
URL = 'https://web.whatsapp.com'
TARGET_TEXT = 'FINANCES REPORTS'
# Wait time for the element to appear (gives you time to scan QR code)
WAIT_FOR_ELEMENT_TIMEOUT = 120

def main():
    """
    Opens WhatsApp Web with a specific Firefox profile, waits for a
    specific chat/group to be visible, and clicks on it.
    """
    if not os.path.isdir(PROFILE_PATH):
        print(f"Error: Firefox profile not found at '{PROFILE_PATH}'")
        print("Please ensure the path is correct.")
        return

    print("Initializing Firefox WebDriver with the specified profile...")
    options = Options()
    options.profile = PROFILE_PATH

    # Using a try...finally block to ensure the browser is always closed
    driver = None
    try:
        driver = webdriver.Firefox(options=options)
        
        print(f"Navigating to {URL}...")
        driver.get(URL)

        print("-----------------------------------------------------------")
        print("Please scan the QR code if you are not already logged in.")
        print(f"Waiting for an element with text '{TARGET_TEXT}' to appear...")
        print(f"Timeout is set to {WAIT_FOR_ELEMENT_TIMEOUT} seconds.")
        print("-----------------------------------------------------------")

        # Use WebDriverWait for a more robust wait than a simple time.sleep()
        wait = WebDriverWait(driver, WAIT_FOR_ELEMENT_TIMEOUT)
        
        # Using XPath to find any element that contains the target text.
        # This is flexible if the tag is a span, div, etc.
        target_element_locator = (By.XPATH, f"//*[contains(text(), '{TARGET_TEXT}')]")
        
        # Wait until the element is present, visible, and clickable
        target_element = wait.until(EC.element_to_be_clickable(target_element_locator))
        
        print("Element found! Clicking now...")
        target_element.click()
        
        print(f"Successfully clicked on '{TARGET_TEXT}'.")
        print("The browser will remain open for 20 seconds to show the result.")
        time.sleep(20)

    except TimeoutException:
        print(f"\nError: Timed out after {WAIT_FOR_ELEMENT_TIMEOUT} seconds.")
        print(f"Could not find a clickable element with the text: '{TARGET_TEXT}'.")
        print("Please ensure you are logged in and the chat/group is visible on the screen.")
        print("Keeping the browser open for 60 seconds for manual inspection.")
        time.sleep(60)
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Keep browser open for a bit for debugging
        time.sleep(30)

    finally:
        if driver:
            print("Closing the browser.")
            driver.quit()

if __name__ == "__main__":
    main()
