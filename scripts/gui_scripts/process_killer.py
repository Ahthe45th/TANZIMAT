
import os
import time
import subprocess

LOCK_FILE = "/tmp/.tanzimat_mpv_zen_lock"
PROCESSES_TO_KILL = ["mpv", "zen"]
CHECK_INTERVAL = 2 # seconds

def kill_processes():
    for proc_name in PROCESSES_TO_KILL:
        try:
            # Use pkill to terminate processes by name
            # -f: match against the full command line
            subprocess.run(["pkill", "-f", proc_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Killed {proc_name} processes.")
        except subprocess.CalledProcessError as e:
            # pkill returns 1 if no processes are found, which is fine
            if "no processes killed" not in e.stderr.decode():
                print(f"Error killing {proc_name}: {e}")
        except FileNotFoundError:
            print(f"pkill command not found. Cannot kill {proc_name} processes.")
            break # Exit if pkill is not available

if __name__ == "__main__":
    print("Process killer started. Monitoring for lock file...")
    while os.path.exists(LOCK_FILE):
        kill_processes()
        time.sleep(CHECK_INTERVAL)
    print("Lock file not found. Process killer exiting.")
