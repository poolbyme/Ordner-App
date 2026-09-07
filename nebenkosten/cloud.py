"""Speichern in einer Google-Tabelle statt in einer Datei.

Wird gebraucht, wenn die App in der Streamlit Cloud läuft: dort ist der
Dateispeicher nach einem Neustart leer. Die komplette Abrechnung wird als
JSON-Text in einer Zeile der Tabelle abgelegt.

Einrichtung: in den Streamlit-Secrets `gcp_json` (Zugangsdaten des
Google-Dienstkontos) und `nebenkosten_sheet_url` (Adresse der Tabelle)
hinterlegen und die Tabelle für die E-Mail-Adresse des Dienstkontos freigeben.
"""

from __future__ import annotations

import json
from datetime import datetime

BLATT = "nebenkosten"
SPALTEN = ["schluessel", "gespeichert_am", "daten"]
BEREICHE = ["https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"]


class TabellenSpeicher:
    """Ablage in einem Arbeitsblatt: je Zeile ein gespeicherter Stand."""

    def __init__(self, sheet_url: str, zugangsdaten: dict, blatt: str = BLATT):
        import gspread
        from google.oauth2.service_account import Credentials

        self.beschreibung = "Google-Tabelle"
        self.adresse = sheet_url
        anmeldung = Credentials.from_service_account_info(zugangsdaten, scopes=BEREICHE)
        tabelle = gspread.authorize(anmeldung).open_by_url(sheet_url)
        try:
            self.blatt = tabelle.worksheet(blatt)
        except gspread.WorksheetNotFound:
            self.blatt = tabelle.add_worksheet(title=blatt, rows=200, cols=len(SPALTEN))
            self.blatt.append_row(SPALTEN)

    # --- intern ----------------------------------------------------------
    def _zeilen(self) -> list[list[str]]:
        return self.blatt.get_all_values()

    def _zeilennummer(self, schluessel: str) -> int | None:
        for nummer, zeile in enumerate(self._zeilen(), start=1):
            if zeile and zeile[0] == schluessel:
                return nummer
        return None

    # --- Schnittstelle ---------------------------------------------------
    def lesen(self, schluessel: str) -> dict | None:
        for zeile in self._zeilen():
            if zeile and zeile[0] == schluessel and len(zeile) > 2 and zeile[2]:
                try:
                    return json.loads(zeile[2])
                except json.JSONDecodeError:
                    return None
        return None

    def schreiben(self, schluessel: str, daten: dict) -> None:
        text = json.dumps(daten, ensure_ascii=False)
        jetzt = datetime.now().isoformat(timespec="seconds")
        nummer = self._zeilennummer(schluessel)
        if nummer:
            self.blatt.update(f"A{nummer}:C{nummer}", [[schluessel, jetzt, text]])
        else:
            if not self._zeilen():
                self.blatt.append_row(SPALTEN)
            self.blatt.append_row([schluessel, jetzt, text])

    def zeitpunkt(self, schluessel: str) -> datetime | None:
        for zeile in self._zeilen():
            if zeile and zeile[0] == schluessel and len(zeile) > 1:
                try:
                    return datetime.fromisoformat(zeile[1])
                except ValueError:
                    return None
        return None

    def schluessel(self) -> list[str]:
        return [z[0] for z in self._zeilen()[1:] if z and z[0] and z[0] != "aktuell"]
