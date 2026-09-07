"""Datenmodell der Nebenkostenabrechnung.

Alle Beträge in EUR, alle Datumsangaben als ISO-String (YYYY-MM-DD),
damit sich der komplette Zustand verlustfrei als JSON speichern lässt.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date

# Verteilerschlüssel (§ 556a BGB). Ohne abweichende Vereinbarung im
# Mietvertrag gilt die Wohnfläche als gesetzlicher Standardschlüssel.
SCHLUESSEL = {
    "flaeche": "Wohnfläche",
    "personen": "Personenzahl",
    "einheiten": "Wohneinheiten",
    "verbrauch": "Verbrauch (Zähler)",
    "direkt": "direkt zugeordnet",
}

# Positionen, die nach herrschender Rechtsprechung nicht auf den Mieter
# umgelegt werden dürfen. Wird nur für Warnhinweise in der App benutzt.
NICHT_UMLAGEFAEHIG_STICHWORTE = [
    "reparatur", "instandhaltung", "instandsetzung", "wartungsreparatur",
    "verwaltung", "verwalter", "kontoführung", "kontofuehrung", "porto",
    "rücklage", "ruecklage", "anwalt", "rechtsschutz", "mietausfall",
    "modernisierung", "sanierung", "neuanschaffung", "bankgebühr",
]


@dataclass
class Position:
    """Eine Kostenart der Abrechnung (i. d. R. eine Position nach § 2 BetrKV)."""

    bezeichnung: str
    betrag: float = 0.0            # Gesamtkosten des Hauses im Abrechnungszeitraum
    schluessel: str = "flaeche"
    verbrauch_gesamt: float = 0.0  # nur bei schluessel == "verbrauch"
    verbrauch_mieter: float = 0.0
    einheit: str = ""              # z. B. m³, kWh
    arbeitskosten: float = 0.0     # im Betrag enthaltene Lohnkosten (§ 35a EStG)
    zeitanteilig: bool = True      # bei unterjähriger Nutzung anteilig kürzen
    aktiv: bool = True
    hinweis: str = ""


@dataclass
class Stammdaten:
    # Vermieter
    vermieter_name: str = ""
    vermieter_strasse: str = ""
    vermieter_plz_ort: str = ""
    vermieter_iban: str = ""
    vermieter_bank: str = ""

    # Mieter / Wohnung
    mieter_name: str = ""
    anrede: str = "Sehr geehrte Damen und Herren,"
    mieter_wohnung: str = "Wohnung Obergeschoss"
    objekt_strasse: str = ""
    objekt_plz_ort: str = ""

    # Zeiträume
    zeitraum_von: str = ""
    zeitraum_bis: str = ""
    nutzung_von: str = ""   # Mietzeit innerhalb des Abrechnungszeitraums
    nutzung_bis: str = ""

    # Umlagegrundlagen
    flaeche_gesamt: float = 0.0
    flaeche_mieter: float = 0.0
    personen_gesamt: float = 0.0
    personen_mieter: float = 0.0
    einheiten_gesamt: float = 2.0
    einheiten_mieter: float = 1.0

    # Vorauszahlungen
    vorauszahlung_monatlich: float = 0.0
    vorauszahlung_monate: int = 12
    vorauszahlung_manuell: float | None = None  # überschreibt monatlich × Monate

    # Sonstiges
    co2_abzug: float = 0.0        # Vermieteranteil an den CO2-Kosten (CO2KostAufG)
    zahlungsfrist_tage: int = 30
    ort: str = ""
    datum: str = field(default_factory=lambda: date.today().isoformat())
    anpassung_vorschlagen: bool = True

    @property
    def vorauszahlung_gesamt(self) -> float:
        if self.vorauszahlung_manuell is not None:
            return float(self.vorauszahlung_manuell)
        return float(self.vorauszahlung_monatlich) * int(self.vorauszahlung_monate)


def standard_positionen() -> list[Position]:
    """Katalog der umlagefähigen Betriebskosten nach § 2 BetrKV.

    Voreingestellt ist, was in einem Zweifamilienhaus typischerweise anfällt;
    alles Weitere ist enthalten, aber deaktiviert.
    """
    return [
        Position("Grundsteuer", schluessel="flaeche",
                 hinweis="§ 2 Nr. 1 BetrKV"),
        Position("Wasserversorgung (Frischwasser)", schluessel="verbrauch", einheit="m³",
                 hinweis="§ 2 Nr. 2 BetrKV – nach Zählerstand, sonst Wohnfläche"),
        Position("Entwässerung / Abwasser", schluessel="verbrauch", einheit="m³",
                 hinweis="§ 2 Nr. 3 BetrKV"),
        Position("Heizung (Brennstoff, Betriebsstrom, Wartung)", schluessel="flaeche",
                 hinweis="§ 2 Nr. 4 BetrKV – HeizkostenV beachten"),
        Position("Warmwasser", schluessel="flaeche",
                 hinweis="§ 2 Nr. 5 BetrKV"),
        Position("Aufzug", schluessel="flaeche", aktiv=False,
                 hinweis="§ 2 Nr. 7 BetrKV"),
        Position("Straßenreinigung / Winterdienst", schluessel="flaeche",
                 hinweis="§ 2 Nr. 8 BetrKV"),
        Position("Müllbeseitigung", schluessel="personen",
                 hinweis="§ 2 Nr. 8 BetrKV"),
        Position("Gebäudereinigung", schluessel="flaeche", aktiv=False,
                 hinweis="§ 2 Nr. 9 BetrKV"),
        Position("Ungezieferbekämpfung", schluessel="flaeche", aktiv=False,
                 hinweis="§ 2 Nr. 9 BetrKV"),
        Position("Gartenpflege", schluessel="flaeche",
                 hinweis="§ 2 Nr. 10 BetrKV"),
        Position("Allgemeinstrom / Beleuchtung", schluessel="flaeche",
                 hinweis="§ 2 Nr. 11 BetrKV"),
        Position("Schornsteinfeger", schluessel="flaeche",
                 hinweis="§ 2 Nr. 12 BetrKV – soweit nicht in der Heizung enthalten"),
        Position("Sach- und Haftpflichtversicherung", schluessel="flaeche",
                 hinweis="§ 2 Nr. 13 BetrKV – Gebäude-, Haftpflicht-, Elementarversicherung"),
        Position("Hauswart / Hausmeister", schluessel="flaeche", aktiv=False,
                 hinweis="§ 2 Nr. 14 BetrKV – ohne Instandhaltungs- und Verwaltungsanteil"),
        Position("Gemeinschaftsantenne / Kabelanschluss", schluessel="einheiten", aktiv=False,
                 hinweis="§ 2 Nr. 15 BetrKV – seit 01.07.2024 nicht mehr über die Nebenkosten umlegbar"),
        Position("Wascheinrichtungen", schluessel="einheiten", aktiv=False,
                 hinweis="§ 2 Nr. 16 BetrKV"),
        Position("Sonstige Betriebskosten", schluessel="flaeche", aktiv=False,
                 hinweis="§ 2 Nr. 17 BetrKV – nur wenn im Mietvertrag konkret benannt"),
    ]


def as_dict(stammdaten: Stammdaten, positionen: list[Position]) -> dict:
    return {
        "version": 1,
        "stammdaten": asdict(stammdaten),
        "positionen": [asdict(p) for p in positionen],
    }


def from_dict(daten: dict) -> tuple[Stammdaten, list[Position]]:
    stamm_felder = {f for f in Stammdaten.__dataclass_fields__}
    pos_felder = {f for f in Position.__dataclass_fields__}
    stamm = Stammdaten(**{k: v for k, v in daten.get("stammdaten", {}).items() if k in stamm_felder})
    positionen = [
        Position(**{k: v for k, v in p.items() if k in pos_felder})
        for p in daten.get("positionen", [])
    ]
    return stamm, positionen or standard_positionen()
