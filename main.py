#!/usr/bin/env python3
"""
CELCAT UVSQ Calendar Fetcher – main entry point
=================================================
Usage
-----
    # 1) Discover your group federation IDs (run once)
    python main.py --discover

    # 2) Fetch & generate your personal ICS calendar
    python main.py --fetch

    # 3) Both in one go (discover → auto-select → fetch)
    python main.py --auto

    # 4) If you already know your federation IDs, put them in
    #    FEDERATION_IDS below and simply run:
    python main.py --fetch
"""

from __future__ import annotations

import argparse
import re
import sys
import json
from pathlib import Path

import config
from celcat_client import CelcatClient
from event_filter import filter_events
from ics_generator import generate_ics, write_ics


# =====================================================================
# If you already know your federation IDs, paste them here so that
# --fetch works without --discover first.
# You can find them by running:  python main.py --discover
# =====================================================================
FEDERATION_IDS: list[str] = [
    # Example (replace with real IDs from --discover):
    # "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
]

# Cache file so you don't need to discover every time
_CACHE_FILE = Path(__file__).with_name(".federation_ids.json")


# ------------------------------------------------------------------
# Discover
# ------------------------------------------------------------------

def cmd_discover(client: CelcatClient) -> list[dict]:
    """Search CELCAT for groups matching the programme and print them."""
    client.initialize()
    results = client.discover_groups(config.PROGRAMME_SEARCH_TERM)

    if not results:
        print("\n[!] No groups found. Try changing PROGRAMME_SEARCH_TERM in config.py")
        return []

    print("Copy the federation ID(s) that correspond to your programme")
    print("into the FEDERATION_IDS list in main.py (or let --auto pick them).\n")
    return results


# ------------------------------------------------------------------
# Auto-select federation IDs from discovered groups
# ------------------------------------------------------------------

def auto_select_ids(groups: list[dict], modules: dict) -> list[str]:
    """
    Automatically pick the federation IDs whose label matches the
    student's enrolled groups.

    Strategy:
        • Include the **main programme group** (no "gr." suffix) to
          capture CM (lecture) events.
        • Include each **specific TD group** referenced in config.MODULES.
    """
    needed_labels: set[str] = set()
    for mod in modules.values():
        lbl = mod.get("td_group_label", "")
        if lbl:
            needed_labels.add(lbl.lower())

    selected: list[str] = []
    selected_labels: list[str] = []

    for g in groups:
        text: str = g.get("text", "")
        text_lower = text.lower()

        # Main programme group (no "gr." → catches CMs)
        if "m1 info]" in text_lower and "gr." not in text_lower:
            selected.append(g["id"])
            selected_labels.append(text)
            continue

        # Specific TD groups
        for lbl in needed_labels:
            if lbl in text_lower:
                selected.append(g["id"])
                selected_labels.append(text)
                break

    if selected:
        print(f"\n[+] Auto-selected {len(selected)} group(s):")
        for lbl in selected_labels:
            print(f"    • {lbl}")
        print()
    else:
        print("[!] Could not auto-select any groups.")
        print("    → Run  python main.py --discover  and manually set FEDERATION_IDS.\n")

    return selected


# ------------------------------------------------------------------
# Fetch
# ------------------------------------------------------------------

def cmd_fetch(client: CelcatClient, fed_ids: list[str]) -> None:
    """Fetch calendar data, filter, and write the .ics file."""
    if not fed_ids:
        print("[!] No federation IDs provided.")
        print("    → Run  python main.py --discover  first, or use --auto.")
        sys.exit(1)

    client.initialize()

    raw_events = client.get_calendar_data(
        federation_ids=fed_ids,
        start_date=config.FETCH_START_DATE,
        end_date=config.FETCH_END_DATE,
    )

    if not raw_events:
        print("[!] CELCAT returned 0 events. Check your federation IDs and date range.")
        sys.exit(1)

    filtered = filter_events(raw_events, config.MODULES, config.COLORS)

    if not filtered:
        print("[!] All events were filtered out. Check your config.MODULES settings.")
        sys.exit(1)

    ics_content = generate_ics(
        filtered,
        cal_name=config.CALENDAR_NAME,
        timezone=config.CALENDAR_TIMEZONE,
        prodid=config.CALENDAR_PRODID,
    )

    out_path = Path(__file__).with_name(config.OUTPUT_ICS_FILE)
    write_ics(str(out_path), ics_content)

    # Summary
    print(f"\n{'='*60}")
    print(f"  Calendar saved: {out_path.name}")
    print(f"  Total events:   {len(filtered)}")
    cats = {}
    for e in filtered:
        cats[e.category] = cats.get(e.category, 0) + 1
    for cat, count in sorted(cats.items()):
        print(f"    {cat}: {count}")
    mods = {}
    for e in filtered:
        for c in e.module_codes:
            mods[c] = mods.get(c, 0) + 1
    print(f"  Modules:")
    for mod, count in sorted(mods.items()):
        name = config.MODULES.get(mod, {}).get("name", mod)
        print(f"    {mod} ({name}): {count}")
    print(f"{'='*60}\n")


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

def load_cached_ids() -> list[str]:
    """Load previously discovered federation IDs from cache."""
    if _CACHE_FILE.exists():
        try:
            return json.loads(_CACHE_FILE.read_text())
        except Exception:
            pass
    return []


def save_cached_ids(ids: list[str]) -> None:
    """Save federation IDs to cache file."""
    _CACHE_FILE.write_text(json.dumps(ids, indent=2))
    print(f"[+] Federation IDs cached in {_CACHE_FILE.name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch your CELCAT UVSQ calendar and generate a personal .ics file."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--discover",
        action="store_true",
        help="Search CELCAT for groups and display their federation IDs.",
    )
    group.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch calendar using known federation IDs and produce the .ics file.",
    )
    group.add_argument(
        "--auto",
        action="store_true",
        help="Discover groups, auto-select IDs, fetch calendar, and generate .ics.",
    )
    args = parser.parse_args()

    client = CelcatClient(config.CELCAT_BASE_URL)

    # --discover
    if args.discover:
        cmd_discover(client)
        return

    # --fetch
    if args.fetch:
        fed_ids = FEDERATION_IDS or load_cached_ids()
        cmd_fetch(client, fed_ids)
        return

    # --auto (discover → auto-select → fetch)
    if args.auto:
        client.initialize()
        groups = client.discover_groups(config.PROGRAMME_SEARCH_TERM)
        if not groups:
            sys.exit(1)

        fed_ids = auto_select_ids(groups, config.MODULES)
        if not fed_ids:
            sys.exit(1)

        save_cached_ids(fed_ids)

        # Re-use the same initialised client for fetching
        raw_events = client.get_calendar_data(
            federation_ids=fed_ids,
            start_date=config.FETCH_START_DATE,
            end_date=config.FETCH_END_DATE,
        )

        if not raw_events:
            print("[!] CELCAT returned 0 events.")
            sys.exit(1)

        filtered = filter_events(raw_events, config.MODULES, config.COLORS)

        if not filtered:
            print("[!] All events were filtered out.")
            sys.exit(1)

        ics_content = generate_ics(
            filtered,
            cal_name=config.CALENDAR_NAME,
            timezone=config.CALENDAR_TIMEZONE,
            prodid=config.CALENDAR_PRODID,
        )

        out_path = Path(__file__).with_name(config.OUTPUT_ICS_FILE)
        write_ics(str(out_path), ics_content)

        # Summary
        print(f"\n{'='*60}")
        print(f"  Calendar saved: {out_path.name}")
        print(f"  Total events:   {len(filtered)}")
        cats = {}
        for e in filtered:
            cats[e.category] = cats.get(e.category, 0) + 1
        for cat, count in sorted(cats.items()):
            print(f"    {cat}: {count}")
        mods = {}
        for e in filtered:
            for c in e.module_codes:
                mods[c] = mods.get(c, 0) + 1
        print(f"  Modules:")
        for mod, count in sorted(mods.items()):
            name = config.MODULES.get(mod, {}).get("name", mod)
            print(f"    {mod} ({name}): {count}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
