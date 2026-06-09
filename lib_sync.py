"""
Folder sync — scans RECORD/YYYY/YYMM/ folders for new books/movies
and suggests adding them to library.json.

Run: python tools/lib_sync.py
Or via CLI: python tools/lib_cli.py sync
"""
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib_db import _load, _save, get_all, add_entry

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORD_DIR = os.path.join(BASE_DIR, "RECORD")

# Known image extensions
IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".psd", ".psb"}
DOC_EXTS = {".docx", ".doc", ".md", ".txt", ".htm", ".html", ".rp"}
SKIP_FILES = {"thumbs.db", "desktop.ini", ".ds_store"}

# Keywords to ignore when extracting titles
IGNORE_KEYWORDS = [
    "月度", "总结", "展望", "书影音", "读书报告", "句子",
    "屏幕截图", "微信图片", "week", "week16", "week18", "week19",
    "DSC_", "v2-", "s3", "s2", "Postal", "Svg",
]


def _is_ignored(name: str) -> bool:
    """Check if filename should be ignored."""
    name_lower = name.lower()
    for kw in IGNORE_KEYWORDS:
        if kw.lower() in name_lower:
            return True
    return False


def _clean_title(name: str) -> str:
    """Clean up a filename into a plausible book/movie title."""
    # Remove extension
    name = os.path.splitext(name)[0]
    # Remove number suffixes like -1, 01, _1, 0
    name = re.sub(r'[-_][0-9]+$', '', name)
    name = re.sub(r'0[0-9]+$', '', name)
    # Remove trailing digits
    name = re.sub(r'[0-9]+$', '', name)
    # Remove "1" at end (common for cover images)
    if len(name) > 2:
        name = name.rstrip("0123456789")
    return name.strip()


def scan_record_folders() -> list[dict]:
    """
    Scan RECORD/ folder structure and extract potential new entries.
    Returns list of {title_cn, type, date_finished, folder_path}
    """
    if not os.path.exists(RECORD_DIR):
        print(f"RECORD directory not found: {RECORD_DIR}")
        return []

    discoveries = []

    for year_dir in sorted(os.listdir(RECORD_DIR)):
        year_path = os.path.join(RECORD_DIR, year_dir)
        if not os.path.isdir(year_path) or year_dir == "PDF":
            continue

        for month_dir in sorted(os.listdir(year_path)):
            month_path = os.path.join(year_path, month_dir)
            if not os.path.isdir(month_path):
                continue

            # Determine type from subfolder structure
            subdirs = [d for d in os.listdir(month_path)
                       if os.path.isdir(os.path.join(month_path, d))]

            # Look for book subfolders and movie subfolders
            book_dirs = []
            movie_dirs = []

            for sd in subdirs:
                sd_lower = sd.lower()
                if any(kw in sd_lower for kw in ["书", "book"]):
                    # This is a book container — look inside
                    inner = os.path.join(month_path, sd)
                    for item in os.listdir(inner):
                        item_path = os.path.join(inner, item)
                        if os.path.isdir(item_path) and not _is_ignored(item):
                            book_dirs.append((item, item_path))
                elif any(kw in sd_lower for kw in ["影", "电影", "movie"]):
                    inner = os.path.join(month_path, sd)
                    for item in os.listdir(inner):
                        item_path = os.path.join(inner, item)
                        if os.path.isdir(item_path) and not _is_ignored(item):
                            movie_dirs.append((item, item_path))
                else:
                    # Direct book/movie folder
                    if not _is_ignored(sd):
                        # Heuristic: check if contains images -> movie; otherwise book
                        # Most direct subfolders are books in this user's structure
                        if any(ext in sd_lower for ext in [".jpg", ".jpeg", ".png"]):
                            continue  # it's a file, not a folder
                        book_dirs.append((sd, os.path.join(month_path, sd)))

            # Also check for loose files in the month dir (earlier months)
            loose_files = [f for f in os.listdir(month_path)
                           if os.path.isfile(os.path.join(month_path, f))
                           and os.path.splitext(f)[1].lower() in IMG_EXTS
                           and not _is_ignored(f)]

            # Extract unique titles from loose files
            loose_titles = set()
            for f in loose_files:
                title = _clean_title(f)
                if title and len(title) >= 2:
                    loose_titles.add(title)

            # Convert YYMM to YYYY-MM
            date_str = f"20{month_dir[:2]}-{month_dir[2:4]}"

            # Add book directory discoveries
            for title, path in book_dirs:
                clean = _clean_title(title)
                if clean and len(clean) >= 2:
                    discoveries.append({
                        "title_cn": clean,
                        "type": "book",
                        "date_finished": date_str,
                        "folder_path": path,
                    })

            # Add movie directory discoveries
            for title, path in movie_dirs:
                clean = _clean_title(title)
                if clean and len(clean) >= 2:
                    discoveries.append({
                        "title_cn": clean,
                        "type": "movie",
                        "date_finished": date_str,
                        "folder_path": path,
                    })

            # For 2501-style flat months: loose title = book, 影音/* = movie
            if "影音" in subdirs:
                # Loose titles are books
                for title in loose_titles:
                    discoveries.append({
                        "title_cn": title,
                        "type": "book",
                        "date_finished": date_str,
                        "folder_path": month_path,
                    })

    return discoveries


def _fuzzy_match(title: str, existing_titles: set[str]) -> bool:
    """Check if title fuzzy-matches any existing title."""
    title_lower = title.lower()
    if title_lower in existing_titles:
        return True
    # Check substring match (e.g., "霍乱" matches "霍乱时期的爱情")
    for ext in existing_titles:
        if len(title_lower) >= 2 and (title_lower in ext or ext in title_lower):
            return True
    return False


def sync():
    """Scan for new entries and offer to add them."""
    print("Scanning RECORD/ folders for new entries...\n")
    discoveries = scan_record_folders()

    # Get existing titles AND creators for dedup
    existing = get_all()
    existing_titles = set(e.get("title_cn", "").lower() for e in existing)
    existing_creators = set(e.get("creator", "").lower() for e in existing if e.get("creator"))

    # Find truly new ones
    new_items = []
    for d in discoveries:
        title = d["title_cn"]
        title_lower = title.lower()

        # Skip if it looks like an author name (no author's portrait is a book)
        if title_lower in existing_creators:
            continue
        # Skip if it fuzzy-matches an existing title or creator
        if _fuzzy_match(title, existing_titles):
            continue

        new_items.append(d)
        existing_titles.add(title_lower)  # prevent duplicates within new items

    if not new_items:
        print("No new entries found. Everything is already in library.json!")
        return

    print(f"Found {len(new_items)} potential new entries:\n")
    for i, item in enumerate(new_items, 1):
        etype = "📖" if item["type"] == "book" else "🎬"
        print(f"  {i:2d}. {etype} {item['title_cn']} ({item['date_finished']}) — {item['folder_path']}")

    print(f"\nAdd these to library.json? [y/N] ", end="")
    try:
        answer = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = "n"

    if answer != "y":
        print("Skipped.")
        return

    added = 0
    for item in new_items:
        entry = {
            "type": item["type"],
            "title_cn": item["title_cn"],
            "creator": "",
            "date_finished": item["date_finished"],
            "rating": None,
            "tags": [],
            "status": "finished",
            "notes": "",
        }
        result = add_entry(entry)
        print(f"  + Added [{result['id']}] {result['title_cn']}")
        added += 1

    print(f"\nAdded {added} new entries. Run `python tools/lib_cli.py export` to update GUIDE files.")
    print("Tip: Use `python tools/lib_cli.py edit <id> --creator 'Author Name' --tags 'tag1,tag2'` to fill in details.")


if __name__ == "__main__":
    sync()
