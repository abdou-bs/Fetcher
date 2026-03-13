#!/usr/bin/env python3
"""
generate.py — Standalone calendar generator for GitHub Actions.

Reads calendar-config.json, fetches live data from CELCAT,
and writes calendar.ics to the repo root.
"""

import json, sys, os

# Allow importing from web/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "web"))

from celcat_client import CelcatClient
from event_filter import filter_events
from ics_generator import generate_ics


def main():
    config_path = os.path.join(os.path.dirname(__file__), "calendar-config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    start_date = cfg.get("startDate", "2025-01-13")
    end_date = cfg.get("endDate", "2025-06-30")
    mod_list = cfg.get("modules", [])

    if not mod_list:
        print("Error: No modules in calendar-config.json")
        sys.exit(1)

    # Build modules dict
    modules = {}
    for m in mod_list:
        code = m["code"].upper()
        grp = int(m.get("tdGroup", 1))
        modules[code] = {
            "name": m.get("name", code),
            "td_group": grp,
            "td_group_label": f"M1 Info gr. {grp}",
        }

    print(f"Modules: {', '.join(modules.keys())}")
    print(f"Date range: {start_date} → {end_date}")

    # Fetch groups from CELCAT
    client = CelcatClient()
    client.initialize()
    all_groups = client.search_groups("M1 AMIS")
    print(f"Found {len(all_groups)} CELCAT groups")

    # Select relevant federation IDs
    needed = {m["td_group_label"].lower() for m in modules.values()}
    fed_ids = []
    for g in all_groups:
        txt = g.get("text", "").lower()
        # CM group: contains "m1 info" without "gr."
        if ("m1 info]" in txt or "m1 info)" in txt) and "gr." not in txt:
            fed_ids.append(g["id"])
            continue
        for lbl in needed:
            if lbl in txt:
                fed_ids.append(g["id"])
                break

    if not fed_ids:
        print("Error: No matching CELCAT groups found")
        sys.exit(1)

    print(f"Fetching events from {len(fed_ids)} groups...")
    raw_events = client.get_calendar_data(fed_ids, start_date, end_date)
    print(f"Raw events: {len(raw_events)}")

    # Filter
    filtered = filter_events(raw_events, modules, include_exams=True)
    print(f"Filtered events: {len(filtered)}")

    if not filtered:
        print("Warning: No events matched — writing empty calendar")

    # Generate .ics
    ics = generate_ics(filtered)
    out_path = os.path.join(os.path.dirname(__file__), "calendar.ics")
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.write(ics)

    print(f"Written to {out_path} ({len(ics)} bytes, {len(filtered)} events)")


if __name__ == "__main__":
    main()
