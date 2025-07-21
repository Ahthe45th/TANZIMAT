# Qur'an Polybar Widget

This directory contains scripts for a local verse-by-verse playback tool
for Qur'an memorization controlled via Polybar.

## Files

- `quran_select.py` – prompts for a surah and ayah range and saves the
  selection under `~/.config/quran_widget/state.json`.
- `quran_play.py` – reads the saved range and plays each corresponding
  MP3 file from `~/quran/naseer_qatami/`.
- `metadata.json` – number of verses per surah for basic validation.

## Installation

1. Ensure `mpv` is installed for audio playback.
2. Place the Qur'an MP3 files for Naseer Al Qatami under
   `~/quran/naseer_qatami/` following the naming convention
   `001001.mp3`, `001002.mp3`, ... `114006.mp3`.
3. Copy the scripts from this directory somewhere in your `$PATH` or
   call them directly from Polybar modules.
4. In Polybar, create two modules:

```dosini
[module/quran-select]
type = custom/script
exec = python3 /path/to/quran_select.py
click-left = python3 /path/to/quran_select.py
format-prefix = " "
```

```dosini
[module/quran-play]
type = custom/script
exec = python3 /path/to/quran_play.py
click-left = python3 /path/to/quran_play.py
format-prefix = " "
```

5. Reload Polybar. Use the first widget to set the surah and range, then
   use the second widget to start playback.

## Notes

- Missing audio files are skipped with a warning.
- Edit `DELAY_BETWEEN_VERSES` in `quran_play.py` to control the pause
  between verses.
