"""
CELCAT UVSQ API Client  (web edition – self-contained)
======================================================
"""

import requests
from bs4 import BeautifulSoup


class CelcatClient:
    RES_TYPE_GROUPS  = 103

    def __init__(self, base_url: str = "https://edt.uvsq.fr"):
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

    # ---- session --------------------------------------------------------
    def initialize(self) -> bool:
        resp = self.session.get(
            self.base_url,
            headers={"Accept": "text/html,application/xhtml+xml"},
            timeout=30,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        inp = soup.find("input", {"name": "__RequestVerificationToken"})
        if inp:
            self._token = inp.get("value", "")
        else:
            meta = soup.find("meta", {"name": "csrf-token"})
            if meta:
                self._token = meta.get("content", "")
        return True

    # ---- search ---------------------------------------------------------
    def search_groups(self, search_term: str, page_size: int = 100) -> list[dict]:
        url = f"{self.base_url}/Home/ReadResourceListItems"
        data = {
            "myResources": "false",
            "searchTerm": search_term,
            "pageSize": str(page_size),
            "pageNumber": "1",
            "resType": str(self.RES_TYPE_GROUPS),
        }
        if self._token:
            data["__RequestVerificationToken"] = self._token
        resp = self.session.post(
            url, data=data,
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])

    # ---- calendar data --------------------------------------------------
    def get_calendar_data(
        self,
        federation_ids: list[str],
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        url = f"{self.base_url}/Home/GetCalendarData"
        form: list[tuple[str, str]] = [
            ("start", start_date),
            ("end", end_date),
            ("resType", str(self.RES_TYPE_GROUPS)),
            ("calView", "agendaWeek"),
            ("colourScheme", "3"),
        ]
        if self._token:
            form.append(("__RequestVerificationToken", self._token))
        for fid in federation_ids:
            form.append(("federationIds[]", fid))
        resp = self.session.post(
            url, data=form,
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()
