"""
Event Filter
=============
Filters raw CELCAT events so that only the courses and TD groups
relevant to a specific student are kept.
"""

from __future__ import annotations
import re
import html
from dataclasses import dataclass, field


# ------------------------------------------------------------------
# Lightweight event representation
# ------------------------------------------------------------------
@dataclass
class CalendarEvent:
    """Normalised representation of a single calendar event."""
    uid: str
    dtstart: str            # "YYYY-MM-DDTHH:MM:SS"
    dtend: str
    summary: str            # e.g. "CM - Simulation - MIN17212"
    description: str        # multi-line ICS description
    location: str
    color: str
    category: str           # CM, TD, TP …
    module_codes: list[str] = field(default_factory=list)
    group_labels: list[str] = field(default_factory=list)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
_MODULE_CODE_RE = re.compile(
    r"(MIN\d{5}|MSANGS\w+)",
    re.IGNORECASE,
)

_GROUP_RE = re.compile(
    r"M1\s+Info\s+gr\.\s*(\d+)",
    re.IGNORECASE,
)


def _extract_module_codes(text: str) -> list[str]:
    """Return all module codes found in *text*."""
    return list({m.upper() for m in _MODULE_CODE_RE.findall(text)})


def _extract_group_numbers(text: str) -> list[int]:
    """Return all group numbers (e.g. 1, 2, 3) found in *text*."""
    return [int(n) for n in _GROUP_RE.findall(text)]


def _clean_html(raw: str) -> str:
    """Strip HTML tags and decode entities."""
    text = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def _event_category(raw_event: dict) -> str:
    """Determine the event category (CM, TD, TP …)."""
    # CELCAT may expose it directly
    cat = raw_event.get("eventCategory", "")
    if cat:
        return cat.strip()

    # Fall back to sniffing the description / title
    desc = raw_event.get("description", "") + " " + (raw_event.get("title") or "")
    for token in ("CM", "TD Cartable Numérique", "TD", "TP"):
        if token in desc:
            # Return the short form
            return token.split()[0]
    return "OTHER"


def _build_uid(raw_event: dict) -> str:
    """Build a UID string for the ICS event."""
    eid = raw_event.get("id", "")
    if eid:
        return f"{eid}@celcat.uvsq.fr"
    # Fallback: hash of start + description
    import hashlib
    blob = (raw_event.get("start", "") + raw_event.get("description", "")).encode()
    return hashlib.md5(blob).hexdigest() + "@celcat.uvsq.fr"


# ------------------------------------------------------------------
# Main filtering function
# ------------------------------------------------------------------
def filter_events(
    raw_events: list[dict],
    modules: dict,
    colors: dict,
) -> list[CalendarEvent]:
    """
    Filter raw CELCAT events according to the student's module/group
    configuration.

    Parameters
    ----------
    raw_events : list[dict]
        Events as returned by ``CelcatClient.get_calendar_data()``.
    modules : dict
        Module configuration from ``config.MODULES``.
    colors : dict
        Colour map from ``config.COLORS``.

    Returns
    -------
    list[CalendarEvent]
        Events that belong to the student.
    """
    enrolled_codes = {code.upper() for code in modules}
    kept: list[CalendarEvent] = []
    seen_keys: set[str] = set()       # for deduplication

    for raw in raw_events:
        # --- Gather raw text for analysis --------------------------------
        desc_raw  = raw.get("description", "")
        title_raw = raw.get("title", "") or ""
        all_text  = f"{title_raw} {desc_raw}"

        # --- Extract module codes ----------------------------------------
        codes = _extract_module_codes(all_text)
        if not codes:
            continue   # event not linked to any known module

        # Check if at least one code belongs to this student
        matching_codes = [c for c in codes if c in enrolled_codes]
        if not matching_codes:
            continue

        # --- Determine category ------------------------------------------
        category = _event_category(raw)

        # --- Group filtering for TD / TP ---------------------------------
        if category.startswith("TD") or category.startswith("TP"):
            group_nums = _extract_group_numbers(all_text)
            if group_nums:
                # At least one group label is present → check match
                match = False
                for code in matching_codes:
                    expected_group = modules.get(code, {}).get("td_group")
                    if expected_group is not None and expected_group in group_nums:
                        match = True
                        break
                if not match:
                    continue   # TD/TP for another group

        # --- Build the clean CalendarEvent -------------------------------
        desc_clean = _clean_html(desc_raw)
        location_raw = raw.get("location", "") or ""
        if not location_raw:
            # Try to extract rooms from structured field
            rooms = raw.get("rooms", [])
            if isinstance(rooms, list) and rooms:
                location_raw = rooms[0] if isinstance(rooms[0], str) else ""

        location_clean = _clean_html(location_raw)

        # Summary: "CM - Simulation - MIN17212"
        primary_code = matching_codes[0]
        mod_name = modules.get(primary_code, {}).get("name", primary_code)
        summary = f"{category} - {mod_name} - {primary_code}"

        color = colors.get(category, colors.get("DEFAULT", "#9E9E9E"))
        # Use event's own colour if provided
        bg = raw.get("backgroundColor", "")
        if bg:
            color = bg

        uid = _build_uid(raw)

        # Build the multi-line ICS description (mirrors the uploaded .ics)
        desc_lines: list[str] = [category]
        if location_clean:
            desc_lines.append(location_clean)
        for code in matching_codes:
            mname = modules.get(code, {}).get("name", code)
            desc_lines.append(f"{code}-{mname} [{code}]")
        # Group line
        groups_raw = raw.get("groups", [])
        if isinstance(groups_raw, list):
            for g in groups_raw:
                if isinstance(g, str):
                    desc_lines.append(_clean_html(g))
        elif isinstance(groups_raw, str):
            desc_lines.append(_clean_html(groups_raw))
        # If no structured group field, try to extract from description
        if len(desc_lines) <= 2 + len(matching_codes):
            for line in desc_clean.split("\n"):
                if "M1 " in line and "Info" in line:
                    desc_lines.append(line.strip())
                    break

        ics_description = "\\n".join(desc_lines)

        # --- Deduplication key -------------------------------------------
        dedup = f"{raw.get('start','')}|{raw.get('end','')}|{summary}"
        if dedup in seen_keys:
            continue
        seen_keys.add(dedup)

        kept.append(CalendarEvent(
            uid=uid,
            dtstart=raw.get("start", ""),
            dtend=raw.get("end", ""),
            summary=summary,
            description=ics_description,
            location=location_clean,
            color=color,
            category=category,
            module_codes=matching_codes,
            group_labels=[_clean_html(g) for g in (groups_raw if isinstance(groups_raw, list) else [groups_raw]) if isinstance(g, str)],
        ))

    # Sort chronologically
    kept.sort(key=lambda e: e.dtstart)
    print(f"[+] {len(kept)} event(s) after filtering (from {len(raw_events)} raw)")
    return kept
