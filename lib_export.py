"""
Markdown export — reads library.json and updates READING GUIDE.md / FILMS GUIDE.md
with auto-generated rating tables between guard comments.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib_db import get_all, get_stats, get_all_tags

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _stars(rating: int | None) -> str:
    """Convert 1-10 rating to ★★★★★ display."""
    if rating is None:
        return "—"
    filled = rating // 2
    half = rating % 2
    empty = 5 - filled - half
    return "★" * filled + ("⯪" if half else "") + "☆" * empty


def _rating_bar(rating: int | None) -> str:
    """Visual rating bar."""
    if rating is None:
        return "`······`"
    n = max(1, rating)
    return "`" + "█" * n + "░" * (10 - n) + "`"


def _build_book_table() -> str:
    """Build the book ratings table in markdown."""
    books = get_all(type_filter="book", sort_by="date_finished", reverse=True)
    finished = [b for b in books if b.get("status") == "finished"]
    reading = [b for b in books if b.get("status") == "reading"]
    to_read = [b for b in books if b.get("status") == "to-read"]

    lines = []
    lines.append("## 📊 阅读记录 (Auto-generated)")
    lines.append("")
    lines.append(f"_共 {len(books)} 本: {len(finished)} 已读, {len(reading)} 在读, {len(to_read)} 想读_")
    lines.append("")

    # Finished books
    if finished:
        lines.append("### 已读")
        lines.append("")
        lines.append("| # | 书名 | 作者 | 日期 | 评分 | 标签 |")
        lines.append("|---|---|---|---|---|---|")
        for i, b in enumerate(finished, 1):
            title = b.get("title_cn", "")
            creator = b.get("creator", "")
            date_str = b.get("date_finished", "") or "—"
            stars_str = _stars(b.get("rating"))
            tags_str = " ".join(f"`{t}`" for t in b.get("tags", [])[:4])
            lines.append(f"| {i} | {title} | {creator} | {date_str} | {stars_str} | {tags_str} |")
        lines.append("")

    # Currently reading
    if reading:
        lines.append("### 在读")
        lines.append("")
        lines.append("| # | 书名 | 作者 | 标签 |")
        lines.append("|---|---|---|---|")
        for i, b in enumerate(reading, 1):
            title = b.get("title_cn", "")
            creator = b.get("creator", "")
            tags_str = " ".join(f"`{t}`" for t in b.get("tags", [])[:4])
            lines.append(f"| {i} | {title} | {creator} | {tags_str} |")
        lines.append("")

    # To-read
    if to_read:
        lines.append("### 想读")
        lines.append("")
        lines.append("| # | 书名 | 作者 | 标签 |")
        lines.append("|---|---|---|---|")
        for i, b in enumerate(to_read, 1):
            title = b.get("title_cn", "")
            creator = b.get("creator", "")
            tags_str = " ".join(f"`{t}`" for t in b.get("tags", [])[:4])
            lines.append(f"| {i} | {title} | {creator} | {tags_str} |")
        lines.append("")

    # Top rated
    top_rated = sorted([b for b in finished if b.get("rating")], key=lambda x: x["rating"], reverse=True)[:10]
    if top_rated:
        lines.append("### 🏆 评分最高")
        lines.append("")
        lines.append("| 书名 | 作者 | 评分 |")
        lines.append("|---|---|---|")
        for b in top_rated:
            lines.append(f"| {b.get('title_cn', '')} | {b.get('creator', '')} | {_stars(b.get('rating'))} {b.get('rating')}/10 |")
        lines.append("")

    return "\n".join(lines)


def _build_movie_table() -> str:
    """Build the movie ratings table in markdown."""
    movies = get_all(type_filter="movie", sort_by="date_finished", reverse=True)
    finished = [m for m in movies if m.get("status") == "finished"]

    lines = []
    lines.append("## 🎬 观影记录 (Auto-generated)")
    lines.append("")
    lines.append(f"_共 {len(movies)} 部: {len(finished)} 已看_")
    lines.append("")

    if finished:
        lines.append("| # | 电影 | 导演 | 日期 | 评分 | 标签 |")
        lines.append("|---|---|---|---|---|---|")
        for i, m in enumerate(finished, 1):
            title = m.get("title_cn", "")
            creator = m.get("creator", "")
            date_str = m.get("date_finished", "") or "—"
            stars_str = _stars(m.get("rating"))
            tags_str = " ".join(f"`{t}`" for t in m.get("tags", [])[:4])
            lines.append(f"| {i} | {title} | {creator} | {date_str} | {stars_str} | {tags_str} |")
        lines.append("")

    top_rated = sorted([m for m in finished if m.get("rating")], key=lambda x: x["rating"], reverse=True)[:10]
    if top_rated:
        lines.append("### 🏆 评分最高")
        lines.append("")
        lines.append("| 电影 | 导演 | 评分 |")
        lines.append("|---|---|---|")
        for m in top_rated:
            lines.append(f"| {m.get('title_cn', '')} | {m.get('creator', '')} | {_stars(m.get('rating'))} {m.get('rating')}/10 |")
        lines.append("")

    return "\n".join(lines)


def _build_stats_section() -> str:
    """Build statistics summary."""
    stats = get_stats()
    tags = get_all_tags()

    lines = []
    lines.append("## 📈 统计 (Auto-generated)")
    lines.append("")
    lines.append(f"- **总收录**: {stats['total_entries']} (书籍 {stats['books_finished']} 本已读, 电影 {stats['movies_finished']} 部已看)")
    if stats['avg_book_rating']:
        lines.append(f"- **书籍均分**: {stats['avg_book_rating']}/10")
    if stats['avg_movie_rating']:
        lines.append(f"- **电影均分**: {stats['avg_movie_rating']}/10")
    lines.append(f"- **今年已读**: {stats['entries_this_year']} 项")
    lines.append("")
    lines.append("### 热门标签")
    lines.append("")
    tag_cloud = " ".join(f"`{t}`×{c}" for t, c in list(tags.items())[:15])
    lines.append(tag_cloud)
    lines.append("")

    return "\n".join(lines)


def _inject_into_file(filepath: str, table_content: str, guard_start: str, guard_end: str) -> None:
    """Inject content between guard comments in a file. Creates guards if absent."""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = ""

    start_marker = f"<!-- {guard_start} -->"
    end_marker = f"<!-- {guard_end} -->"

    if start_marker in content and end_marker in content:
        # Replace existing guarded section
        before = content.split(start_marker)[0]
        after = content.split(end_marker)[1]
        new_content = before + start_marker + "\n\n" + table_content + "\n" + end_marker + after
    else:
        # Append at end
        if content and not content.endswith("\n"):
            content += "\n"
        new_content = content + "\n" + start_marker + "\n\n" + table_content + "\n" + end_marker + "\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)


def export_all() -> None:
    """Export all tables to GUIDE files."""
    reading_path = os.path.join(BASE_DIR, "READING GUIDE.md")
    films_path = os.path.join(BASE_DIR, "FILMS GUIDE.md")

    # Build the full block for READING GUIDE
    reading_block = _build_stats_section() + "\n" + _build_book_table()
    _inject_into_file(reading_path, reading_block, "AUTO_TABLES_START", "AUTO_TABLES_END")
    print(f"Updated {reading_path}")

    # Build the full block for FILMS GUIDE
    films_block = _build_movie_table()
    _inject_into_file(films_path, films_block, "AUTO_TABLES_START", "AUTO_TABLES_END")
    print(f"Updated {films_path}")


if __name__ == "__main__":
    export_all()
