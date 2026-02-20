
import subprocess
import os

def add_prayer_reminders():
    # Get prayer times
    try:
        prayer_times_output = subprocess.check_output(["python", "/home/mehmet/Proyectos/TANZIMAT/scripts/get_prayer_times.py", "--city", "Nairobi", "--country", "Kenya"], text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error getting prayer times: {e}")
        return

    prayer_times = {}
    for line in prayer_times_output.strip().split('\n')[1:]:
        if ":" in line:
            parts = line.split(":", 1)
            print(parts)
            prayer_times[parts[0].strip()] = f"{parts[1].strip().split(':')[0].strip()}:{int(parts[1].strip().split(':')[1])-5}"

    prayers_to_add = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    for prayer in prayers_to_add:
        if prayer in prayer_times:
            prayer_time = prayer_times[prayer]
            label = f"{prayer} Prayer"
            try:
                subprocess.run(["python", "/home/mehmet/Proyectos/TANZIMAT/scripts/add_reminder.py", 
                                "--time", prayer_time, 
                                "--file", "/home/mehmet/Proyectos/TANZIMAT/prayer_reminder.md", 
                                "--label", label, 
                                "--days", "0", "1", "2", "3", "4", "5", "6",
                                "--post-command", "/home/mehmet/miniconda3/envs/idris/bin/python /home/mehmet/Proyectos/TANZIMAT/scripts/recite_surah.py"], 
                               check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error adding reminder for {prayer}: {e}")

if __name__ == "__main__":
    try:
        add_prayer_reminders()
        subprocess.run(["bash", "-c", "DISPLAY=:1 notify-send 'Prayer Reminders Added' 'The prayer reminders have been successfully added.'"])
    except Exception as e:
        subprocess.run(["bash", "-c", f"DISPLAY=:1 notify-send 'Error Adding Prayer Reminders' '{e}'"])


