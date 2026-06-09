"""
Article generation engine — 小红书 (RedNote) style markdown output.
Generates reading notes, monthly wrap-ups, themed lists, and annual reports.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib_db import get_by_id, get_all, get_stats, get_viz_data

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BULLET_POOL = ["·", "·", "·", "·", "·", "·", "·", "·", "·", "·", "·", "·", "·", "·", "·"]
FORMAT_LABEL = {"纸质书": "纸质书", "电子书": "电子书", "有声书": "有声书"}


def _stars_str(rating):
    if rating is None:
        return "—"
    filled = rating // 2
    half = rating % 2
    return "★" * filled + ("⯪" if half else "") + "☆" * (5 - filled - half)


def _pick_bullet(title: str, index: int = 0) -> str:
    """Pick a bullet marker for a book based on its title hash."""
    return ""


def generate_title_suggestions(entry: dict) -> list[str]:
    """Generate 3-5 title options for a single book review."""
    title = entry.get("title_cn", "")
    creator = entry.get("creator", "")
    rating = entry.get("rating", 8)
    tags = entry.get("tags", [])
    mood_tags = entry.get("mood_tags", [])

    suggestions = []

    # Type 1: Rating-led
    star_word = "神作" if rating >= 9 else "值得一读" if rating >= 7 else "我的私藏"
    suggestions.append(f"《{title}》｜{star_word}，读完久久不能平静")

    # Type 2: Emotion-led
    if mood_tags:
        mood = mood_tags[0]
        suggestions.append(f"《{title}》｜一本让你感到{mood}的书")

    # Type 3: Hook-led
    suggestions.append(f"读完《{title}》，我合上书坐了很久")

    # Type 4: Creator-led
    if creator:
        suggestions.append(f"{creator}的《{title}》｜{_stars_str(rating)} 我的真实感受")

    # Type 5: Tag-led
    if tags:
        tag = tags[0]
        suggestions.append(f"【{tag}】《{title}》— 我的阅读笔记")

    return suggestions[:5]


def suggest_related_books(entry: dict, all_entries: list[dict]) -> list[dict]:
    """Suggest related books from user's library based on tag overlap."""
    entry_tags = set(entry.get("tags", []))
    entry_id = entry.get("id", "")
    entry_title = entry.get("title_cn", "")

    scored = []
    for e in all_entries:
        if e.get("id") == entry_id or e.get("title_cn") == entry_title:
            continue
        if e.get("type") != "book" or e.get("status") != "finished":
            continue

        e_tags = set(e.get("tags", []))
        overlap = len(entry_tags & e_tags)
        if overlap > 0:
            scored.append({
                "title_cn": e["title_cn"],
                "creator": e.get("creator", ""),
                "rating": e.get("rating"),
                "overlap": overlap,
                "shared_tags": list(entry_tags & e_tags),
            })

    scored.sort(key=lambda x: x["overlap"], reverse=True)
    return scored[:4]


def _format_moods(mood_tags: list[str]) -> str:
    if not mood_tags:
        return "—"
    return " · ".join(mood_tags)


def generate_single_book_article(entry: dict, all_entries: list[dict]) -> str:
    """Generate 小红书-style single book review in Markdown."""
    title = entry.get("title_cn", "")
    creator = entry.get("creator", "")
    rating = entry.get("rating")
    tags = entry.get("tags", [])
    mood_tags = entry.get("mood_tags", [])
    extracts = entry.get("extracts", [])
    notes = entry.get("notes", "")
    date_started = entry.get("date_started", "")
    date_finished = entry.get("date_finished", "")
    reading_days = entry.get("reading_time_days")
    fmt = entry.get("format", "纸质书")
    emoji = _pick_bullet(title)

    related = suggest_related_books(entry, all_entries)
    titles = generate_title_suggestions(entry)

    lines = []
    lines.append(f"# {emoji} 《{title}》｜{titles[0].split('｜')[1] if '｜' in titles[0] else '阅读笔记'}")
    lines.append("")
    lines.append(f"> **{creator}** 著  |  {_stars_str(rating)} {rating}/10  |  {FORMAT_LABEL.get(fmt, '纸质书')} {fmt}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 一句话推荐
    lines.append("## 一句话推荐")
    lines.append("")
    reco = f"如果你喜欢{', '.join(tags[:2])}，那这本书一定会击中你。"
    if rating and rating >= 9:
        reco = f"这不仅仅是一本书，是一次完整的生命体验。如果你喜欢{', '.join(tags[:2])}，这本书不可错过。"
    lines.append(f"> {reco}")
    lines.append("")

    # 为什么读这本书
    lines.append("##  为什么读这本书")
    lines.append("")
    if notes:
        lines.append(notes)
    else:
        source = entry.get("source", "")
        if source:
            lines.append(f"最初是被{source}吸引的。")
        else:
            lines.append(f"一直对{' / '.join(tags[:3])}很感兴趣，这本书在书单里放了很久。")
    lines.append("")

    # 3个记忆点
    lines.append("##  3个让我记住的瞬间")
    lines.append("")
    if extracts:
        for i, ext in enumerate(extracts[:3], 1):
            txt = ext.get("text", "")[:120]
            note = ext.get("note", "")
            lines.append(f"**{i}.** 「{txt}...」")
            if note:
                lines.append(f"   — {note}")
            lines.append("")
    else:
        # Fallback: generic structure
        lines.append("**1.** 读到一半时的感受 — *(在这里写下你最深的记忆点)*")
        lines.append("")
        lines.append("**2.** 某个难以忘记的场景或句子 — *(从这里开始)*")
        lines.append("")
        lines.append("**3.** 合上书的那一刻 — *(结尾的感受)*")
        lines.append("")

    # 摘录
    if extracts:
        lines.append("## 摘录")
        lines.append("")
        for ext in extracts[:6]:
            txt = ext.get("text", "")
            note = ext.get("note", "")
            page = ext.get("page", "")
            lines.append(f"> “{txt}”")
            meta_parts = []
            if page:
                meta_parts.append(f"📎 {page}")
            if note:
                meta_parts.append(note)
            if meta_parts:
                lines.append(f"> — {' · '.join(meta_parts)}")
            lines.append("")
    lines.append("")

    # 评分与感受
    lines.append("## 我的评分与感受")
    lines.append("")
    lines.append(f"| 维度 | |")
    lines.append(f"|------|------|")
    lines.append(f"| **评分** | {_stars_str(rating)} **{rating}/10** |")
    lines.append(f"|  **感受** | {_format_moods(mood_tags)} |")
    if date_started and date_finished:
        lines.append(f"| **时间** | {date_started} → {date_finished}" + (f"（{reading_days}天）" if reading_days else "") + " |")
    elif date_finished:
        lines.append(f"| **读完** | {date_finished} |")
    lines.append(f"| **格式** | {FORMAT_LABEL.get(fmt, '纸质书')} {fmt} |")
    lines.append(f"| 🔄 **重读** | {'是' if entry.get('reread_count', 0) > 0 else '否'} |")
    lines.append("")

    # 适合谁读
    lines.append("## 适合谁读")
    lines.append("")
    audience_parts = []
    for tag in tags[:4]:
        audience_parts.append(f"对**{tag}**感兴趣的读者")
    if mood_tags:
        audience_parts.append(f"想要感到{mood_tags[0]}的时候")
    lines.append(f"- {' · '.join(audience_parts[:3])}")
    if rating and rating <= 7:
        lines.append(f"- 如果你时间有限，可以优先读其他同类型作品")
    lines.append("")

    # 关联阅读
    if related:
        lines.append("## 关联阅读")
        lines.append("")
        lines.append("> 读完这本书，你可能会想继续读：")
        lines.append("")
        for r in related[:3]:
            shared = " · ".join(r["shared_tags"][:2])
            lines.append(f"- **《{r['title_cn']}》** — {r.get('creator', '')} ｜ 共同主题：{shared}")
        lines.append("")

    # Tags
    lines.append("---")
    lines.append("")
    all_tags = tags + (mood_tags if mood_tags else [])
    tag_line = " ".join(f"`#{t}`" for t in all_tags[:8])
    lines.append(tag_line)
    lines.append("")
    hashtags = " ".join(f"#{t}" for t in (tags[:4] + ["阅读笔记", "读书分享", "我的私人书单"]))
    lines.append(hashtags)
    lines.append("")

    return "\n".join(lines)


def generate_monthly_article(entries: list[dict], month: str) -> str:
    """Generate monthly reading wrap-up article."""
    # Parse month (YYYY-MM)
    year, mon = month.split("-") if "-" in month else (month[:4], month[4:])
    month_names = ["一月", "二月", "三月", "四月", "五月", "六月",
                   "七月", "八月", "九月", "十月", "十一月", "十二月"]
    month_cn = month_names[int(mon) - 1] if mon.isdigit() and 1 <= int(mon) <= 12 else month

    books = [e for e in entries if e.get("type") == "book"]
    movies = [e for e in entries if e.get("type") == "movie"]
    rated = [e for e in entries if e.get("rating")]
    avg_rating = round(sum(e["rating"] for e in rated) / len(rated), 1) if rated else 0

    all_tags = []
    for e in entries:
        all_tags.extend(e.get("tags", []))
    from collections import Counter
    top_tags = [t for t, _ in Counter(all_tags).most_common(6)]

    lines = []
    lines.append(f"# {year}年{month_cn} 书影音月度总结")
    lines.append("")
    lines.append(f"> 本月共读了 **{len(books)}** 本书，看了 **{len(movies)}** 部影视")
    if avg_rating:
        lines.append(f"> 月度均分：**{avg_rating}/10**")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Books section
    if books:
        lines.append("## 阅读")
        lines.append("")
        for e in books:
            stars = _stars_str(e.get("rating"))
            rating = e.get("rating")
            rating_str = f"{stars} {rating}/10" if rating else "未评分"
            lines.append(f"### 《{e['title_cn']}》— {e.get('creator', '')}")
            lines.append(f"> {rating_str}")
            if e.get("mood_tags"):
                lines.append(f"> 感受：{_format_moods(e['mood_tags'])}")
            if e.get("notes"):
                lines.append(f"> {e['notes'][:200]}")
            if e.get("extracts"):
                ext = e["extracts"][0]
                lines.append(f'>  "{ext["text"][:100]}..."')
            lines.append("")
    else:
        lines.append("## 阅读")
        lines.append("")
        lines.append("> 本月暂无阅读记录。期待下个月的新书 📚")
        lines.append("")

    # Movies section
    if movies:
        lines.append("## 观影")
        lines.append("")
        for e in movies:
            stars = _stars_str(e.get("rating"))
            rating = e.get("rating")
            rating_str = f"{stars} {rating}/10" if rating else "未评分"
            lines.append(f"### 《{e['title_cn']}》— {e.get('creator', '')}")
            lines.append(f"> {rating_str}")
            if e.get("mood_tags"):
                lines.append(f"> 感受：{_format_moods(e['mood_tags'])}")
            lines.append("")
        lines.append("")

    # Monthly pick
    if rated:
        best = max(rated, key=lambda e: e.get("rating", 0))
        lines.append("## 本月最佳")
        lines.append("")
        lines.append(f"**《{best['title_cn']}》** — {best.get('creator', '')}")
        lines.append(f"评分：{_stars_str(best['rating'])} {best['rating']}/10")
        lines.append("")

    # Tags
    lines.append("---")
    lines.append("")
    tag_line = " ".join(f"`#{t}`" for t in top_tags)
    lines.append(tag_line)
    lines.append("")
    lines.append(f"#月度总结 #阅读记录 #观影记录 #{year}年{month_cn}")
    lines.append("")

    return "\n".join(lines)


def generate_theme_article(entries: list[dict], theme: str = "") -> str:
    """Generate themed book list article."""
    if not entries:
        return f"# 主题书单\n\n> 暂无相关书籍。\n"

    if not theme:
        # Try to infer theme from most common tag
        from collections import Counter
        all_tags = []
        for e in entries:
            all_tags.extend(e.get("tags", []))
        theme = Counter(all_tags).most_common(1)[0][0] if all_tags else "推荐"

    lines = []
    lines.append(f"# 主题书单｜{theme}")
    lines.append("")
    lines.append(f"> 整理了 **{len(entries)}** 本与「{theme}」相关的好书，每一本都值得花时间慢慢读。")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, e in enumerate(entries, 1):
        title = e.get("title_cn", "")
        creator = e.get("creator", "")
        rating = e.get("rating")
        stars = _stars_str(rating)
        tags = e.get("tags", [])

        lines.append(f"## {i}. 《{title}》")
        lines.append(f"> {creator} ｜ {stars} " + (f"{rating}/10" if rating else ""))
        lines.append("")

        if e.get("notes"):
            lines.append(f"{e['notes'][:200]}")
            lines.append("")

        if e.get("extracts"):
            ext = e["extracts"][0]
            lines.append(f'>  "{ext["text"][:150]}..."')
            lines.append("")

        tag_line = " · ".join(t for t in tags if t != theme)[:5]
        if tag_line:
            lines.append(f"`{tag_line}`")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"#主题书单 #阅读推荐 #{theme} #我的私人书单")
    lines.append("")

    return "\n".join(lines)


def generate_annual_article(entries: list[dict], year: str, stats: dict = None) -> str:
    """Generate annual reading report like Spotify Wrapped."""
    if stats is None:
        stats = get_viz_data(year)

    summary = stats.get("stats_summary", {})
    total = summary.get("total_year", len(entries))
    avg_rating = summary.get("avg_rating", 0)
    top_tags = stats.get("top_tags", {})
    top_tag_list = list(top_tags.keys())[:5]
    top_creators = stats.get("top_creators", {})

    # Find highest rated
    rated = [e for e in entries if e.get("rating")]
    best_book = max(rated, key=lambda e: (e.get("rating", 0), len(e.get("extracts", [])))) if rated else None

    # Most extracts
    most_extracts = max(entries, key=lambda e: len(e.get("extracts", []))) if entries else None

    # Monthly trend
    monthly_trend = stats.get("monthly_trend", [])
    best_month_data = max(monthly_trend, key=lambda m: m["total_month"]) if monthly_trend else None
    best_month = best_month_data["month"] if best_month_data else ""

    # Format breakdown
    format_dist = stats.get("format_distribution", {})

    month_names = ["一月", "二月", "三月", "四月", "五月", "六月",
                   "七月", "八月", "九月", "十月", "十一月", "十二月"]

    lines = []
    lines.append(f"# {year} 年度阅读报告")
    lines.append("")
    lines.append(f"> 一年过去了，书是最好的陪伴。来看看这一年的阅读足迹吧 ")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Highlight stats
    lines.append("## 年度高光")
    lines.append("")
    lines.append(f"| 指标 | |")
    lines.append(f"|------|------|")
    lines.append(f"| 年度阅读总量 | **{total}** 本书 + 影视 |")
    lines.append(f"| 年度均分 | **{avg_rating}/10** |")
    lines.append(f"| 阅读最多的月份 | **{best_month}** |")
    if top_tag_list:
        lines.append(f"| 🏷️ 年度主题 | **{' · '.join(top_tag_list[:3])}** |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Format breakdown
    if format_dist:
        lines.append("## 阅读方式")
        lines.append("")
        for fmt, count in sorted(format_dist.items(), key=lambda x: x[1], reverse=True):
            emoji = FORMAT_LABEL.get(fmt, "📖")
            bar = "█" * min(count, 20)
            lines.append(f"**{emoji} {fmt}**  {count} 本  {bar}")
        lines.append("")

    # Best of the year
    if best_book:
        lines.append("## 年度最佳")
        lines.append("")
        lines.append(f"### 《{best_book['title_cn']}》— {best_book.get('creator', '')}")
        lines.append(f"> 评分：{_stars_str(best_book.get('rating'))} **{best_book.get('rating')}/10**")
        if best_book.get("mood_tags"):
            lines.append(f"> 感受：{_format_moods(best_book['mood_tags'])}")
        if best_book.get("notes"):
            lines.append(f"> {best_book['notes'][:200]}")
        lines.append("")

    # Most annotated
    if most_extracts and len(most_extracts.get("extracts", [])) > 0:
        lines.append("## 摘录最多的书")
        lines.append("")
        lines.append(f"**《{most_extracts['title_cn']}》** — 共摘录了 {len(most_extracts['extracts'])} 段文字")
        ext = most_extracts["extracts"][0]
        lines.append(f'> “{ext["text"][:150]}...”')
        lines.append("")

    # Top creators
    if top_creators:
        lines.append("## 年度作者")
        lines.append("")
        for i, (creator, data) in enumerate(list(top_creators.items())[:5], 1):
            lines.append(f"**{i}. {creator}** — {data['count']} 部作品" + (f"，均分 {data['avg_rating']}" if data['avg_rating'] else ""))
        lines.append("")

    # Monthly reading calendar summary
    if monthly_trend:
        lines.append("## 月度阅读节奏")
        lines.append("")
        lines.append("| 月份 | 书籍 | 影视 | 累计 |")
        lines.append("|------|------|------|------|")
        for m in monthly_trend:
            month_idx = int(m["month"].split("-")[1]) if "-" in m["month"] else 0
            month_display = month_names[month_idx - 1] if 1 <= month_idx <= 12 else m["month"]
            lines.append(f"| {month_display} | {m['books']} | {m['movies']} | {m['cumulative']} |")
        lines.append("")

    # Closing
    lines.append("---")
    lines.append("")
    lines.append(f"## {int(year)+1} 年的阅读目标")
    lines.append("")
    lines.append("> 继续读下去，继续被书改变。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"#年度阅读报告 #阅读总结 #{year} #我的私人书单")
    lines.append("")

    return "\n".join(lines)


def generate_article(entry_ids: list[str], article_type: str = "single",
                     options: dict = None) -> dict:
    """Main entry point for article generation.

    Args:
        entry_ids: List of entry IDs to include
        article_type: "single" | "monthly" | "theme" | "annual"
        options: Optional dict with month, year, theme keys

    Returns:
        {"markdown": str, "title_suggestions": list[str], "entry_count": int}
    """
    options = options or {}

    if article_type == "single" and entry_ids:
        entry = get_by_id(entry_ids[0])
        if not entry:
            return {"error": f"Entry {entry_ids[0]} not found"}
        all_entries = get_all(type_filter="book", status_filter="finished")
        markdown = generate_single_book_article(entry, all_entries)
        titles = generate_title_suggestions(entry)
        return {"markdown": markdown, "title_suggestions": titles, "entry_count": 1}

    elif article_type == "monthly":
        month = options.get("month", datetime.now().strftime("%Y-%m"))
        entries = get_all(status_filter="finished")
        month_entries = [e for e in entries if e.get("date_finished", "").startswith(month)]
        markdown = generate_monthly_article(month_entries, month)
        return {"markdown": markdown, "title_suggestions": [], "entry_count": len(month_entries)}

    elif article_type == "theme":
        theme = options.get("theme", "")
        if entry_ids:
            entries = [get_by_id(eid) for eid in entry_ids if get_by_id(eid)]
            entries = [e for e in entries if e is not None]
            if theme:
                entries = [e for e in entries if theme in e.get("tags", [])]
        elif theme:
            all_entries = get_all(type_filter="book", status_filter="finished")
            entries = [e for e in all_entries if theme in e.get("tags", [])]
        else:
            entries = []
        markdown = generate_theme_article(entries, theme)
        return {"markdown": markdown, "title_suggestions": [], "entry_count": len(entries)}

    elif article_type == "annual":
        year = options.get("year", datetime.now().strftime("%Y"))
        viz_data = get_viz_data(year)
        entries = get_all(status_filter="finished")
        year_entries = [e for e in entries if e.get("date_finished", "").startswith(year)]
        markdown = generate_annual_article(year_entries, year, viz_data)
        return {"markdown": markdown, "title_suggestions": [], "entry_count": len(year_entries)}

    else:
        return {"error": f"Unknown article type: {article_type}"}


def save_article(markdown: str, filename: str = None, article_type: str = "article") -> str:
    """Save generated article to Writing/ folder. Returns the filepath."""
    writing_dir = os.path.join(BASE_DIR, "Writing")
    os.makedirs(writing_dir, exist_ok=True)

    if filename is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}-{article_type}.md"

    # Ensure .md extension
    if not filename.endswith(".md"):
        filename += ".md"

    filepath = os.path.join(writing_dir, filename)

    # If file exists, append timestamp
    if os.path.exists(filepath):
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%H%M%S")
        filepath = os.path.join(writing_dir, f"{name}-{timestamp}{ext}")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown)

    return filepath


if __name__ == "__main__":
    # Quick test
    entries = get_all(type_filter="book", status_filter="finished")
    if entries:
        result = generate_article([entries[0]["id"]], "single")
        print(result["markdown"][:500])
    else:
        print("No entries found for testing.")
