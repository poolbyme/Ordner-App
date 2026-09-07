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
    "flaeche": "nach Wohnfläche",
    "personen": "nach Personenzahl",
    "einheiten": "je Wohnung",
    "verbrauch": "nach Zählerstand",
    "direkt": "nur der Mieter",
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
    # Zählerstände; sind sie gefüllt, ergibt die Differenz den Verbrauch
    zaehler_haus_alt: float = 0.0
    zaehler_haus_neu: float = 0.0
    zaehler_mieter_alt: float = 0.0
    zaehler_mieter_neu: float = 0.0
    einheit: str = ""              # z. B. m³, kWh
    arbeitskosten: float = 0.0     # im Betrag enthaltene Lohnkosten (§ 35a EStG)
    zeitanteilig: bool = True      # bei unterjähriger Nutzung anteilig kürzen
    aktiv: bool = True
    hinweis: str = ""

    @property
    def verbrauch_haus(self) -> float:
        """Verbrauch des Hauses: aus den Zählerständen, sonst direkt eingetragen."""
        differenz = self.zaehler_haus_neu - self.zaehler_haus_alt
        return differenz if differenz > 0 else float(self.verbrauch_gesamt)

    @property
    def verbrauch_wohnung(self) -> float:
        """Verbrauch der Mietwohnung: aus den Zählerständen, sonst direkt eingetragen."""
        differenz = self.zaehler_mieter_neu - self.zaehler_mieter_alt
        return differenz if differenz > 0 else float(self.verbrauch_mieter)

    @property
    def hat_zaehlerstaende(self) -> bool:
        return any([self.zaehler_haus_alt, self.zaehler_haus_neu,
                    self.zaehler_mieter_alt, self.zaehler_mieter_neu])


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
    """Die Kostenarten, die auf einen Mieter umgelegt werden dürfen (§ 2 BetrKV).

    Der Hinweis sagt, welcher Beleg zu der Zeile gehört. Voreingestellt ist,
    was in einem Zweifamilienhaus üblicherweise anfällt; der Rest ist
    vorhanden, aber abgewählt.
    """
    return [
        Position("Grundsteuer", schluessel="flaeche",
                 hinweis="Grundsteuerbescheid der Gemeinde"),
        Position("Wasser", schluessel="verbrauch", einheit="m³",
                 hinweis="Jahresrechnung des Wasserversorgers"),
        Position("Abwasser", schluessel="verbrauch", einheit="m³",
                 hinweis="Gebührenbescheid der Gemeinde oder Stadtwerke"),
        Position("Heizung", schluessel="flaeche",
                 hinweis="Rechnungen für Gas, Öl oder Pellets, Wartung, Betriebsstrom"),
        Position("Warmwasser", schluessel="flaeche", aktiv=False,
                 hinweis="nur nötig, wenn getrennt von der Heizung abgerechnet wird"),
        Position("Aufzug", schluessel="flaeche", aktiv=False,
                 hinweis="Wartungsvertrag, Notruf, Strom"),
        Position("Straßenreinigung und Winterdienst", schluessel="flaeche",
                 hinweis="Gebührenbescheid oder Rechnung des Dienstleisters"),
        Position("Müllabfuhr", schluessel="personen",
                 hinweis="Gebührenbescheid der Gemeinde"),
        Position("Gebäudereinigung", schluessel="flaeche", aktiv=False,
                 hinweis="Rechnung der Reinigungsfirma, Treppenhausreinigung"),
        Position("Ungezieferbekämpfung", schluessel="flaeche", aktiv=False,
                 hinweis="nur laufende Bekämpfung, keine einmalige Beseitigung"),
        Position("Gartenpflege", schluessel="flaeche",
                 hinweis="Rechnungen der Gärtnerei; eigene Arbeit darf zum "
                         "üblichen Preis ohne Mehrwertsteuer angesetzt werden"),
        Position("Allgemeinstrom", schluessel="flaeche",
                 hinweis="Stromrechnung für Flur, Keller, Außenbeleuchtung"),
        Position("Schornsteinfeger", schluessel="flaeche",
                 hinweis="Rechnung des Schornsteinfegers, wenn nicht schon in der Heizung enthalten"),
        Position("Versicherungen", schluessel="flaeche",
                 hinweis="Gebäude-, Haftpflicht- und Elementarversicherung; "
                         "keine Rechtsschutz- oder Reparaturversicherung"),
        Position("Hausmeister", schluessel="flaeche", aktiv=False,
                 hinweis="Lohn ohne Reparatur- und Verwaltungsanteil"),
        Position("Kabelanschluss", schluessel="einheiten", aktiv=False,
                 hinweis="seit 01.07.2024 nicht mehr über die Nebenkosten umlegbar"),
        Position("Gemeinsame Waschmaschine", schluessel="einheiten", aktiv=False,
                 hinweis="Strom und Wartung gemeinsam genutzter Geräte"),
        Position("Sonstiges", schluessel="flaeche", aktiv=False,
                 hinweis="nur wenn diese Kosten im Mietvertrag ausdrücklich genannt sind"),
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
