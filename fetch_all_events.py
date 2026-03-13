#!/usr/bin/env python3
"""
Fetch ALL M1 Informatique S2 events from CELCAT and save as JSON.
Used by the client-side tool on GitHub Pages to generate .ics files.
"""

import json
import sys
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://edt.uvsq.fr"
SEARCH_TERM = "m1 info"
START_DATE = "2025-01-13"
END_DATE = "2025-08-31"
OUTPUT_FILE = "celcat-data.json"

RES_TYPE_GROUPS = 103


def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    })

    # 1. Get session + anti-forgery token
    resp = session.get(
        BASE_URL,
        headers={"Accept": "text/html,application/xhtml+xml"},
        timeout=30,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    inp = soup.find("input", {"name": "__RequestVerificationToken"})
    token = inp["value"] if inp else ""
    if not token:
        print("Warning: no anti-forgery token found", file=sys.stderr)

    # 2. Search groups
    data = {
        "myResources": "false",
        "searchTerm": SEARCH_TERM,
        "pageSize": "10000",
        "pageNumber": "1",
        "resType": str(RES_TYPE_GROUPS),
    }
    if token:
        data["__RequestVerificationToken"] = token
    resp = session.post(
        f"{BASE_URL}/Home/ReadResourceListItems",
        data=data,
        headers={
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
        },
        timeout=30,
    )
    resp.raise_for_status()
    groups = resp.json().get("results", [])
    fed_ids = [g["id"] for g in groups]
    print(f"Found {len(groups)} groups, {len(fed_ids)} federation IDs")

    if not fed_ids:
        print("No groups found, aborting.", file=sys.stderr)
        sys.exit(1)

    # 3. Fetch calendar data
    form = [
        ("start", START_DATE),
        ("end", END_DATE),
        ("resType", str(RES_TYPE_GROUPS)),
        ("calView", "agendaWeek"),
        ("colourScheme", "3"),
    ]
    if token:
        form.append(("__RequestVerificationToken", token))
    for fid in fed_ids:
        form.append(("federationIds[]", fid))

    resp = session.post(
        f"{BASE_URL}/Home/GetCalendarData",
        data=form,
        headers={
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
        timeout=60,
    )
    resp.raise_for_status()
    events = resp.json()
    print(f"Fetched {len(events)} events")

    # 4. Save
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False)
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
