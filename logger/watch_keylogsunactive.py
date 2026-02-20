#!/usr/bin/env python3
import json, os, re, sys, time, subprocess, unicodedata
from collections import deque

CONFIG_PATH = sys.argv[1] if len(sys.argv) > 1 else "/etc/watch_keylogs.json"

TOKEN_RE = re.compile(r"<([^>]+)>")
# Tokens to ignore completely (navigation etc.)
IGNORE_TOKENS = {
    "up","down","left","right","home","end","pgup","pgdn",
    "insert","delete","tab","caps","shift","lshift","rshift",
    "ctrl","lctrl","rctrl","alt","lalt","ralt","meta","super",
    "esc","escape","menu","compose"
}

def strip_diacritics(s: str) -> str:
    # NFKD then remove combining marks
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))

def norm_text(s: str) -> str:
    # Casefold, strip diacritics, collapse whitespace
    s = strip_diacritics(s.casefold())
    return re.sub(r"\s+", " ", s)

def load_config(path):
    with open(path, "r") as f:
        cfg = json.load(f)
    cfg.setdefault("logfile", os.path.expanduser("~/logkeys.log"))
    cfg.setdefault("clear_on_enter", True)
    cfg.setdefault("debounce_sec", 2)
    cfg.setdefault("time_window_sec", 5)   # require phrase typed within N seconds
    cfg.setdefault("rules", [])
    for r in cfg["rules"]:
        r.setdefault("icase", True)
        r.setdefault("whole_word", False)
        flags = re.IGNORECASE if r.get("icase") else 0
        if "regex" in r:
            r["_rx_raw"] = re.compile(r["regex"], flags)
        elif "match" in r:
            patt = r["match"]
            if r["whole_word"]:
                patt = r"\b" + re.escape(patt) + r"\b"
            else:
                patt = re.escape(patt)
            r["_rx_raw"] = re.compile(patt, flags)
        else:
            raise ValueError("Rule must have 'match' or 'regex'")
        if "command" not in r or not isinstance(r["command"], list):
            raise ValueError("Rule must have 'command' as a list")
        # Precompute a normalized pattern to search in normalized text
        r["_rx_norm"] = re.compile(norm_text(r["_rx_raw"].pattern), re.IGNORECASE)
    return cfg

def tail_f(path):
    with open(path, "r", errors="ignore") as f:
        f.seek(0, os.SEEK_END)
        while True:
            data = f.read()
            if not data:
                time.sleep(0.1)
                continue
            yield data

def main():
    cfg = load_config(CONFIG_PATH)
    logfile = cfg["logfile"]
    clear_on_enter = cfg["clear_on_enter"]
    debounce_sec = float(cfg["debounce_sec"])
    time_window = float(cfg["time_window_sec"])
    rules = cfg["rules"]

    # Rolling buffers: raw chars and timestamps to enforce time window
    buf = deque(maxlen=4096)
    tbuf = deque(maxlen=4096)
    last_exec = 0.0

    def push_char(c):
        buf.append(c)
        tbuf.append(time.time())

    def apply_bksp(n=1):
        for _ in range(n):
            if buf:
                buf.pop()
                tbuf.pop()

    def clear_buf():
        buf.clear(); tbuf.clear()

    def text_in_window():
        """Return normalized text consisting of chars typed within time_window seconds."""
        now = time.time()
        # Keep only recent chars
        i = len(tbuf) - 1
        while i >= 0 and now - tbuf[i] <= time_window:
            i -= 1
        # take chars from i+1..end
        recent = "".join(list(buf)[i+1:])
        return norm_text(recent)

    print(f"[watch_keys] watching {logfile} with {len(rules)} rule(s)")
    for chunk in tail_f(logfile):
        i = 0
        fired = None
        while i < len(chunk):
            if chunk[i] == "<":
                m = TOKEN_RE.match(chunk, i)
                if m:
                    token = m.group(1).lower()
                    # normalize aliases like <BckSp> -> "bcksp"
                    token = re.sub(r'[^a-z]', '', token)
                    if token.startswith("bcksp"):
                        apply_bksp(1)
                    elif token in IGNORE_TOKENS:
                        pass  # ignore navigation and non-text tokens
                    elif token.startswith("enter"):
                        # On Enter, evaluate windowed text, then optionally clear
                        recent_norm = text_in_window()
                        for r in rules:
                            if r["_rx_norm"].search(recent_norm):
                                fired = r; break
                        if clear_on_enter:
                            clear_buf()
                    # else: ignore other tokens
                    i = m.end()
                    if fired: break
                    continue
            # Accept only printable characters; drop control chars
            c = chunk[i]
            if c.isprintable():
                push_char(c)
                recent_norm = text_in_window()
                for r in rules:
                    if r["_rx_norm"].search(recent_norm):
                        fired = r; break
                if fired: 
                    break
            i += 1

        if fired:
            now = time.time()
            if now - last_exec >= debounce_sec:
                print(f"[watch_keys] matched -> executing: {' '.join(fired['command'])}")
                try:
                    subprocess.Popen(fired["command"])
                except Exception as e:
                    print(f"[watch_keys] exec failed: {e}", file=sys.stderr)
                last_exec = now
            else:
                print("[watch_keys] debounced trigger")
            clear_buf()  # avoid repeats on the same text

if __name__ == "__main__":
    main()
