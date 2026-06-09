"""
Library database module — reads/writes library.json, provides CRUD and query API.
"""
import json
import os
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.json")

# Preset mood tags for emotional response tracking
PRESET_MOODS = [
    "震撼", "温暖", "忧伤", "共鸣", "被看见",
    "绝望", "治愈", "愤怒", "平静", "惆怅",
    "启发", "困惑", "兴奋", "怀念", "深思",
]


def _load() -> dict:
    """Load the full database from disk."""
    if not os.path.exists(DB_PATH):
        return {"version": 1, "entries": []}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(db: dict) -> None:
    """Save the database to disk."""
    db["updated_at"] = datetime.now().isoformat()
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def get_all(type_filter: Optional[str] = None,
            status_filter: Optional[str] = None,
            tag_filter: Optional[str] = None,
            sort_by: str = "date_finished",
            reverse: bool = True) -> list[dict]:
    """Get all entries, optionally filtered and sorted."""

    db = _load()
    entries = db.get("entries", [])

    if type_filter:
        entries = [e for e in entries if e.get("type") == type_filter]
    if status_filter:
        entries = [e for e in entries if e.get("status") == status_filter]
    if tag_filter:
        entries = [e for e in entries if tag_filter in e.get("tags", [])]

    # Sort — handle None values gracefully
    def sort_key(e):
        val = e.get(sort_by, "")
        return val if val is not None else ""

    entries.sort(key=sort_key, reverse=reverse)
    return entries


def get_by_id(entry_id: str) -> Optional[dict]:
    """Get a single entry by its ID."""
    db = _load()
    for e in db.get("entries", []):
        if e.get("id") == entry_id:
            return e
    return None


def add_entry(entry: dict) -> dict:
    """Add a new entry. Returns the added entry with generated id."""
    db = _load()
    entry["id"] = str(uuid.uuid4())[:8]
    entry["created_at"] = datetime.now().isoformat()
    entry.setdefault("type", "book")
    entry.setdefault("status", "finished")
    entry.setdefault("rating", None)
    entry.setdefault("tags", [])
    entry.setdefault("notes", "")
    entry.setdefault("title_orig", "")
    entry.setdefault("creator_orig", "")
    entry.setdefault("cover_image", "")
    entry.setdefault("source", "")
    entry.setdefault("date_finished", datetime.now().strftime("%Y-%m"))
    # New fields for journal + reading experience
    entry.setdefault("date_started", "")
    entry.setdefault("mood_tags", [])
    entry.setdefault("extracts", [])
    entry.setdefault("reread_count", 0)
    entry.setdefault("reading_time_days", None)
    entry.setdefault("format", "纸质书")
    entry.setdefault("daily_reading", [])
    entry.setdefault("cover_url", "")
    entry.setdefault("active_session", None)
    entry.setdefault("sessions", [])

    db.setdefault("entries", []).append(entry)
    _save(db)
    return entry


def update_entry(entry_id: str, updates: dict) -> Optional[dict]:
    """Update fields of an existing entry. Returns the updated entry or None."""
    db = _load()
    for e in db.get("entries", []):
        if e.get("id") == entry_id:
            e.update(updates)
            e["updated_at"] = datetime.now().isoformat()
            _save(db)
            return e
    return None


def delete_entry(entry_id: str) -> bool:
    """Delete an entry by ID. Returns True if deleted."""
    db = _load()
    entries = db.get("entries", [])
    new_entries = [e for e in entries if e.get("id") != entry_id]
    if len(new_entries) != len(entries):
        db["entries"] = new_entries
        _save(db)
        return True
    return False


def search(query: str) -> list[dict]:
    """Full-text search across titles, creators, tags, and notes."""
    db = _load()
    q = query.lower()
    results = []
    for e in db.get("entries", []):
        searchable = " ".join([
            e.get("title_cn", ""),
            e.get("title_orig", ""),
            e.get("creator", ""),
            e.get("creator_orig", ""),
            " ".join(e.get("tags", [])),
            e.get("notes", ""),
        ]).lower()
        if q in searchable:
            results.append(e)
    return results


def get_all_tags() -> dict[str, int]:
    """Get all tags with their usage counts."""
    db = _load()
    tag_counts = {}
    for e in db.get("entries", []):
        for tag in e.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    return dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True))


def get_stats() -> dict:
    """Get summary statistics."""
    db = _load()
    entries = db.get("entries", [])
    books = [e for e in entries if e.get("type") == "book" and e.get("status") == "finished"]
    movies = [e for e in entries if e.get("type") == "movie" and e.get("status") == "finished"]
    currently_reading = [e for e in entries if e.get("status") == "reading"]

    rated_books = [e for e in books if e.get("rating") is not None]
    rated_movies = [e for e in movies if e.get("rating") is not None]

    return {
        "total_entries": len(entries),
        "books_finished": len(books),
        "movies_finished": len(movies),
        "currently_reading": len(currently_reading),
        "avg_book_rating": round(sum(e["rating"] for e in rated_books) / len(rated_books), 1) if rated_books else None,
        "avg_movie_rating": round(sum(e["rating"] for e in rated_movies) / len(rated_movies), 1) if rated_movies else None,
        "top_tags": list(get_all_tags().items())[:10],
        "entries_this_year": len([e for e in entries
                                  if e.get("date_finished", "").startswith(datetime.now().strftime("%Y"))]),
    }


def get_entries_for_journal(type_filter: str = "book") -> dict:
    """Return entries grouped by month for the journal timeline.
    Returns: { "YYYY-MM": [entries], "months_order": ["YYYY-MM", ...] }
    Only returns finished entries with date_finished.
    """
    entries = get_all(type_filter=type_filter, status_filter="finished", sort_by="date_finished", reverse=True)
    entries = [e for e in entries if e.get("date_finished")]

    grouped = defaultdict(list)
    for e in entries:
        month = e["date_finished"][:7]  # "YYYY-MM"
        grouped[month].append(e)

    months_order = sorted(grouped.keys(), reverse=True)
    return {"groups": dict(grouped), "months_order": months_order, "total": len(entries)}


def get_viz_data(year: Optional[str] = None) -> dict:
    """Return aggregated data for all visualization charts.
    If year is None, returns all-time data.
    """
    if year is None:
        year = datetime.now().strftime("%Y")

    entries = _load().get("entries", [])
    finished = [e for e in entries if e.get("status") == "finished"]

    # Filter by year if specified
    year_entries = [e for e in finished if e.get("date_finished", "").startswith(year)]

    # Calendar heatmap data: aggregate daily reading minutes across all entries
    date_minutes = defaultdict(int)
    # From daily_reading records (reading time in minutes)
    for e in finished:
        for dr in e.get("daily_reading", []):
            d = dr.get("date", "")
            if d and d.startswith(year):
                date_minutes[d[:10]] += dr.get("minutes", 0)
    # From date_finished (book-completion days, at least 1 unit to show)
    date_books = defaultdict(int)
    for e in year_entries:
        df = e.get("date_finished", "")
        if len(df) == 7:
            df = df + "-01"
        if df and len(df) >= 10:
            date_books[df[:10]] += 1

    # Merge: prefer minutes, fall back to book count as visual marker
    all_dates = set(date_minutes.keys()) | set(date_books.keys())
    calendar_data = []
    for d in sorted(all_dates):
        val = date_minutes.get(d, 0) or date_books.get(d, 0)
        calendar_data.append([d, val])

    # Monthly trend: books per month, movies per month, cumulative
    monthly_data = defaultdict(lambda: {"book": 0, "movie": 0, "music": 0})
    for e in finished:
        df = e.get("date_finished", "")
        if len(df) >= 7:
            month = df[:7]
            etype = e.get("type", "book")
            if etype in monthly_data[month]:
                monthly_data[month][etype] += 1

    sorted_months = sorted(monthly_data.keys())
    monthly_trend = []
    cum_total = 0
    for m in sorted_months:
        d = monthly_data[m]
        cum_total += d["book"] + d["movie"] + d["music"]
        monthly_trend.append({
            "month": m,
            "books": d["book"],
            "movies": d["movie"],
            "music": d["music"],
            "total_month": d["book"] + d["movie"] + d["music"],
            "cumulative": cum_total,
        })

    # Tag counts for radar/pie
    tag_counts = defaultdict(int)
    for e in finished:
        for t in e.get("tags", []):
            tag_counts[t] += 1
    top_tags = dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10])

    # Rose chart category groups — map raw tags to broad categories
    TAG_CATEGORIES = {
        "文学小说": ["文学", "小说", "中短篇小说", "长篇", "魔幻现实", "讽刺", "成长", "爱情", "城市", "流亡", "反乌托邦"],
        "诗歌戏剧": ["诗歌", "戏剧", "短歌"],
        "思想哲学": ["哲学", "社会学", "美学", "政治", "存在主义", "心理学"],
        "女性书写": ["女性主义", "女性", "性别"],
        "科幻奇幻": ["科幻", "奇幻", "幻想", "赛博朋克", "反乌托邦"],
        "历史传记": ["历史", "中国历史", "二战", "传记", "自传", "中国古典文学"],
        "非虚构": ["非虚构", "科普", "散文", "访谈", "书信", "法律", "学术", "社会"],
        "地域文学": ["拉美文学", "日本文学", "英国文学", "美国文学", "法国文学", "德国文学", "俄罗斯文学", "韩国文学", "中国文学", "中国当代文学", "意大利文学", "西班牙文学", "葡萄牙文学", "波兰文学", "捷克文学", "爱尔兰文学", "阿根廷文学", "中国台湾文学", "东欧", "古希腊"],
        "电影艺术": ["剧情", "动画", "武侠", "悬疑", "喜剧", "犯罪", "纪录片", "史诗", "经典", "美学", "电影"],
    }

    rose_data = defaultdict(int)
    for e in finished:
        entry_tags = e.get("tags", [])
        for cat, keywords in TAG_CATEGORIES.items():
            if any(t in keywords for t in entry_tags):
                rose_data[cat] += 1

    rose_categories = dict(sorted(rose_data.items(), key=lambda x: x[1], reverse=True))

    # Rating distribution
    rating_dist = defaultdict(int)
    for e in finished:
        r = e.get("rating")
        if r is not None:
            rating_dist[r] += 1

    # Top authors/creators
    creator_counts = defaultdict(lambda: {"count": 0, "type": "", "avg_rating": 0, "ratings": []})
    for e in finished:
        c = e.get("creator", "")
        if c:
            creator_counts[c]["count"] += 1
            creator_counts[c]["type"] = e.get("type", "book")
            if e.get("rating"):
                creator_counts[c]["ratings"].append(e["rating"])

    for c in creator_counts:
        ratings = creator_counts[c]["ratings"]
        creator_counts[c]["avg_rating"] = round(sum(ratings) / len(ratings), 1) if ratings else 0
        del creator_counts[c]["ratings"]

    top_creators = dict(sorted(creator_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:10])

    # Format distribution
    format_dist = defaultdict(int)
    for e in year_entries:
        fmt = e.get("format", "纸质书") or "纸质书"
        format_dist[fmt] += 1

    # Stats summary for the year
    books_year = sum(1 for e in year_entries if e.get("type") == "book")
    movies_year = sum(1 for e in year_entries if e.get("type") == "movie")
    rated = [e for e in year_entries if e.get("rating") is not None]
    avg_rating = round(sum(e["rating"] for e in rated) / len(rated), 1) if rated else 0

    return {
        "year": year,
        "calendar_data": calendar_data,
        "monthly_trend": monthly_trend,
        "top_tags": top_tags,
        "rose_categories": rose_categories,
        "rating_distribution": {str(k): rating_dist[k] for k in sorted(rating_dist)},
        "top_creators": top_creators,
        "format_distribution": dict(format_dist),
        "stats_summary": {
            "total_year": len(year_entries),
            "books_year": books_year,
            "movies_year": movies_year,
            "avg_rating": avg_rating,
            "total_all_time": len(finished),
            "unique_tags": len(tag_counts),
        },
        "available_years": sorted(set(
            e.get("date_finished", "")[:4] for e in finished if e.get("date_finished", "").startswith("20")
        ), reverse=True),
    }


def update_extracts(entry_id: str, extracts: list[dict]) -> Optional[dict]:
    """Replace all extracts for an entry."""
    return update_entry(entry_id, {"extracts": extracts})


def add_extract(entry_id: str, extract: dict) -> Optional[dict]:
    """Append a single extract to an entry."""
    entry = get_by_id(entry_id)
    if not entry:
        return None
    extracts = entry.get("extracts", [])
    extracts.append(extract)
    return update_entry(entry_id, {"extracts": extracts})


def update_mood_tags(entry_id: str, mood_tags: list[str]) -> Optional[dict]:
    """Replace mood tags for an entry."""
    return update_entry(entry_id, {"mood_tags": mood_tags})


def update_daily_reading(entry_id: str, date_str: str, minutes: int) -> Optional[dict]:
    """Add or update daily reading minutes for a given date."""
    entry = get_by_id(entry_id)
    if not entry:
        return None
    daily = entry.get("daily_reading", [])
    # Update existing or append
    found = False
    for d in daily:
        if d.get("date") == date_str:
            d["minutes"] = minutes
            found = True
            break
    if not found:
        daily.append({"date": date_str, "minutes": minutes})
    daily.sort(key=lambda x: x.get("date", ""))
    return update_entry(entry_id, {"daily_reading": daily})


# ── Check-in / Check-out Session System ──────────────────

def check_in(entry_id: str, session_date: str = None) -> Optional[dict]:
    """Start a reading session for an entry. Sets active_session start time and date."""
    entry = get_by_id(entry_id)
    if not entry:
        return None
    # If there's already an active session elsewhere, auto-check-out first
    db = _load()
    for e in db.get("entries", []):
        if e.get("active_session") and e.get("id") != entry_id:
            e["active_session"] = None
    _save(db)
    now = datetime.now().isoformat()
    date_str = session_date or now.strftime("%Y-%m-%d")
    return update_entry(entry_id, {"active_session": {"start": now, "date": date_str}})


def check_out(entry_id: str) -> Optional[dict]:
    """End a reading session. Moves to sessions list and updates daily_reading."""
    entry = get_by_id(entry_id)
    if not entry:
        return None
    active = entry.get("active_session")
    if not active:
        return entry  # No active session to end

    start_str = active.get("start", "")
    now = datetime.now()
    end_str = now.isoformat()

    # Calculate duration
    try:
        start_dt = datetime.fromisoformat(start_str)
        duration = max(1, round((now - start_dt).total_seconds() / 60))
    except Exception:
        duration = 0

    # Use the session date (set at check-in) or fall back to today
    session_date = active.get("date", now.strftime("%Y-%m-%d"))

    session = {
        "start": start_str,
        "end": end_str,
        "duration": duration,
        "date": session_date,
    }

    sessions = entry.get("sessions", [])
    sessions.append(session)

    # Also add to daily_reading
    daily = entry.get("daily_reading", [])
    found = False
    for d in daily:
        if d.get("date") == session_date:
            d["minutes"] = d.get("minutes", 0) + duration
            found = True
            break
    if not found:
        daily.append({"date": session_date, "minutes": duration})
    daily.sort(key=lambda x: x.get("date", ""))

    return update_entry(entry_id, {
        "active_session": None,
        "sessions": sessions,
        "daily_reading": daily,
    })


def get_active_session() -> Optional[dict]:
    """Get the currently active reading session across all entries."""
    db = _load()
    for e in db.get("entries", []):
        active = e.get("active_session")
        if active:
            return {
                "entry_id": e.get("id"),
                "title_cn": e.get("title_cn"),
                "creator": e.get("creator"),
                "start": active.get("start"),
                "date": active.get("date", ""),
            }
    return None


def get_session_history(entry_id: str) -> list[dict]:
    """Get all reading sessions for an entry."""
    entry = get_by_id(entry_id)
    if not entry:
        return []
    return entry.get("sessions", [])


def get_preset_moods() -> list[str]:
    """Return the preset list of mood tags."""
    return PRESET_MOODS


def init_db() -> None:
    """Initialize the database if it doesn't exist."""
    if not os.path.exists(DB_PATH):
        _save({"version": 1, "entries": []})
        print(f"Created empty library at {DB_PATH}")
    else:
        print(f"Library already exists at {DB_PATH}")


if __name__ == "__main__":
    init_db()
