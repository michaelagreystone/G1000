"""
Granola Transcript Saver
------------------------
Paste a Granola transcript when prompted.
Extracts the date and title from the metadata,
then saves it to: meeting docs/YYYY-MM-DD - Title.md

Granola metadata formats supported:
  - Date: Month DD, YYYY  (e.g. February 17, 2026)
  - Date: MM/DD/YYYY
  - Date: YYYY-MM-DD
  - Title on the first non-empty line
"""

import os
import re
import sys
from datetime import datetime

SAVE_DIR = os.path.join(os.path.dirname(__file__), "meeting docs")


def parse_date(text):
    """Try multiple date formats found in Granola exports."""
    patterns = [
        (r"(\d{4}-\d{2}-\d{2})", "%Y-%m-%d"),
        (r"(\d{1,2}/\d{1,2}/\d{4})", "%m/%d/%Y"),
        (r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})", "%B %d, %Y"),
        (r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\s+\d{4})", "%B %d %Y"),
    ]
    for pattern, fmt in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", "")
            try:
                return datetime.strptime(raw.strip(), fmt.replace(",", "")).strftime("%Y-%m-%d")
            except ValueError:
                continue
    return None


def parse_title(lines):
    """Return the first meaningful line as the title."""
    for line in lines:
        line = line.strip()
        # Skip metadata-looking lines and blank lines
        if not line:
            continue
        if re.match(r"^(date|time|attendees|participants|duration|meeting)[\s:]", line, re.IGNORECASE):
            continue
        # Strip markdown heading markers
        line = re.sub(r"^#+\s*", "", line)
        if line:
            return line
    return "Untitled Meeting"


def sanitize_filename(name):
    """Remove characters not safe for filenames."""
    return re.sub(r'[<>:"/\\|?*]', "", name).strip()


def collect_input():
    """Read multi-line paste from stdin until double Enter."""
    print("Paste Granola transcript below.")
    print("When done, press Enter twice:\n")
    lines = []
    blank_count = 0
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "":
            blank_count += 1
            if blank_count >= 2:
                break
            lines.append(line)
        else:
            blank_count = 0
            lines.append(line)
    return lines


def main():
    # Accept file path as argument or interactive paste
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    else:
        lines = collect_input()

    if not lines:
        print("No content provided.")
        sys.exit(1)

    full_text = "\n".join(lines)

    # Extract date and title
    date_str = parse_date(full_text)
    if not date_str:
        date_str = input("\nCould not detect date. Enter it (YYYY-MM-DD): ").strip()

    title = parse_title(lines)
    print(f"\nDetected title : {title}")
    confirm = input("Use this title? (Enter to confirm, or type a new one): ").strip()
    if confirm:
        title = confirm

    filename = f"{date_str} - {sanitize_filename(title)}.md"
    save_path = os.path.join(SAVE_DIR, filename)

    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    print(f"\nSaved: meeting docs/{filename}")


if __name__ == "__main__":
    main()
