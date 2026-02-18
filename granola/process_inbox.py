"""
Granola Inbox Processor
-----------------------
1. Drop any Granola .txt (or .md) export into granola/inbox/
2. Run this script: python granola/process_inbox.py
3. Files are saved to: granola/meeting docs/YYYY-MM-DD - Title.md
4. Inbox is cleared automatically
"""

import os
import re
import shutil
from datetime import datetime

BASE_DIR    = os.path.dirname(__file__)
INBOX_DIR   = os.path.join(BASE_DIR, "inbox")
SAVE_DIR    = os.path.join(BASE_DIR, "meeting docs")


# ── Date parsing ─────────────────────────────────────────────────────────────

DATE_PATTERNS = [
    (r"\b(\d{4}-\d{2}-\d{2})\b",                                                          "%Y-%m-%d"),
    (r"\b(\d{1,2}/\d{1,2}/\d{4})\b",                                                      "%m/%d/%Y"),
    (r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b", None),
    (r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})\b",   None),
]

MONTH_FMTS = ["%B %d %Y", "%b %d %Y", "%B %d, %Y", "%b %d, %Y",
              "%d %B %Y", "%d %b %Y"]


def parse_date(text):
    for pattern, fmt in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        raw = re.sub(r",", "", match.group(1)).strip()
        if fmt:
            try:
                return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        else:
            for f in MONTH_FMTS:
                try:
                    return datetime.strptime(raw, f).strftime("%Y-%m-%d")
                except ValueError:
                    continue
    return None


# ── Title parsing ─────────────────────────────────────────────────────────────

SKIP_PREFIXES = re.compile(
    r"^(date|time|attendees|participants|duration|location|meeting|from|to|subject)[\s:]",
    re.IGNORECASE,
)


def parse_title(lines):
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if SKIP_PREFIXES.match(line):
            continue
        # Strip markdown headings
        line = re.sub(r"^#+\s*", "", line)
        # Skip lines that are purely a date/time stamp
        if parse_date(line) and len(line) < 30:
            continue
        if line:
            return line
    return "Untitled Meeting"


# ── Filename helpers ──────────────────────────────────────────────────────────

def sanitize(name):
    return re.sub(r'[<>:"/\\|?*]', "", name).strip()


def unique_path(directory, filename):
    base, ext = os.path.splitext(filename)
    path = os.path.join(directory, filename)
    counter = 1
    while os.path.exists(path):
        path = os.path.join(directory, f"{base} ({counter}){ext}")
        counter += 1
    return path


# ── Main ──────────────────────────────────────────────────────────────────────

def process_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    lines = content.splitlines()

    date_str = parse_date(content)
    title    = parse_title(lines)

    if not date_str:
        print(f"  [!] Could not detect date in: {os.path.basename(filepath)}")
        date_str = input("      Enter date manually (YYYY-MM-DD): ").strip()

    print(f"  Date  : {date_str}")
    print(f"  Title : {title}")
    confirm = input("  Use this title? (Enter to confirm, or type a new one): ").strip()
    if confirm:
        title = confirm

    filename  = f"{date_str} - {sanitize(title)}.md"
    save_path = unique_path(SAVE_DIR, filename)

    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(content)

    return save_path


def main():
    files = [
        f for f in os.listdir(INBOX_DIR)
        if f.lower().endswith((".txt", ".md")) and not f.startswith(".")
    ]

    if not files:
        print("Inbox is empty. Drop a Granola .txt export into granola/inbox/ and run again.")
        return

    print(f"Found {len(files)} file(s) in inbox:\n")

    saved = []
    for fname in files:
        filepath = os.path.join(INBOX_DIR, fname)
        print(f"Processing: {fname}")
        save_path = process_file(filepath)
        saved.append((filepath, save_path))
        print(f"  Saved -> meeting docs/{os.path.basename(save_path)}\n")

    # Clear processed files from inbox
    for src, _ in saved:
        os.remove(src)

    print(f"Done. {len(saved)} transcript(s) saved. Inbox cleared.")


if __name__ == "__main__":
    main()
