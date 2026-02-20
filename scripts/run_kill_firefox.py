#!/usr/bin/env python3
import subprocess
import os
import logging

script_dir = os.path.dirname(os.path.realpath(__file__))
kill_script_path = os.path.join(script_dir, 'kill_firefox.sh')

# --- LOGGING CONFIGURATION ---
LOG_DIR = os.path.join(script_dir, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "run_kill_firefox.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("Starting run_kill_firefox.py script.")
try:
    subprocess.run([kill_script_path], check=True)
    logging.info(f"Successfully executed {kill_script_path}")
except subprocess.CalledProcessError as e:
    logging.error(f"Error executing {kill_script_path}: {e}")
except FileNotFoundError:
    logging.error(f"Script not found: {kill_script_path}")
except Exception as e:
    logging.critical(f"An unexpected error occurred: {e}")
logging.info("run_kill_firefox.py script finished.")
