# TANZIMAT

Collection of automation scripts used for various daily tasks.

## YouTube Watchlist

`scripts/youtube_watchlist.py` checks a list of channels in `scripts/channels.txt`.
If any videos were uploaded in the last 24 hours and are not listed in
`scripts/downloaded_videos.txt`, they are downloaded using `yt-dlp` at 360p to
`~/yt-watchlist/`.

Run the script manually or via cron:

```bash
python3 scripts/youtube_watchlist.py
```

Ensure `yt-dlp` is installed and network access is available.

## Qur'an Polybar Widget

See `quran_widget/README.md
**NOTE**: If you move `programstarter.bash` or `programs.txt`, you must update the path in `~/.config/bspwm/bspwmrc` accordingly.
` for a local verse-by-verse playback tool
aimed at memorization and review.