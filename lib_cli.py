#!/usr/bin/env python
"""
Unified CLI for personal library management.
Usage: python tools/lib_cli.py <command> [options]

Commands:
  add       Add a new book/movie/music entry
  rate      Update rating for an entry
  edit      Edit any field of an entry
  delete    Delete an entry
  list      List entries with filtering and sorting
  search    Full-text search
  stats     Show reading/viewing statistics
  discover  Run discovery engine (topic suggestions)
  reflect   Generate reflection writing prompts for an entry
  recommend Get book/movie recommendations
  export    Regenerate markdown tables in GUIDE files
  tags      List all tags
"""

import argparse
import os
import sys

# Fix Windows console encoding for emoji and CJK characters
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure tools/ is on path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib_db import (
    add_entry, update_entry, delete_entry, get_by_id,
    get_all, search, get_stats, get_all_tags, init_db
)
from lib_export import export_all
from lib_discover import discover, reflect_on
from lib_recommend import recommend
from lib_sync import sync as do_sync


def cmd_add(args):
    """Add a new entry."""
    entry = {
        "type": args.type,
        "title_cn": args.title,
        "title_orig": args.title_orig or "",
        "creator": args.creator or "",
        "creator_orig": args.creator_orig or "",
        "date_finished": args.date or "",
        "rating": args.rating,
        "tags": [t.strip() for t in args.tags.split(",")] if args.tags else [],
        "status": args.status or "finished",
        "notes": args.notes or "",
        "source": args.source or "",
        "cover_image": args.cover or "",
    }
    result = add_entry(entry)
    print(f"✅ Added [{result['id']}] {result['title_cn']} ({result['type']})")
    print(f"   Rating: {result['rating'] or 'not rated'} | Tags: {', '.join(result['tags']) or 'none'}")


def cmd_rate(args):
    """Update rating for an entry."""
    entry = get_by_id(args.id)
    if not entry:
        print(f"❌ Entry '{args.id}' not found")
        return
    result = update_entry(args.id, {"rating": args.rating})
    stars = "★" * (args.rating // 2) + ("+" if args.rating % 2 else "") + "☆" * (5 - args.rating // 2 - args.rating % 2)
    print(f"[*] Updated [{args.id}] {result['title_cn']}: {stars} {args.rating}/10")


def cmd_edit(args):
    """Edit fields of an entry."""
    entry = get_by_id(args.id)
    if not entry:
        print(f"❌ Entry '{args.id}' not found")
        return

    updates = {}
    if args.title is not None:
        updates["title_cn"] = args.title
    if args.creator is not None:
        updates["creator"] = args.creator
    if args.tags is not None:
        updates["tags"] = [t.strip() for t in args.tags.split(",")]
    if args.status is not None:
        updates["status"] = args.status
    if args.date is not None:
        updates["date_finished"] = args.date
    if args.notes is not None:
        updates["notes"] = args.notes

    if not updates:
        print("No updates specified.")
        return

    result = update_entry(args.id, updates)
    print(f"✅ Updated [{args.id}] {result['title_cn']}")


def cmd_list(args):
    """List entries."""
    entries = get_all(
        type_filter=args.type,
        status_filter=args.status,
        tag_filter=args.tag,
        sort_by=args.sort or "date_finished",
        reverse=not args.ascending,
    )

    if args.limit:
        entries = entries[:args.limit]

    if not entries:
        print("No entries found.")
        return

    print(f"\n{'=' * 80}")
    print(f"{'ID':<10} {'Type':<6} {'Title':<25} {'Creator':<15} {'Rating':<7} {'Date':<8} {'Status'}")
    print(f"{'=' * 80}")

    for e in entries:
        eid = e.get("id", "")[:8]
        etype = e.get("type", "")
        title = e.get("title_cn", "")[:24]
        creator = e.get("creator", "")[:14]
        rating = e.get("rating")
        if rating:
            stars = "*" * (rating // 2) + ("+" if rating % 2 else "")
            rating_str = f"{stars} {rating}"
        else:
            rating_str = "--"
        date_str = e.get("date_finished", "") or "--"
        status = e.get("status", "")

        print(f"{eid:<10} {etype:<6} {title:<25} {creator:<15} {rating_str:<7} {date_str:<8} {status}")


def cmd_search(args):
    """Full-text search."""
    results = search(args.query)
    if not results:
        print(f"No results for '{args.query}'")
        return

    print(f"\n🔍 Found {len(results)} results for '{args.query}':\n")
    for e in results:
        stars_str = ""
        if e.get("rating"):
            r = e["rating"]
            stars_str = f" {'★'*(r//2)}{'⯪' if r%2 else ''} {r}/10"
        tags_str = " · ".join(e.get("tags", [])[:3])
        print(f"  [{e['id']}] {e['title_cn']} — {e['creator']}{stars_str}")
        if tags_str:
            print(f"       {tags_str}")
        print()


def cmd_stats(args):
    """Show statistics."""
    stats = get_stats()
    tags = get_all_tags()

    print(f"\n=== Library Statistics ===")
    print(f"{'=' * 40}")
    print(f"  Total entries:        {stats['total_entries']}")
    print(f"  Books finished:       {stats['books_finished']}")
    print(f"  Movies watched:       {stats['movies_finished']}")
    print(f"  Currently reading:    {stats['currently_reading']}")
    if stats['avg_book_rating']:
        print(f"  Avg book rating:      {stats['avg_book_rating']}/10")
    if stats['avg_movie_rating']:
        print(f"  Avg movie rating:     {stats['avg_movie_rating']}/10")
    print(f"  This year:            {stats['entries_this_year']}")
    print(f"\n  Top Tags:")
    for tag, count in list(tags.items())[:12]:
        bar = "#" * min(count, 20)
        print(f"    {tag:<12} {bar} {count}")


def cmd_tags(args):
    """List all tags."""
    tags = get_all_tags()
    print(f"\n🏷️  All Tags ({len(tags)}):\n")
    for tag, count in tags.items():
        print(f"  {tag} ({count})")


def main():
    parser = argparse.ArgumentParser(description="Personal Book & Movie Library Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # --- add ---
    p_add = subparsers.add_parser("add", help="Add a new entry")
    p_add.add_argument("type", choices=["book", "movie", "music"], help="Entry type")
    p_add.add_argument("--title", required=True, help="Title (Chinese)")
    p_add.add_argument("--title-orig", help="Original title")
    p_add.add_argument("--creator", help="Author/Director")
    p_add.add_argument("--creator-orig", help="Original name of creator")
    p_add.add_argument("--date", help="Date finished (YYYY-MM)")
    p_add.add_argument("--rating", type=int, choices=range(1, 11), help="Rating 1-10")
    p_add.add_argument("--tags", help="Comma-separated tags")
    p_add.add_argument("--status", choices=["finished", "reading", "to-read", "to-watch", "abandoned"], default="finished")
    p_add.add_argument("--notes", help="Personal notes")
    p_add.add_argument("--source", help="Source (豆瓣/推荐/自己发现)")
    p_add.add_argument("--cover", help="Path to cover image")

    # --- rate ---
    p_rate = subparsers.add_parser("rate", help="Rate an entry")
    p_rate.add_argument("id", help="Entry ID")
    p_rate.add_argument("--rating", type=int, required=True, choices=range(1, 11), help="Rating 1-10")

    # --- edit ---
    p_edit = subparsers.add_parser("edit", help="Edit an entry")
    p_edit.add_argument("id", help="Entry ID")
    p_edit.add_argument("--title")
    p_edit.add_argument("--creator")
    p_edit.add_argument("--tags", help="Comma-separated tags")
    p_edit.add_argument("--status", choices=["finished", "reading", "to-read", "to-watch", "abandoned"])
    p_edit.add_argument("--date", help="Date finished (YYYY-MM)")
    p_edit.add_argument("--notes")

    # --- delete ---
    p_del = subparsers.add_parser("delete", help="Delete an entry")
    p_del.add_argument("id", help="Entry ID")
    p_del.add_argument("--force", action="store_true", help="Skip confirmation")

    # --- list ---
    p_list = subparsers.add_parser("list", help="List entries")
    p_list.add_argument("--type", choices=["book", "movie", "music"], help="Filter by type")
    p_list.add_argument("--status", choices=["finished", "reading", "to-read", "to-watch", "abandoned"], help="Filter by status")
    p_list.add_argument("--tag", help="Filter by tag")
    p_list.add_argument("--sort", default="date_finished", help="Sort field")
    p_list.add_argument("--ascending", action="store_true", help="Sort ascending")
    p_list.add_argument("--limit", type=int, help="Limit results")

    # --- search ---
    p_search = subparsers.add_parser("search", help="Full-text search")
    p_search.add_argument("query", help="Search query")

    # --- stats ---
    subparsers.add_parser("stats", help="Show statistics")

    # --- tags ---
    subparsers.add_parser("tags", help="List all tags")

    # --- discover ---
    p_disc = subparsers.add_parser("discover", help="Run discovery engine")
    p_disc.add_argument("--save", action="store_true", help="Save report to Writing/discoveries/")

    # --- reflect ---
    p_refl = subparsers.add_parser("reflect", help="Get reflection prompts for an entry")
    p_refl.add_argument("id", help="Entry ID")
    p_refl.add_argument("--save", action="store_true", help="Save prompts to Writing/")

    # --- recommend ---
    p_rec = subparsers.add_parser("recommend", help="Get recommendations")
    p_rec.add_argument("--source", choices=["local", "web", "both"], default="both", help="Recommendation source")
    p_rec.add_argument("--type", choices=["book", "movie", "both"], default="both", help="What to recommend")
    p_rec.add_argument("--count", type=int, default=5, help="Number of recommendations")
    p_rec.add_argument("--save", action="store_true", help="Save to Writing/recommendations/")
    p_rec.add_argument("--schedule", choices=["daily", "weekly", "monthly"], help="Set up periodic delivery via cron")

    # --- export ---
    subparsers.add_parser("export", help="Regenerate GUIDE.md files")

    # --- sync ---
    subparsers.add_parser("sync", help="Scan RECORD/ folders for new entries")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    # Ensure database exists
    init_db()

    # Dispatch
    if args.command == "add":
        cmd_add(args)
    elif args.command == "rate":
        cmd_rate(args)
    elif args.command == "edit":
        cmd_edit(args)
    elif args.command == "delete":
        entry = get_by_id(args.id)
        if not entry:
            print(f"❌ Entry '{args.id}' not found")
            return
        if not args.force:
            confirm = input(f"Delete '{entry['title_cn']}' ({entry['type']})? [y/N] ")
            if confirm.lower() != "y":
                print("Cancelled.")
                return
        delete_entry(args.id)
        print(f"🗑️  Deleted [{args.id}] {entry['title_cn']}")
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "tags":
        cmd_tags(args)
    elif args.command == "discover":
        discover(save=args.save)
    elif args.command == "reflect":
        reflect_on(args.id, save=args.save)
    elif args.command == "recommend":
        if args.schedule:
            _setup_schedule(args)
        else:
            recommend(source=args.source, rec_type=args.type, count=args.count, save=args.save)
    elif args.command == "export":
        export_all()
    elif args.command == "sync":
        do_sync()


def _setup_schedule(args):
    """Print instructions for cron setup via Claude Code."""
    cron_map = {
        "daily": "0 9 * * *",
        "weekly": "7 9 * * 1",
        "monthly": "13 9 1 * *",
    }
    cron_expr = cron_map[args.schedule]
    source = args.source or "both"
    rec_type = args.type or "both"
    count = args.count or 3

    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_text = (
        f'Run: cd "{script_dir}" && python lib_cli.py recommend --source {source} '
        f'--type {rec_type} --count {count} --save && '
        f'python lib_export.py'
    )

    print(f"""
📅 To set up {args.schedule} recommendations via Claude Code CronCreate:

Use: CronCreate with:
  cron:   {cron_expr}
  prompt: {prompt_text}

Or ask Claude: "Set up a {args.schedule} recommendation for books and movies"

This will automatically save recommendations to:
  Writing/recommendations/YYYY-MM-DD.md
""")


if __name__ == "__main__":
    main()
