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


KONTEN_BLATT = "benutzer"
KONTEN_SPALTEN = ["name", "passwort", "blatt", "wechseln", "geaendert"]


def tabelle_oeffnen(sheet_url: str, zugangsdaten: dict):
    """Die Google-Tabelle oeffnen. Getrennt, weil zwei Blaetter sie brauchen:
    die Abrechnung und die Liste der Konten."""
    import gspread
    from google.oauth2.service_account import Credentials

    anmeldung = Credentials.from_service_account_info(zugangsdaten, scopes=BEREICHE)
    return gspread.authorize(anmeldung).open_by_url(sheet_url)


def blatt_holen(tabelle, name: str, spalten: list[str]):
    """Ein Arbeitsblatt holen und anlegen, falls es noch nicht da ist."""
    import gspread

    try:
        return tabelle.worksheet(name)
    except gspread.WorksheetNotFound:
        blatt = tabelle.add_worksheet(title=name, rows=200, cols=max(len(spalten), 3))
        blatt.append_row(spalten)
        return blatt


class TabellenSpeicher:
    """Ablage in einem Arbeitsblatt: je Zeile ein gespeicherter Stand."""

    def __init__(self, sheet_url: str, zugangsdaten: dict, blatt: str = BLATT):
        self.beschreibung = "Google-Tabelle"
        self.adresse = sheet_url
        tabelle = tabelle_oeffnen(sheet_url, zugangsdaten)
        self.blatt = blatt_holen(tabelle, blatt, SPALTEN)

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

    def loeschen(self, schluessel: str) -> None:
        nummer = self._zeilennummer(schluessel)
        if nummer:
            self.blatt.delete_rows(nummer)

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


class TabellenKonten:
    """Die Benutzerliste in einem eigenen Arbeitsblatt derselben Tabelle.

    Sie steht bewusst nicht in den Streamlit-Einstellungen: Wer sein Passwort
    selbst vergibt, darf dafuer nicht auf eine Einstellungsseite angewiesen
    sein, an die nur der Betreiber herankommt. Gespeichert wird nie das
    Passwort, sondern nur eine Pruefsumme daraus.

    Die Liste ist kurz - ein paar Zeilen. Deshalb wird sie beim Schreiben
    komplett neu gesetzt; das ist einfacher und kann nicht halb misslingen.
    """

    beschreibung = "Google-Tabelle"

    def __init__(self, sheet_url: str, zugangsdaten: dict):
        self.adresse = sheet_url
        tabelle = tabelle_oeffnen(sheet_url, zugangsdaten)
        self.blatt = blatt_holen(tabelle, KONTEN_BLATT, KONTEN_SPALTEN)

    def lesen(self) -> list[dict]:
        zeilen = self.blatt.get_all_values()
        gefunden = []
        for zeile in zeilen[1:]:
            if not zeile or not zeile[0].strip():
                continue
            eintrag = dict(zip(KONTEN_SPALTEN, list(zeile) + [""] * len(KONTEN_SPALTEN)))
            gefunden.append(eintrag)
        return gefunden

    def schreiben(self, konten: list[dict]) -> None:
        werte = [KONTEN_SPALTEN]
        werte += [[str(k.get(spalte, "")) for spalte in KONTEN_SPALTEN] for k in konten]
        self.blatt.clear()
        self.blatt.update("A1", werte)
