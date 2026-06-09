"""
Discovery & Reflection engine.
Analyzes existing library data for patterns, gaps, and generates reflection prompts.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from lib_db import get_all, get_by_id, get_all_tags, _load

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _find_similar_authors(entries: list[dict]) -> list[str]:
    """Find authors the user loves and suggest their other works."""
    # Group by creator, look at high-rated entries
    author_scores = {}
    for e in entries:
        creator = e.get("creator", "")
        if not creator or not e.get("rating"):
            continue
        if creator not in author_scores:
            author_scores[creator] = {"ratings": [], "tags": set(), "count": 0}
        author_scores[creator]["ratings"].append(e["rating"])
        author_scores[creator]["tags"].update(e.get("tags", []))
        author_scores[creator]["count"] += 1

    suggestions = []
    for creator, data in author_scores.items():
        if data["count"] >= 2 and sum(data["ratings"]) / len(data["ratings"]) >= 8:
            suggestions.append(f"💡 You love **{creator}**'s work (avg {sum(data['ratings'])/len(data['ratings']):.1f}/10 across {data['count']} entries). Explore more of their bibliography!")

    return suggestions[:5]


def _find_tag_correlations(entries: list[dict]) -> list[str]:
    """Find tags that co-occur with high ratings."""
    # Build co-occurrence of tags with high-rated entries
    rated = [e for e in entries if e.get("rating") and e.get("rating") >= 8]
    tag_pairs = {}
    for e in rated:
        tags = e.get("tags", [])
        for i, t1 in enumerate(tags):
            for t2 in tags[i + 1:]:
                key = tuple(sorted([t1, t2]))
                tag_pairs[key] = tag_pairs.get(key, 0) + 1

    top_pairs = sorted(tag_pairs.items(), key=lambda x: x[1], reverse=True)[:5]
    suggestions = []
    for (t1, t2), count in top_pairs:
        if count >= 2:
            suggestions.append(f"🔗 `{t1}` + `{t2}` often appear together in your favorites ({count}×). Look for works combining both.")

    return suggestions


def _find_genre_gaps(entries: list[dict]) -> list[str]:
    """Identify complementary genres the user hasn't explored much."""
    tags = get_all_tags()

    # Define genre clusters and their complements
    clusters = {
        "拉美文学": ["博尔赫斯", "科塔萨尔", "波拉尼奥", "鲁尔福"],
        "科幻": ["菲利普·迪克", "莱姆", "特德·姜", "阿瑟·克拉克"],
        "日本文学": ["川端康成", "三岛由纪夫", "村上春树", "夏目漱石"],
        "中短篇小说": ["爱丽丝·门罗", "雷蒙德·卡佛", "契诃夫", "海明威"],
        "女性主义": ["弗吉尼亚·伍尔夫", "玛格丽特·阿特伍德", "埃莱娜·费兰特", "托妮·莫里森"],
        "诗歌": ["佩索阿", "里尔克", "艾米莉·狄金森", "博尔赫斯"],
        "哲学": ["尼采", "萨特", "加缪", "维特根斯坦"],
        "历史": ["尤瓦尔·赫拉利", "史景迁", "孔飞力", "徐中约"],
        "东欧": ["赫拉巴尔", "昆德拉", "米沃什", "扎加耶夫斯基"],
        "中短篇小说": ["爱丽丝·门罗", "雷蒙德·卡佛", "契诃夫", "海明威"],
    }

    existing_tags = set(tags.keys())
    high_rated_tags = set()
    for e in entries:
        if e.get("rating") and e["rating"] >= 8:
            high_rated_tags.update(e.get("tags", []))

    suggestions = []
    for cluster, authors in clusters.items():
        if cluster in existing_tags:
            # User likes this — suggest related authors they haven't tried
            listed_authors = set(e.get("creator", "") for e in entries)
            new_authors = [a for a in authors if a not in listed_authors]
            if new_authors:
                suggestions.append(f"📚 You enjoy `{cluster}` — try: {', '.join(new_authors[:3])}")

    # Find clusters they haven't touched
    untouched = [c for c in clusters if c not in existing_tags and c not in high_rated_tags]
    if untouched:
        suggestions.append(f"🌱 Unexplored territory: `{'`, `'.join(untouched[:4])}` — consider expanding here.")

    return suggestions[:8]


def _find_theme_clusters(entries: list[dict]) -> list[str]:
    """Group entries by shared themes and surface patterns."""
    # Count entries by region/era
    finished = [e for e in entries if e.get("status") == "finished"]
    by_tag = {}
    for e in finished:
        for t in e.get("tags", []):
            by_tag.setdefault(t, []).append(e["title_cn"])

    suggestions = []
    # Highlight clusters with 3+ entries
    for tag, titles in sorted(by_tag.items(), key=lambda x: len(x[1]), reverse=True):
        if len(titles) >= 3:
            suggestions.append(f"📂 Your `{tag}` collection ({len(titles)}): {', '.join(titles[:6])}")

    return suggestions[:6]


def _build_discovery_report() -> str:
    """Build the full discovery report."""
    entries = _load().get("entries", [])
    finished = [e for e in entries if e.get("status") == "finished"]

    lines = []
    lines.append(f"# 🔎 Discovery Report — {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("")

    lines.append("## 📖 Author Deep-Dives")
    lines.extend(_find_similar_authors(finished))
    lines.append("")

    lines.append("## 🔗 Tag Correlations")
    lines.extend(_find_tag_correlations(finished))
    lines.append("")

    lines.append("## 🗺️ Genre & Direction Suggestions")
    lines.extend(_find_genre_gaps(finished))
    lines.append("")

    lines.append("## 📂 Your Theme Clusters")
    lines.extend(_find_theme_clusters(finished))
    lines.append("")

    lines.append("---")
    lines.append(f"_Generated from {len(finished)} finished entries across {len(get_all_tags())} tags._")

    return "\n".join(lines)


def discover(save: bool = False) -> None:
    """Run the discovery engine and print or save the report."""
    report = _build_discovery_report()
    print(report)

    if save:
        discoveries_dir = os.path.join(BASE_DIR, "Writing", "discoveries")
        os.makedirs(discoveries_dir, exist_ok=True)
        filename = f"{datetime.now().strftime('%Y-%m-%d')}-discovery.md"
        filepath = os.path.join(discoveries_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n📁 Saved to {filepath}")


def _generate_prompts(entry: dict) -> list[str]:
    """Generate reflection prompts based on an entry's tags and content."""
    title = entry.get("title_cn", "")
    creator = entry.get("creator", "")
    etype = entry.get("type", "")
    tags = entry.get("tags", [])
    rating = entry.get("rating")

    prompts = []

    # Generic prompts
    prompts.append(f"What stayed with you most after finishing 《{title}》?")

    # Tag-based prompts
    if "女性主义" in tags or "女性" in tags:
        prompts.append(f"How does 《{title}》 change or deepen your understanding of the female experience?")
        # Look for other feminist works to compare
        all_entries = get_all(tag_filter="女性主义")
        others = [e for e in all_entries if e.get("title_cn") != title]
        if others:
            prompts.append(f"Compare 《{title}》 with your other feminist readings ({', '.join(e['title_cn'] for e in others[:3])}). How do their rebellions differ?")

    if "拉美文学" in tags:
        prompts.append(f"Latin American literature often blends the real and the fantastic. Where does 《{title}》 sit on that spectrum, and what does that blending achieve?")

    if "科幻" in tags:
        prompts.append(f"What future does 《{title}》 imagine — and is it one you'd want to live in?")

    if "历史" in tags:
        prompts.append(f"What does 《{title}》 reveal about how power operates across time? Can you see its patterns in the present?")

    if "诗歌" in tags:
        prompts.append(f"Which image or line from 《{title}》 has stayed with you? Try writing a response poem.")

    if "中短篇小说" in tags:
        prompts.append(f"Short stories are worlds in miniature. Which story in 《{title}》 felt most complete, and which left you wanting more?")

    if "哲学" in tags:
        prompts.append(f"What question does 《{title}》 ask that you're still thinking about?")

    if "东欧" in tags:
        prompts.append(f"How does 《{title}》's Eastern European context shape its emotional landscape? What does exile feel like in its pages?")

    if "日本" in tags or "日本文学" in tags:
        prompts.append(f"Japanese aesthetics often find beauty in transience. Where does 《{title}》 embody this sensibility — or resist it?")

    # Movie-specific prompts
    if etype == "movie":
        prompts.append(f"What visual moment in 《{title}》 couldn't be expressed in words alone?")
        if "动画" in tags:
            prompts.append(f"How does the animated form of 《{title}》 enable something live-action couldn't?")

    # Rating-based
    if rating and rating >= 9:
        prompts.append(f"You rated 《{title}》 highly ({rating}/10). What makes it exceptional — and what would have pushed it to a perfect 10?")
    elif rating and rating <= 6:
        prompts.append(f"You rated 《{title}》 {rating}/10. What held it back? Was it the right book at the wrong time, or something deeper?")

    # Creator-based
    if creator:
        prompts.append(f"What do you know about {creator}'s life? How might their biography inform 《{title}》?")

    return prompts[:5]


def reflect_on(entry_id: str, save: bool = False) -> None:
    """Generate reflection prompts for a specific entry."""
    entry = get_by_id(entry_id)
    if not entry:
        print(f"❌ Entry '{entry_id}' not found")
        return

    prompts = _generate_prompts(entry)

    print(f"\n✍️  Reflection Prompts for 《{entry['title_cn']}》 ({entry.get('creator','')})")
    print(f"   Tags: {', '.join(entry.get('tags', []))}")
    if entry.get("rating"):
        print(f"   Your rating: {'★' * (entry['rating'] // 2)} {entry['rating']}/10")
    print(f"\n{'=' * 60}")
    for i, p in enumerate(prompts, 1):
        print(f"\n  {i}. {p}")
    print(f"\n{'=' * 60}")

    if save:
        writing_dir = os.path.join(BASE_DIR, "Writing")
        os.makedirs(writing_dir, exist_ok=True)
        safe_title = entry['title_cn'].replace("/", "-").replace(":", "：")
        filename = f"Reflection-{safe_title}.md"
        filepath = os.path.join(writing_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Reflection: 《{entry['title_cn']}》\n\n")
            f.write(f"**Author**: {entry.get('creator', '')}\n")
            f.write(f"**Rating**: {entry.get('rating', '—')}/10\n")
            f.write(f"**Tags**: {', '.join(entry.get('tags', []))}\n\n")
            f.write("## Prompts\n\n")
            for i, p in enumerate(prompts, 1):
                f.write(f"{i}. {p}\n\n")
            f.write("\n## My Response\n\n_(Write your reflection here...)_\n")
        print(f"\n📁 Saved reflection template to {filepath}")


if __name__ == "__main__":
    discover()
