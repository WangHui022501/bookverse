#!/usr/bin/env python
"""
Flask API server for personal library management.
Run: python tools/server.py
Then open: http://localhost:5090
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request, send_from_directory
from lib_db import (
    add_entry, update_entry, delete_entry, get_by_id,
    get_all, search, get_stats, get_all_tags,
    get_entries_for_journal, get_viz_data,
    update_extracts, add_extract, update_mood_tags,
    get_preset_moods, update_daily_reading,
    check_in, check_out, get_active_session, get_session_history
)
from lib_export import export_all
from lib_discover import _build_discovery_report, _generate_prompts
from lib_recommend import _local_recommend
from lib_article import generate_article, save_article

app = Flask(__name__, static_folder=None)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── Static ──────────────────────────────────────────────────
@app.route("/")
def index():
    """Serve the frontend HTML page."""
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


# ── API: Entries ────────────────────────────────────────────
@app.route("/api/entries", methods=["GET"])
def api_entries():
    """List entries with filters."""
    entries = get_all(
        type_filter=request.args.get("type"),
        status_filter=request.args.get("status"),
        tag_filter=request.args.get("tag"),
        sort_by=request.args.get("sort", "date_finished"),
        reverse=request.args.get("order", "desc") == "desc",
    )
    limit = request.args.get("limit", type=int)
    if limit:
        entries = entries[:limit]
    return jsonify(entries)


@app.route("/api/entries/<entry_id>", methods=["GET"])
def api_get_entry(entry_id):
    """Get single entry."""
    entry = get_by_id(entry_id)
    if not entry:
        return jsonify({"error": "Not found"}), 404
    return jsonify(entry)


@app.route("/api/entries", methods=["POST"])
def api_add_entry():
    """Add a new entry."""
    data = request.get_json()
    if not data or not data.get("title_cn"):
        return jsonify({"error": "title_cn is required"}), 400
    entry = add_entry(data)
    return jsonify(entry), 201


@app.route("/api/entries/<entry_id>", methods=["PUT"])
def api_update_entry(entry_id):
    """Update an entry."""
    data = request.get_json()
    entry = update_entry(entry_id, data)
    if not entry:
        return jsonify({"error": "Not found"}), 404
    return jsonify(entry)


@app.route("/api/entries/<entry_id>", methods=["DELETE"])
def api_delete_entry(entry_id):
    """Delete an entry."""
    ok = delete_entry(entry_id)
    if not ok:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"deleted": True})


# ── API: Search ─────────────────────────────────────────────
@app.route("/api/search")
def api_search():
    q = request.args.get("q", "")
    if not q:
        return jsonify([])
    return jsonify(search(q))


# ── API: Stats & Tags ───────────────────────────────────────
@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())


@app.route("/api/tags")
def api_tags():
    return jsonify(get_all_tags())


# ── API: Discover ───────────────────────────────────────────
@app.route("/api/discover")
def api_discover():
    report = _build_discovery_report()
    return jsonify({"report": report})


# ── API: Reflect ────────────────────────────────────────────
@app.route("/api/reflect/<entry_id>")
def api_reflect(entry_id):
    entry = get_by_id(entry_id)
    if not entry:
        return jsonify({"error": "Not found"}), 404
    prompts = _generate_prompts(entry)
    return jsonify({"entry": entry, "prompts": prompts})


# ── API: Recommend ──────────────────────────────────────────
@app.route("/api/recommend")
def api_recommend():
    rec_type = request.args.get("type", "both")
    count = request.args.get("count", 5, type=int)
    results = _local_recommend(rec_type=rec_type, count=count)
    return jsonify([{k: v for k, v in r.items() if k != "score"} for r in results])


# ── API: Export ─────────────────────────────────────────────
@app.route("/api/export", methods=["POST"])
def api_export():
    try:
        export_all()
        return jsonify({"success": True, "message": "GUIDE files updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── API: Static files (cover images) ────────────────────────
@app.route("/record/<path:filepath>")
def serve_record(filepath):
    """Serve files from RECORD/ folder."""
    record_dir = os.path.join(BASE_DIR, "RECORD")
    return send_from_directory(record_dir, filepath)


# ── API: Journal ───────────────────────────────────────────
@app.route("/api/journal")
def api_journal():
    """Return entries grouped by month for the journal timeline."""
    type_filter = request.args.get("type", "book")
    return jsonify(get_entries_for_journal(type_filter=type_filter))


# ── API: Extracts ──────────────────────────────────────────
@app.route("/api/entries/<entry_id>/extracts", methods=["PUT"])
def api_update_extracts(entry_id):
    """Replace all extracts for an entry."""
    data = request.get_json()
    if not data or "extracts" not in data:
        return jsonify({"error": "extracts list is required"}), 400
    entry = update_extracts(entry_id, data["extracts"])
    if not entry:
        return jsonify({"error": "Not found"}), 404
    return jsonify(entry)


@app.route("/api/entries/<entry_id>/extracts", methods=["POST"])
def api_add_extract(entry_id):
    """Append a single extract to an entry."""
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "extract text is required"}), 400
    extract = {
        "text": data["text"],
        "page": data.get("page", ""),
        "note": data.get("note", ""),
        "added_at": data.get("added_at", ""),
    }
    entry = add_extract(entry_id, extract)
    if not entry:
        return jsonify({"error": "Not found"}), 404
    return jsonify(entry), 201


# ── API: Daily Reading ─────────────────────────────────────
@app.route("/api/entries/<entry_id>/daily-reading", methods=["PUT"])
def api_update_daily_reading(entry_id):
    """Record daily reading time for an entry."""
    data = request.get_json()
    if not data or "date" not in data or "minutes" not in data:
        return jsonify({"error": "date and minutes are required"}), 400
    entry = update_daily_reading(entry_id, data["date"], int(data["minutes"]))
    if not entry:
        return jsonify({"error": "Not found"}), 404
    return jsonify(entry)


# ── API: Check-in / Check-out Sessions ────────────────────
@app.route("/api/sessions/check-in", methods=["POST"])
def api_check_in():
    """Start a reading session."""
    data = request.get_json()
    if not data or "entry_id" not in data:
        return jsonify({"error": "entry_id is required"}), 400
    session_date = data.get("date", "")
    entry = check_in(data["entry_id"], session_date if session_date else None)
    if not entry:
        return jsonify({"error": "Not found"}), 404
    return jsonify(entry)


@app.route("/api/sessions/check-out", methods=["POST"])
def api_check_out():
    """End a reading session."""
    data = request.get_json()
    if not data or "entry_id" not in data:
        return jsonify({"error": "entry_id is required"}), 400
    entry = check_out(data["entry_id"])
    if not entry:
        return jsonify({"error": "Not found"}), 404
    return jsonify(entry)


@app.route("/api/sessions/active")
def api_active_session():
    """Get the currently active reading session."""
    session = get_active_session()
    return jsonify(session)


@app.route("/api/entries/<entry_id>/sessions")
def api_get_sessions(entry_id):
    """Get all reading sessions for an entry."""
    sessions = get_session_history(entry_id)
    total = sum(s.get("duration", 0) for s in sessions)
    return jsonify({"sessions": sessions, "total_minutes": total, "count": len(sessions)})


# ── API: Mood Tags ─────────────────────────────────────────
@app.route("/api/entries/<entry_id>/moods", methods=["PUT"])
def api_update_moods(entry_id):
    """Update mood tags for an entry."""
    data = request.get_json()
    if not data or "mood_tags" not in data:
        return jsonify({"error": "mood_tags list is required"}), 400
    entry = update_mood_tags(entry_id, data["mood_tags"])
    if not entry:
        return jsonify({"error": "Not found"}), 404
    return jsonify(entry)


@app.route("/api/moods/presets")
def api_preset_moods():
    """Return the preset list of mood tags."""
    return jsonify(get_preset_moods())


# ── API: Visualization ─────────────────────────────────────
@app.route("/api/viz")
def api_viz():
    """Return all visualization data."""
    year = request.args.get("year")
    return jsonify(get_viz_data(year=year))


# ── API: Article Generation ────────────────────────────────
@app.route("/api/article/generate", methods=["POST"])
def api_generate_article():
    """Generate a 小红书-style article."""
    data = request.get_json() or {}
    entry_ids = data.get("entry_ids", [])
    article_type = data.get("type", "single")
    options = data.get("options", {})
    result = generate_article(entry_ids, article_type, options)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/article/save", methods=["POST"])
def api_save_article():
    """Save generated article to Writing/ folder."""
    data = request.get_json() or {}
    markdown = data.get("markdown", "")
    filename = data.get("filename")
    article_type = data.get("article_type", "article")
    if not markdown:
        return jsonify({"error": "markdown content is required"}), 400
    try:
        filepath = save_article(markdown, filename, article_type)
        return jsonify({"success": True, "filepath": filepath})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── API: Cover Search ──────────────────────────────────────
@app.route("/api/cover/search")
def api_search_cover():
    """Search for book covers via Open Library API."""
    import urllib.request
    import urllib.parse

    title = request.args.get("title", "")
    creator = request.args.get("creator", "")
    if not title:
        return jsonify({"error": "title is required"}), 400

    results = []
    try:
        # Search Open Library by title + author
        q = title
        if creator:
            q += " " + creator
        url = "https://openlibrary.org/search.json?q=" + urllib.parse.quote(q) + "&limit=3"
        req = urllib.request.Request(url, headers={"User-Agent": "ReadingJournal/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
        for doc in data.get("docs", [])[:3]:
            olid = doc.get("cover_edition_key") or doc.get("edition_key", [None])[0]
            cover_url = ""
            if olid:
                cover_url = f"https://covers.openlibrary.org/b/olid/{olid}-M.jpg"
            results.append({
                "title": doc.get("title", ""),
                "author": ", ".join(doc.get("author_name", [])),
                "cover_url": cover_url,
                "year": doc.get("first_publish_year", ""),
            })
    except Exception as e:
        # Open Library failed — try Google Books as fallback
        pass

    # Fallback: construct a Douban search link for manual lookup
    douban_url = f"https://search.douban.com/book/subject_search?search_text={urllib.parse.quote(title)}"

    return jsonify({"results": results, "douban_search": douban_url})


# ── Main ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Personal Library Manager")
    print(f"  Open: http://localhost:5090")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5090, debug=True)