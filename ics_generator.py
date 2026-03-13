"""
ICS Calendar Generator
======================
Generates a standards-compliant .ics file matching the exact format
of the uploaded CELCAT calendar (COLOR, VALARM reminders, etc.).
"""

from __future__ import annotations
import re
from datetime import datetime

from event_filter import CalendarEvent


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _to_ics_datetime(iso: str) -> str:
    """
    Convert "2026-01-23T09:40:00" → "20260123T094000".
    Handles both "YYYY-MM-DDTHH:MM:SS" and already-formatted strings.
    """
    cleaned = iso.replace("-", "").replace(":", "")
    # Keep only digits and the 'T'
    cleaned = re.sub(r"[^0-9T]", "", cleaned)
    # Ensure we have exactly YYYYMMDDTHHmmss (15 chars)
    if len(cleaned) >= 15:
        return cleaned[:15]
    return cleaned


def _ics_escape(text: str) -> str:
    """
    Escape a string for use inside an ICS property value.
    ICS requires: backslash, semicolons, and commas to be escaped.
    New-lines become literal \\n.
    """
    text = text.replace("\\", "\\\\")
    text = text.replace(";", "\\;")
    text = text.replace(",", "\\,")
    # Real newlines → ICS literal \n
    text = text.replace("\r\n", "\\n").replace("\n", "\\n")
    return text


def _ics_escape_location(text: str) -> str:
    """
    Escape LOCATION values.  Also encodes non-ASCII characters as
    HTML numeric character references to mirror the CELCAT output.
    """
    # First do standard escapes
    escaped = _ics_escape(text)
    # Encode selected accented characters as HTML entities (like CELCAT does)
    result: list[str] = []
    for ch in escaped:
        if ord(ch) > 127:
            result.append(f"&#{ord(ch)}\\;")
        else:
            result.append(ch)
    return "".join(result)


def _fold_line(line: str) -> str:
    """
    Fold long ICS content lines at 75 octets (RFC 5545 §3.1).
    Continuation lines begin with a single space.
    """
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line

    parts: list[str] = []
    while len(encoded) > 75:
        # Find a safe cut point (don't break multi-byte chars)
        cut = 75 if not parts else 74  # subsequent lines lose 1 byte for leading space
        while cut > 0 and (encoded[cut] & 0xC0) == 0x80:
            cut -= 1
        chunk = encoded[:cut].decode("utf-8", errors="ignore")
        parts.append(chunk)
        encoded = encoded[cut:]

    if encoded:
        parts.append(encoded.decode("utf-8", errors="ignore"))

    return "\r\n ".join(parts)


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def generate_ics(
    events: list[CalendarEvent],
    *,
    cal_name: str = "CELCAT - UVSQ Calendar",
    timezone: str = "Europe/Paris",
    prodid: str = "-//CELCAT to ICS//UVSQ Calendar//EN",
) -> str:
    """
    Build a complete ICS string from a list of ``CalendarEvent`` objects.

    The output mirrors the structure of the reference ``calendar.ics``
    produced by CELCAT (same properties, same VALARM reminders).
    """
    now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    lines: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{prodid}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{cal_name}",
        f"X-WR-TIMEZONE:{timezone}",
        "X-WR-CALDESC:University calendar from CELCAT",
    ]

    for ev in events:
        dtstart = _to_ics_datetime(ev.dtstart)
        dtend   = _to_ics_datetime(ev.dtend)

        summary_escaped     = _ics_escape(ev.summary)
        description_escaped = _ics_escape(ev.description)
        location_escaped    = _ics_escape_location(ev.location) if ev.location else ""

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{ev.uid}")
        lines.append(f"DTSTAMP:{now_stamp}")
        lines.append(f"DTSTART:{dtstart}")
        lines.append(f"DTEND:{dtend}")
        lines.append(_fold_line(f"SUMMARY:{summary_escaped}"))
        lines.append(_fold_line(f"DESCRIPTION:{description_escaped}"))
        if location_escaped:
            lines.append(_fold_line(f"LOCATION:{location_escaped}"))
        lines.append(f"COLOR:{ev.color}")
        lines.append(f"CATEGORIES:{ev.category}")
        lines.append("STATUS:CONFIRMED")

        # Reminder 30 minutes before
        lines.append("BEGIN:VALARM")
        lines.append("TRIGGER:-PT30M")
        lines.append("ACTION:DISPLAY")
        lines.append(_fold_line(f"DESCRIPTION:Reminder: {summary_escaped}"))
        lines.append("END:VALARM")

        # Reminder 1 day before
        lines.append("BEGIN:VALARM")
        lines.append("TRIGGER:-P1D")
        lines.append("ACTION:DISPLAY")
        lines.append(_fold_line(f"DESCRIPTION:Reminder: {summary_escaped} (Tomorrow)"))
        lines.append("END:VALARM")

        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def write_ics(filepath: str, ics_content: str) -> None:
    """Write the ICS content to disk."""
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        f.write(ics_content)
    print(f"[+] Calendar written to  {filepath}")
