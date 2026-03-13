# =============================================================================
# CELCAT UVSQ Calendar Fetcher - Configuration
# =============================================================================
# Edit this file to match YOUR specific enrollment (modules + TD groups).
# All information comes from your "Contrat d'études" on the university portal.
# =============================================================================

# ---------------------------------------------------------------------------
# CELCAT base URL
# ---------------------------------------------------------------------------
CELCAT_BASE_URL = "https://edt.uvsq.fr"

# ---------------------------------------------------------------------------
# Programme / promotion search term used to discover federation IDs
# This should match the name shown in CELCAT for your master programme.
# ---------------------------------------------------------------------------
PROGRAMME_SEARCH_TERM = "M1 AMIS"

# ---------------------------------------------------------------------------
# Date range to fetch (ISO format YYYY-MM-DD)
# Adjust to cover your current semester.
# ---------------------------------------------------------------------------
FETCH_START_DATE = "2026-01-19"
FETCH_END_DATE   = "2026-07-01"

# ---------------------------------------------------------------------------
# YOUR enrolled modules with the TD group number for each one.
#
#   "module_code": {
#       "name":           human-readable name,
#       "td_group":       your TD group number (int),
#       "td_group_label": label that appears in CELCAT descriptions,
#   }
#
# CM (lectures) are common to ALL groups so no CM-specific group is needed.
# TD / TP events will be filtered so that ONLY your group is kept.
# ---------------------------------------------------------------------------
MODULES = {
    "MIN15221": {
        "name": "TER",
        "td_group": 1,
        "td_group_label": "M1 Info gr. 1",
    },
    "MIN17201": {
        "name": "Programmation, GL et Preuve",
        "td_group": 3,
        "td_group_label": "M1 Info gr. 3",
    },
    "MSANGS2I": {
        "name": "Anglais",
        "td_group": 4,
        "td_group_label": "M1 Info gr. 4",
    },
    "MIN17211": {
        "name": "Méthodes de Ranking",
        "td_group": 1,
        "td_group_label": "M1 Info gr. 1",
    },
    "MIN17212": {
        "name": "Simulation",
        "td_group": 1,
        "td_group_label": "M1 Info gr. 1",
    },
    "MIN17214": {
        "name": "Conception de BD",
        "td_group": 2,
        "td_group_label": "M1 Info gr. 2",
    },
    "MIN17216": {
        "name": "Réseaux étendus",
        "td_group": 1,
        "td_group_label": "M1 Info gr. 1",
    },
}

# ---------------------------------------------------------------------------
# Color scheme  (matches the CELCAT colour scheme)
# ---------------------------------------------------------------------------
COLORS = {
    "CM":      "#27AE60",   # green  – lectures
    "TD":      "#E91E63",   # pink   – tutorials
    "TP":      "#2196F3",   # blue   – practicals
    "DEFAULT": "#9E9E9E",   # grey   – fallback
}

# ---------------------------------------------------------------------------
# Output ICS settings
# ---------------------------------------------------------------------------
OUTPUT_ICS_FILE   = "my_calendar.ics"
CALENDAR_NAME     = "CELCAT - UVSQ Calendar"
CALENDAR_TIMEZONE = "Europe/Paris"
CALENDAR_PRODID   = "-//CELCAT to ICS//UVSQ Calendar//EN"
