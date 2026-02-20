
import os
import subprocess

def get_video_duration(filepath):
    """Gets the duration of a video file in seconds."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        filepath,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def remove_short_videos(directory, max_duration_seconds=60):
    """Removes videos in a directory that are shorter than a specified duration."""
    for filename in os.listdir(directory):
        if filename.endswith(".mp4"):
            filepath = os.path.join(directory, filename)
            duration = get_video_duration(filepath)
            if duration is not None and duration < max_duration_seconds:
                print(f"Removing {filename} (duration: {duration:.2f}s)")
                os.remove(filepath)

if __name__ == "__main__":
    remove_short_videos("/home/mehmet/yt-watchlist")
