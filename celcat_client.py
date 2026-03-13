"""
CELCAT UVSQ API Client
======================
Handles HTTP session management, CSRF token extraction, resource discovery,
and calendar data fetching from the CELCAT system at UVSQ.
"""

import re
import time
import requests
from bs4 import BeautifulSoup


class CelcatClient:
    """HTTP client for the CELCAT calendar system at UVSQ."""

    # CELCAT resource types
    RES_TYPE_ROOMS   = 100
    RES_TYPE_STAFF   = 101
    RES_TYPE_STUDENT = 102
    RES_TYPE_GROUPS  = 103
    RES_TYPE_MODULES = 104

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        self._token: str | None = None

    # ------------------------------------------------------------------
    # Session initialisation
    # ------------------------------------------------------------------
    def initialize(self) -> bool:
        """
        Fetch the CELCAT main page to obtain session cookies and the
        anti-forgery token required by subsequent POST requests.
        Returns True on success.
        """
        print("[*] Connecting to CELCAT …")
        resp = self.session.get(
            self.base_url,
            headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
            timeout=30,
        )
        resp.raise_for_status()

        # Extract __RequestVerificationToken from a hidden <input>
        soup = BeautifulSoup(resp.text, "html.parser")
        token_input = soup.find("input", {"name": "__RequestVerificationToken"})
        if token_input:
            self._token = token_input.get("value", "")
            print(f"[+] Session initialised  (token: {self._token[:12]}…)")
        else:
            # Some CELCAT deployments put it in a <meta> tag instead
            meta = soup.find("meta", {"name": "csrf-token"})
            if meta:
                self._token = meta.get("content", "")
                print(f"[+] Session initialised  (meta-token: {self._token[:12]}…)")
            else:
                print("[!] Warning: no anti-forgery token found – requests may fail")

        return True

    # ------------------------------------------------------------------
    # Resource search  (groups, modules, rooms …)
    # ------------------------------------------------------------------
    def search_resources(
        self,
        search_term: str,
        res_type: int = RES_TYPE_GROUPS,
        page_size: int = 50,
    ) -> list[dict]:
        """
        Search CELCAT resources by name.

        Returns a list of dicts: [{"id": "<federation_id>", "text": "<label>"}, …]
        """
        url = f"{self.base_url}/Home/ReadResourceListItems"
        data = {
            "myResources": "false",
            "searchTerm": search_term,
            "pageSize": str(page_size),
            "pageNumber": "1",
            "resType": str(res_type),
        }
        if self._token:
            data["__RequestVerificationToken"] = self._token

        resp = self.session.post(
            url,
            data=data,
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=30,
        )
        resp.raise_for_status()

        payload = resp.json()
        results = payload.get("results", [])
        print(f"[+] Search '{search_term}' → {len(results)} result(s)")
        return results

    # ------------------------------------------------------------------
    # Calendar data
    # ------------------------------------------------------------------
    def get_calendar_data(
        self,
        federation_ids: list[str],
        start_date: str,
        end_date: str,
        res_type: int = RES_TYPE_GROUPS,
    ) -> list[dict]:
        """
        Fetch calendar events for a list of federation IDs.

        Parameters
        ----------
        federation_ids : list[str]
            One or more CELCAT federation IDs (UUIDs or opaque strings).
        start_date, end_date : str
            ISO dates  "YYYY-MM-DD".
        res_type : int
            Resource type used for the query.

        Returns
        -------
        list[dict]  – raw event objects as returned by CELCAT.
        """
        url = f"{self.base_url}/Home/GetCalendarData"

        # Build form data as a list of tuples so that duplicate keys
        # (federationIds[]) are sent correctly.
        form: list[tuple[str, str]] = [
            ("start", start_date),
            ("end", end_date),
            ("resType", str(res_type)),
            ("calView", "agendaWeek"),
            ("colourScheme", "3"),
        ]
        if self._token:
            form.append(("__RequestVerificationToken", self._token))
        for fid in federation_ids:
            form.append(("federationIds[]", fid))

        print(f"[*] Fetching events  {start_date} → {end_date}  ({len(federation_ids)} group(s)) …")

        resp = self.session.post(
            url,
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
        print(f"[+] Received {len(events)} raw event(s)")
        return events

    # ------------------------------------------------------------------
    # Convenience: discover groups for a programme
    # ------------------------------------------------------------------
    def discover_groups(self, search_term: str) -> list[dict]:
        """
        Search for groups matching *search_term* and pretty-print them
        so the user can identify the correct federation IDs.
        """
        results = self.search_resources(search_term, res_type=self.RES_TYPE_GROUPS, page_size=100)
        if not results:
            print(f"[!] No groups found for '{search_term}'")
        else:
            print(f"\n{'#':<4} {'Federation ID':<40} {'Label'}")
            print("-" * 100)
            for i, r in enumerate(results, 1):
                print(f"{i:<4} {r['id']:<40} {r['text']}")
            print()
        return results
