#!/usr/bin/env python3
"""
CELCAT UVSQ Calendar Fetcher – Web Edition
==========================================
"""

from __future__ import annotations
import base64, html, io, json, re
from flask import Flask, render_template, request, jsonify, send_file

from celcat_client import CelcatClient
from event_filter import filter_events
from ics_generator import generate_ics

app = Flask(__name__)

DEFAULT_START = "2026-01-19"
DEFAULT_END   = "2026-08-31"


def _encode_config(cfg: dict) -> str:
    """Compact JSON → base64url token (no padding)."""
    raw = json.dumps(cfg, separators=(",", ":"), ensure_ascii=True)
    return base64.urlsafe_b64encode(raw.encode()).rstrip(b"=").decode()


def _decode_config(token: str) -> dict:
    """base64url token → dict.  Raises on bad input."""
    pad = 4 - len(token) % 4
    if pad != 4:
        token += "=" * pad
    raw = base64.urlsafe_b64decode(token)
    return json.loads(raw)


# =====================================================================
# Pages
# =====================================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/guide")
def guide():
    return render_template("guide.html")


# =====================================================================
# API – live data from CELCAT
# =====================================================================

@app.route("/api/groups", methods=["GET"])
def api_groups():
    """Fetch all M1 Info groups from CELCAT live."""
    search = request.args.get("q", "M1 AMIS")
    try:
        client = CelcatClient()
        client.initialize()
        raw = client.search_groups(search, page_size=200)
        groups = [{"id": g["id"], "text": html.unescape(g.get("text", ""))} for g in raw]
        return jsonify({"ok": True, "groups": groups})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/modules", methods=["POST"])
def api_modules():
    """
    Given group federation IDs, fetch events and extract all
    distinct module codes + names.
    """
    data = request.get_json(silent=True) or {}
    fed_ids = data.get("federationIds", [])
    start   = data.get("start", DEFAULT_START)
    end     = data.get("end", DEFAULT_END)

    if not fed_ids:
        return jsonify({"ok": False, "error": "No group IDs provided"}), 400

    try:
        client = CelcatClient()
        client.initialize()
        events = client.get_calendar_data(fed_ids, start, end)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

    code_re = re.compile(r"(MIN\d{5}|MSANGS\w+)", re.IGNORECASE)
    name_re = re.compile(
        r"((?:MIN\d{5}|MSANGS\w+))\s*[-–]\s*([^\[\]<>]+?)(?:\s*\[|$)",
        re.IGNORECASE,
    )

    code_names: dict[str, str] = {}
    for ev in events:
        blob = (ev.get("description", "") + " " + (ev.get("title") or ""))
        for m in name_re.finditer(blob):
            code = m.group(1).upper()
            name = m.group(2).strip()
            if code not in code_names or len(name) > len(code_names[code]):
                code_names[code] = name
        for c in code_re.findall(blob):
            cu = c.upper()
            if cu not in code_names:
                code_names[cu] = cu

    modules = sorted(
        [{"code": c, "name": html.unescape(n)} for c, n in code_names.items()],
        key=lambda m: m["code"],
    )
    return jsonify({"ok": True, "modules": modules, "eventCount": len(events)})


# =====================================================================
# Generate .ics
# =====================================================================

@app.route("/api/generate", methods=["POST"])
def api_generate():
    """Accept JSON, fetch + filter + return .ics download."""
    data = request.get_json(silent=True) or {}
    start_date = data.get("startDate", DEFAULT_START)
    end_date   = data.get("endDate", DEFAULT_END)
    mod_list   = data.get("modules", [])

    if not mod_list:
        return jsonify({"ok": False, "error": "No modules selected"}), 400

    modules: dict[str, dict] = {}
    for m in mod_list:
        code = m["code"].upper()
        grp  = int(m.get("tdGroup", 1))
        modules[code] = {
            "name": m.get("name", code),
            "td_group": grp,
            "td_group_label": f"M1 Info gr. {grp}",
        }

    try:
        client = CelcatClient()
        client.initialize()
        all_groups = client.search_groups("M1 AMIS")
    except Exception as exc:
        return jsonify({"ok": False, "error": f"CELCAT error: {exc}"}), 500

    needed = {m["td_group_label"].lower() for m in modules.values()}
    fed_ids: list[str] = []
    for g in all_groups:
        t = g.get("text", "").lower()
        if ("m1 info]" in t or "m1 info)" in t) and "gr." not in t:
            fed_ids.append(g["id"])
            continue
        for lbl in needed:
            if lbl in t:
                fed_ids.append(g["id"])
                break

    if not fed_ids:
        return jsonify({"ok": False, "error": "No matching CELCAT groups found"}), 500

    try:
        raw_events = client.get_calendar_data(fed_ids, start_date, end_date)
    except Exception as exc:
        return jsonify({"ok": False, "error": f"Fetch failed: {exc}"}), 500

    filtered = filter_events(raw_events, modules, include_exams=True)
    if not filtered:
        return jsonify({"ok": False, "error": "No events matched"}), 404

    ics = generate_ics(filtered)
    buf = io.BytesIO(ics.encode("utf-8"))
    buf.seek(0)
    return send_file(buf, mimetype="text/calendar", as_attachment=True,
                     download_name="my_calendar.ics")


# =====================================================================
# Subscribe: create subscription URL
# =====================================================================

@app.route("/api/subscribe", methods=["POST"])
def api_subscribe():
    """Return a subscription URL that encodes the user's selection."""
    data = request.get_json(silent=True) or {}
    mod_list   = data.get("modules", [])
    start_date = data.get("startDate", DEFAULT_START)
    end_date   = data.get("endDate", DEFAULT_END)

    if not mod_list:
        return jsonify({"ok": False, "error": "No modules selected"}), 400

    compact = {
        "s": start_date,
        "e": end_date,
        "m": [{"c": m["code"], "g": int(m.get("tdGroup", 1))} for m in mod_list],
    }
    token = _encode_config(compact)
    base  = request.host_url.rstrip("/")
    url   = f"{base}/cal/{token}.ics"
    webcal = url.replace("http://", "webcal://").replace("https://", "webcal://")
    return jsonify({"ok": True, "url": url, "webcal": webcal})


# =====================================================================
# Update: upload old .ics → get refreshed .ics
# =====================================================================

_ICS_CODE_RE = re.compile(r"(MIN\d{5}|MSANGS\w+)", re.IGNORECASE)
_ICS_GROUP_RE = re.compile(r"M1\s*Info\s*gr\.\s*(\d+)", re.IGNORECASE)


@app.route("/api/update", methods=["POST"])
def api_update():
    """Parse uploaded .ics, extract modules/groups, fetch fresh data, return new .ics."""
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "No file uploaded"}), 400

    f = request.files["file"]
    if not f.filename or not f.filename.lower().endswith(".ics"):
        return jsonify({"ok": False, "error": "Please upload a .ics file"}), 400

    try:
        content = f.read().decode("utf-8", errors="replace")
    except Exception:
        return jsonify({"ok": False, "error": "Could not read file"}), 400

    if len(content) > 2_000_000:  # 2 MB safety limit
        return jsonify({"ok": False, "error": "File too large"}), 400

    # Extract module codes
    codes_found: set[str] = set()
    for m in _ICS_CODE_RE.finditer(content):
        codes_found.add(m.group(1).upper())

    if not codes_found:
        return jsonify({"ok": False, "error": "No module codes found in the file"}), 400

    # Extract TD group numbers per module (look near each code mention)
    code_groups: dict[str, int] = {}
    for code in codes_found:
        # Find all occurrences of this code and look for nearby group references
        for cm in re.finditer(re.escape(code), content, re.IGNORECASE):
            chunk = content[max(0, cm.start() - 200):cm.end() + 200]
            gm = _ICS_GROUP_RE.search(chunk)
            if gm:
                code_groups[code] = int(gm.group(1))
                break

    # Default group = 1 for codes where we couldn't detect it
    modules: dict[str, dict] = {}
    for code in codes_found:
        grp = code_groups.get(code, 1)
        modules[code] = {
            "name": code,
            "td_group": grp,
            "td_group_label": f"M1 Info gr. {grp}",
        }

    # Extract date range from existing events
    dt_matches = re.findall(r"DTSTART:(\d{8})", content)
    if dt_matches:
        dates_sorted = sorted(dt_matches)
        start_date = f"{dates_sorted[0][:4]}-{dates_sorted[0][4:6]}-{dates_sorted[0][6:8]}"
        end_date = f"{dates_sorted[-1][:4]}-{dates_sorted[-1][4:6]}-{dates_sorted[-1][6:8]}"
    else:
        start_date = DEFAULT_START
        end_date = DEFAULT_END

    try:
        client = CelcatClient()
        client.initialize()
        all_groups = client.search_groups("M1 AMIS")
    except Exception as exc:
        return jsonify({"ok": False, "error": f"CELCAT error: {exc}"}), 500

    needed = {m["td_group_label"].lower() for m in modules.values()}
    fed_ids: list[str] = []
    for g in all_groups:
        t = g.get("text", "").lower()
        if ("m1 info]" in t or "m1 info)" in t) and "gr." not in t:
            fed_ids.append(g["id"])
            continue
        for lbl in needed:
            if lbl in t:
                fed_ids.append(g["id"])
                break

    if not fed_ids:
        return jsonify({"ok": False, "error": "No matching CELCAT groups found"}), 500

    try:
        raw_events = client.get_calendar_data(fed_ids, start_date, end_date)
    except Exception as exc:
        return jsonify({"ok": False, "error": f"Fetch failed: {exc}"}), 500

    filtered = filter_events(raw_events, modules, include_exams=True)
    if not filtered:
        return jsonify({"ok": False, "error": "No events matched"}), 404

    # Build summary of what was detected
    detected = {"codes": sorted(codes_found), "groups": code_groups,
                "start": start_date, "end": end_date, "events": len(filtered)}

    ics = generate_ics(filtered)
    buf = io.BytesIO(ics.encode("utf-8"))
    buf.seek(0)
    return send_file(buf, mimetype="text/calendar", as_attachment=True,
                     download_name="my_calendar_updated.ics")


# =====================================================================
# Subscription endpoint: live .ics from encoded config
# =====================================================================

@app.route("/cal/<token>.ics")
def cal_subscription(token: str):
    """Decode config token, fetch fresh CELCAT data, return .ics."""
    try:
        cfg = _decode_config(token)
    except Exception:
        return "Invalid subscription link", 400

    start_date = cfg.get("s", DEFAULT_START)
    end_date   = cfg.get("e", DEFAULT_END)
    mods_raw   = cfg.get("m", [])

    if not mods_raw:
        return "No modules in subscription", 400

    modules: dict[str, dict] = {}
    for m in mods_raw:
        code = m["c"].upper()
        grp  = int(m.get("g", 1))
        modules[code] = {
            "name": code,
            "td_group": grp,
            "td_group_label": f"M1 Info gr. {grp}",
        }

    try:
        client = CelcatClient()
        client.initialize()
        all_groups = client.search_groups("M1 AMIS")
    except Exception as exc:
        return f"CELCAT error: {exc}", 502

    needed = {m["td_group_label"].lower() for m in modules.values()}
    fed_ids: list[str] = []
    for g in all_groups:
        txt = g.get("text", "").lower()
        if ("m1 info]" in txt or "m1 info)" in txt) and "gr." not in txt:
            fed_ids.append(g["id"])
            continue
        for lbl in needed:
            if lbl in txt:
                fed_ids.append(g["id"])
                break

    if not fed_ids:
        return "No matching CELCAT groups", 404

    try:
        raw_events = client.get_calendar_data(fed_ids, start_date, end_date)
    except Exception as exc:
        return f"Fetch failed: {exc}", 502

    filtered = filter_events(raw_events, modules, include_exams=True)
    ics = generate_ics(filtered) if filtered else generate_ics([])
    buf = io.BytesIO(ics.encode("utf-8"))
    buf.seek(0)
    resp = send_file(buf, mimetype="text/calendar",
                     download_name="calendar.ics")
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


if __name__ == "__main__":
    print("=" * 50)
    print("  UVSQ Calendar Fetcher")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)
