#!/usr/bin/env python3
import requests
import os
from pathlib import Path

# --- CONFIGURATION ---
LIST_URL = "https://n8n.tuongeechat.com/webhook/9a228570-f01c-44a2-aeaa-c537b1861d0e"
DOWNLOAD_URL_TEMPLATE = "https://n8n.tuongeechat.com/webhook/ce2eebb0-169c-4115-9bf3-663cb5464a28?id={id}"
FINAL_URL = "https://n8n.tuongeechat.com/webhook/96130e15-47bf-4659-96e6-d555b8b96c10"
DOWNLOAD_DIR = Path.home() / "Documents" / "webhook_downloads"

# --- SCRIPT ---

def main():
    """
    Main function to download files from the webhook.
    """
    print("Starting file download process...")

    # Create download directory if it doesn't exist
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    print(f"Download directory: {DOWNLOAD_DIR}")

    try:
        # Get the list of items
        print(f"Fetching item list from {LIST_URL}...")
        list_response = requests.get(LIST_URL)
        list_response.raise_for_status()  # Raise an exception for bad status codes
        items = list_response.json()
        print(f"Found {len(items)} items to download.")

        # Download each item
        for item in items:
            item_id = item.get("id")
            item_name = item.get("name", item_id) # Use name for filename, fallback to id
            if not item_id:
                print("Skipping item with no id.")
                continue

            download_url = DOWNLOAD_URL_TEMPLATE.format(id=item_id)
            file_path = DOWNLOAD_DIR / f"{item_name}" # You might want to adjust the extension

            print(f"Downloading {item_name} from {download_url}...")
            download_response = requests.get(download_url)
            download_response.raise_for_status()

            with open(file_path, "wb") as f:
                f.write(download_response.content)
            print(f"Saved file to {file_path}")

        # Call the final webhook
        print(f"Calling final webhook at {FINAL_URL}...")
        final_response = requests.get(FINAL_URL)
        final_response.raise_for_status()
        print("Final webhook called successfully.")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during a network request: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    print("File download process finished.")

if __name__ == "__main__":
    main()
