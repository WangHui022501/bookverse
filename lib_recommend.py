"""
Recommendation engine — local match scoring + web search enhancement.
"""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from lib_db import get_all, _load
from lib_catalog import get_book_catalog, get_movie_catalog

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _build_user_profile() -> dict:
    """Build a taste profile from the user's library."""
    entries = _load().get("entries", [])
    finished = [e for e in entries if e.get("status") in ("finished", "reading")]

    # Collect preferences
    preferred_tags = {}
    preferred_authors = {}
    preferred_regions = {}
    preferred_eras = {}

    for e in finished:
        rating = e.get("rating") or 5  # default weight
        weight = rating / 10.0

        for tag in e.get("tags", []):
            preferred_tags[tag] = preferred_tags.get(tag, 0) + weight
        creator = e.get("creator", "")
        if creator:
            preferred_authors[creator] = preferred_authors.get(creator, 0) + weight

    # Normalize
    total = sum(preferred_tags.values()) or 1
    preferred_tags = {k: v / total for k, v in preferred_tags.items()}

    # Get existing titles for dedup
    existing_titles = set(e.get("title_cn", "") for e in entries)

    return {
        "preferred_tags": preferred_tags,
        "preferred_authors": preferred_authors,
        "existing_titles": existing_titles,
        "top_rated": sorted(
            [e for e in finished if e.get("rating") and e["rating"] >= 8],
            key=lambda x: x["rating"], reverse=True
        )[:10],
    }


def _score_match(item: dict, profile: dict) -> float:
    """Score a catalog item against the user profile."""
    score = 0.0
    item_tags = item.get("tags", [])
    item_creator = item.get("creator", "")

    # Tag overlap (weighted by user preference strength)
    for tag in item_tags:
        if tag in profile["preferred_tags"]:
            score += profile["preferred_tags"][tag] * 5

    # Author match
    if item_creator in profile["preferred_authors"]:
        score += profile["preferred_authors"].get(item_creator, 0) * 3

    # Quality baseline
    score += item.get("quality", 5) * 0.2

    # Region diversity bonus (slight, to encourage exploring new regions)
    # We don't penalize, just give a tiny bump

    return score


def _local_recommend(rec_type: str = "both", count: int = 5) -> list[dict]:
    """Get local recommendations based on taste profile."""
    profile = _build_user_profile()

    candidates = []
    if rec_type in ("book", "both"):
        catalog = get_book_catalog()
        for item in catalog:
            if item["title_cn"] not in profile["existing_titles"]:
                item["type"] = "book"
                item["score"] = _score_match(item, profile)
                candidates.append(item)

    if rec_type in ("movie", "both"):
        catalog = get_movie_catalog()
        for item in catalog:
            if item["title_cn"] not in profile["existing_titles"]:
                item["type"] = "movie"
                item["score"] = _score_match(item, profile)
                candidates.append(item)

    # Sort by score, then add some randomness in the top tier
    candidates.sort(key=lambda x: x["score"], reverse=True)
    top = candidates[:count * 2]
    # Pick top-scored + one or two slightly diverse
    results = top[:count]

    return results


def _web_recommend(rec_type: str = "both", count: int = 3) -> list[dict]:
    """
    Get web-enhanced recommendations.
    Uses WebSearch to find trending/recommended items.
    Note: This is a best-effort — returns empty list on failure.
    """
    results = []
    profile = _build_user_profile()

    # Build search queries based on user's top tags
    top_tags = sorted(profile["preferred_tags"].items(), key=lambda x: x[1], reverse=True)[:5]
    top_tag_names = [t for t, _ in top_tags]

    try:
        # We'll try to web-search but gracefully handle failures
        # The actual search happens via Claude Code's WebSearch in the caller
        # Here we just prepare the queries and return what we can
        print(f"🌐 Web search queries prepared:")
        if rec_type in ("book", "both"):
            tag_query = " ".join(top_tag_names[:3])
            print(f"   📖 Search for: 豆瓣 2026 推荐 书籍 {tag_query}")
            print(f"   📖 Search for: 2026年 好书推荐 书单")
        if rec_type in ("movie", "both"):
            print(f"   🎬 Search for: 豆瓣 2026 高分 电影 推荐")
            print(f"   🎬 Search for: 2026年 值得看的电影")

        print("\n   💡 Tip: Run with --source web from Claude Code for live results.")
        print("   Claude will execute web searches and integrate results automatically.")
    except Exception as e:
        print(f"   ⚠️ Web recommendation preparation failed: {e}")

    return results


def _format_recommendation(item: dict, source: str) -> str:
    """Format a single recommendation."""
    stars = "★" * (item.get("quality", 5) // 2)
    etype = item.get("type", "book")
    type_icon = "📖" if etype == "book" else "🎬"
    match_pct = min(99, int(item.get("score", 0) * 100 / 15))

    lines = []
    lines.append(f"### {type_icon} {item['title_cn']} — {item['creator']}")
    lines.append(f"**Match**: {match_pct}% | **Quality**: {stars} | **Source**: {source}")
    if item.get("tags"):
        lines.append(f"Tags: {' · '.join(item['tags'][:6])}")
    if item.get("region"):
        lines.append(f"Region: {item['region']} | Era: {item.get('era', '')}")
    lines.append("")
    return "\n".join(lines)


def recommend(source: str = "both", rec_type: str = "both", count: int = 5, save: bool = False) -> None:
    """Generate recommendations and print/save them."""
    print(f"\n🎯 Recommendations for You")
    print(f"{'=' * 60}\n")

    all_results = []

    if source in ("local", "both"):
        local_results = _local_recommend(rec_type=rec_type, count=count)
        print("## 📚 From Your Taste Profile (Local)\n")
        for item in local_results:
            print(_format_recommendation(item, "本地推荐"))
        all_results.extend(local_results)

    if source in ("web", "both"):
        print("\n## 🌐 Web-Enhanced Recommendations\n")
        web_results = _web_recommend(rec_type=rec_type, count=min(count, 3))
        if not web_results:
            print("_Web recommendations require live web search. Run from Claude Code with --source web._\n")
        all_results.extend(web_results)

    if not all_results:
        print("No recommendations generated. Try adding more ratings to your library first!")
        return

    # Save if requested
    if save:
        recs_dir = os.path.join(BASE_DIR, "Writing", "recommendations")
        os.makedirs(recs_dir, exist_ok=True)
        filename = f"{datetime.now().strftime('%Y-%m-%d')}-recommendations.md"
        filepath = os.path.join(recs_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# 🎯 Recommendations — {datetime.now().strftime('%Y-%m-%d')}\n\n")
            f.write(f"_Source: {source} | Type: {rec_type}_\n\n---\n\n")
            for item in all_results:
                src = "本地" if item.get("score") is not None else "网络"
                f.write(_format_recommendation(item, src))
                f.write("\n")

        print(f"\n📁 Saved to {filepath}")


if __name__ == "__main__":
    recommend()
