"""
ICS Generator  (web edition – self-contained)
==============================================
"""

from __future__ import annotations
import re
from datetime import datetime, timezone

from event_filter import CalendarEvent


def _to_ics_dt(iso: str) -> str:
    cleaned = iso.replace("-", "").replace(":", "")
    cleaned = re.sub(r"[^0-9T]", "", cleaned)
    return cleaned[:15] if len(cleaned) >= 15 else cleaned


def _esc(text: str) -> str:
    text = text.replace("\\", "\\\\")
    text = text.replace(";", "\\;")
    text = text.replace(",", "\\,")
    text = text.replace("\r\n", "\\n").replace("\n", "\\n")
    return text


def _esc_loc(text: str) -> str:
    return _esc(text)


def _fold(line: str) -> str:
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line
    parts: list[str] = []
    while len(encoded) > 75:
        cut = 75 if not parts else 74
        while cut > 0 and (encoded[cut] & 0xC0) == 0x80:
            cut -= 1
        parts.append(encoded[:cut].decode("utf-8", errors="ignore"))
        encoded = encoded[cut:]
    if encoded:
        parts.append(encoded.decode("utf-8", errors="ignore"))
    return "\r\n ".join(parts)


def generate_ics(
    events: list[CalendarEvent],
    cal_name: str = "CELCAT - UVSQ Calendar",
    tz: str = "Europe/Paris",
    prodid: str = "-//CELCAT to ICS//UVSQ Calendar//EN",
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    lines: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{prodid}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{cal_name}",
        f"X-WR-TIMEZONE:{tz}",
        "X-WR-CALDESC:University calendar from CELCAT",
    ]
    for ev in events:
        s_esc = _esc(ev.summary)
        d_esc = _esc(ev.description)
        l_esc = _esc_loc(ev.location) if ev.location else ""
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{ev.uid}")
        lines.append(f"DTSTAMP:{now}")
        lines.append(f"DTSTART:{_to_ics_dt(ev.dtstart)}")
        lines.append(f"DTEND:{_to_ics_dt(ev.dtend)}")
        lines.append(_fold(f"SUMMARY:{s_esc}"))
        lines.append(_fold(f"DESCRIPTION:{d_esc}"))
        if l_esc:
            lines.append(_fold(f"LOCATION:{l_esc}"))
        lines.append(f"COLOR:{ev.color}")
        lines.append(f"CATEGORIES:{ev.category}")
        lines.append("STATUS:CONFIRMED")
        # 30-min alarm
        lines.append("BEGIN:VALARM")
        lines.append("TRIGGER:-PT30M")
        lines.append("ACTION:DISPLAY")
        lines.append(_fold(f"DESCRIPTION:Reminder: {s_esc}"))
        lines.append("END:VALARM")
        # 1-day alarm
        lines.append("BEGIN:VALARM")
        lines.append("TRIGGER:-P1D")
        lines.append("ACTION:DISPLAY")
        lines.append(_fold(f"DESCRIPTION:Reminder: {s_esc} (Tomorrow)"))
        lines.append("END:VALARM")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
