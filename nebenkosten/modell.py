"""Datenmodell der Nebenkostenabrechnung.

Alle Beträge in EUR, alle Datumsangaben als ISO-String (YYYY-MM-DD),
damit sich der komplette Zustand verlustfrei als JSON speichern lässt.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import date

# Verteilerschlüssel (§ 556a BGB). Ohne abweichende Vereinbarung im
# Mietvertrag gilt die Wohnfläche als gesetzlicher Standardschlüssel.
SCHLUESSEL = {
    "flaeche": "nach Wohnfläche",
    "personen": "nach Personenzahl",
    "einheiten": "je Wohnung",
    "verbrauch": "nach Zählerstand",
    "direkt": "nur der Mieter",
    "direkt_vermieter": "nur ich selbst",
}

ABRECHNUNGSARTEN = {
    "jahr": "Jahresabrechnung",
    "mietende": "Abrechnung zum Mietende (Auszug)",
    "zwischen": "Zwischenabrechnung (nur zur Information)",
}

# Häufige Gründe für eine Zwischenabrechnung – nur Vorschläge für das Feld.
ZWISCHEN_ANLAESSE = [
    "Wechsel des Gasanbieters",
    "Wechsel des Strom- oder Wasserversorgers",
    "auf Wunsch des Mieters",
    "Zwischenstand zur Prüfung der Vorauszahlungen",
]

# Wie die Differenz zwischen Hauptzähler und Wohnungszählern verteilt wird.
# Ohne andere Vereinbarung im Mietvertrag ist die Wohnfläche der gesetzliche
# Maßstab (§ 556a Abs. 1 S. 1 BGB).
DIFFERENZ_VERTEILUNG = {
    "verbrauch": "nach gemessenem Verbrauch",
    "flaeche": "nach Wohnfläche",
}

# Positionen, die nach herrschender Rechtsprechung nicht auf den Mieter
# umgelegt werden dürfen. Wird nur für Warnhinweise in der App benutzt.
NICHT_UMLAGEFAEHIG_STICHWORTE = [
    "reparatur", "instandhaltung", "instandsetzung", "wartungsreparatur",
    "verwaltung", "verwalter", "kontoführung", "kontofuehrung", "porto",
    "rücklage", "ruecklage", "anwalt", "rechtsschutz", "mietausfall",
    "modernisierung", "sanierung", "neuanschaffung", "bankgebühr",
]


SICHTEN = {
    "mieter": "Abrechnung für den Mieter",
    "vermieter": "Abrechnung für die eigene Wohnung",
}

PARTEIEN = {
    "haus": "Hauptzähler (ganzes Haus)",
    "mieter": "Wohnung des Mieters",
    "vermieter": "Deine Wohnung",
}

# Woraus sich der Anteil des Mieters ergibt
ZAEHLER_GRUNDLAGE = {
    "hauptzaehler": "Anteil am Hauptzähler (Differenz wird verteilt)",
    "unterzaehler": "nur die Unterzähler im Verhältnis",
}


@dataclass
class Zaehlerstand:
    """Ein einzelner Zähler mit Stand am Anfang und am Ende des Zeitraums."""

    name: str = ""
    partei: str = "mieter"      # haus, mieter oder vermieter
    alt: float = 0.0
    neu: float = 0.0

    @property
    def verbrauch(self) -> float:
        return max(0.0, float(self.neu) - float(self.alt))


@dataclass
class Position:
    """Eine Kostenart der Abrechnung (i. d. R. eine Position nach § 2 BetrKV)."""

    bezeichnung: str
    betrag: float = 0.0            # Gesamtkosten des Hauses im Abrechnungszeitraum
    schluessel: str = "flaeche"
    einheit: str = ""              # z. B. m³ oder kWh
    zaehler: list[Zaehlerstand] = field(default_factory=list)
    zaehler_grundlage: str = "hauptzaehler"
    zaehler_von: str = ""          # Zähler einer anderen Position mitbenutzen
    # Ersatz, wenn es gar keine Zähler gibt: Mengen direkt eintragen
    verbrauch_gesamt: float = 0.0
    verbrauch_mieter: float = 0.0
    verbrauch_eigen_direkt: float = 0.0
    # Bei Heiz- und Warmwasserkosten üblich: ein Teil wird nach Wohnfläche
    # verteilt (Grundkosten), der Rest nach Verbrauch. 0 = alles nach Verbrauch.
    grundkosten_anteil: float = 0.0   # Prozent, 0 bis 50
    arbeitskosten: float = 0.0     # im Betrag enthaltene Lohnkosten (§ 35a EStG)
    zeitanteilig: bool = True      # bei unterjähriger Nutzung anteilig kürzen
    aktiv: bool = True
    hinweis: str = ""

    def _summe(self, partei: str) -> float:
        return sum(z.verbrauch for z in self.zaehler if z.partei == partei)

    @property
    def verbrauch_haus(self) -> float:
        """Verbrauch laut Hauptzähler; ohne Hauptzähler die direkte Eingabe."""
        return self._summe("haus") or float(self.verbrauch_gesamt)

    @property
    def verbrauch_wohnung(self) -> float:
        return self._summe("mieter") or float(self.verbrauch_mieter)

    @property
    def verbrauch_eigen(self) -> float:
        return self._summe("vermieter") or float(self.verbrauch_eigen_direkt)

    @property
    def hat_zaehlerstaende(self) -> bool:
        return any(z.alt or z.neu for z in self.zaehler)


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

    # Art der Abrechnung
    abrechnungsart: str = "jahr"   # "jahr", "mietende" oder "zwischen"
    auszug_am: str = ""            # nur bei abrechnungsart == "mietende"
    anlass: str = ""               # nur bei abrechnungsart == "zwischen"

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
    grundstuecksflaeche: float = 0.0   # nur zur Information im Abrechnungskopf

    # Verteilung der Differenz zwischen Hauptzähler und Wohnungszählern
    zaehlerdifferenz: str = "verbrauch"  # "verbrauch" oder "flaeche"

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
    eigene_abrechnung: bool = False

    @property
    def ist_endabrechnung(self) -> bool:
        return self.abrechnungsart == "mietende"

    @property
    def ist_zwischenabrechnung(self) -> bool:
        return self.abrechnungsart == "zwischen"

    @property
    def ist_verbindlich(self) -> bool:
        """Eine Zwischenabrechnung begründet noch keine Forderung."""
        return not self.ist_zwischenabrechnung

    @property
    def bezeichnung_abrechnung(self) -> str:
        return {"mietende": "Abrechnung zum Mietende",
                "zwischen": "Zwischenabrechnung"}.get(self.abrechnungsart, "Jahresabrechnung")

    @property
    def vorauszahlung_gesamt(self) -> float:
        if self.vorauszahlung_manuell is not None:
            return float(self.vorauszahlung_manuell)
        return float(self.vorauszahlung_monatlich) * int(self.vorauszahlung_monate)


def standard_positionen() -> list[Position]:
    """Die Kostenarten, die auf einen Mieter umgelegt werden dürfen (§ 2 BetrKV).

    Der Hinweis sagt, welcher Beleg zu der Zeile gehört. Die Zähler sind für ein
    Zweifamilienhaus vorbereitet und lassen sich in der App ändern, löschen und
    ergänzen.
    """
    wasserzaehler = [
        Zaehlerstand("Hauptzähler Wasser", "haus"),
        Zaehlerstand("Kaltwasser Mieter", "mieter"),
        Zaehlerstand("Warmwasser Mieter", "mieter"),
        Zaehlerstand("Kaltwasser eigene Wohnung", "vermieter"),
        Zaehlerstand("Warmwasser eigene Wohnung", "vermieter"),
    ]
    return [
        Position("Grundsteuer", schluessel="flaeche",
                 hinweis="Grundsteuerbescheid der Gemeinde"),
        Position("Wasser", schluessel="verbrauch", einheit="m³",
                 zaehler=wasserzaehler,
                 hinweis="Jahresrechnung des Wasserversorgers"),
        Position("Abwasser", schluessel="verbrauch", einheit="m³",
                 zaehler_von="Wasser",
                 hinweis="Gebührenbescheid der Gemeinde; meist auf die Frischwassermenge"),
        Position("Heizung (Gas)", schluessel="verbrauch", einheit="kWh",
                 zaehler_grundlage="unterzaehler", grundkosten_anteil=30.0,
                 zaehler=[
                     Zaehlerstand("Gaszähler Haus (nur zur Information)", "haus"),
                     Zaehlerstand("Wärmemenge Fußbodenheizung Mieter", "mieter"),
                     Zaehlerstand("Wärmemenge Fußbodenheizung eigene Wohnung", "vermieter"),
                     Zaehlerstand("Wärmemenge Heizkörper eigene Wohnung", "vermieter"),
                 ],
                 hinweis="Gasrechnung, Wartung, Betriebsstrom – verteilt nach den "
                         "Wärmemengenzählern"),
        Position("Warmwasser (Gas)", schluessel="verbrauch", einheit="m³",
                 zaehler_grundlage="unterzaehler", grundkosten_anteil=30.0,
                 zaehler=[
                     Zaehlerstand("Warmwasser Mieter", "mieter"),
                     Zaehlerstand("Warmwasser eigene Wohnung", "vermieter"),
                 ],
                 hinweis="Anteil der Gaskosten für die Warmwasserbereitung – "
                         "verteilt nach den Warmwasserzählern"),
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


def sicht_vermieter(s: Stammdaten) -> Stammdaten:
    """Dieselben Daten aus Sicht der eigenen Wohnung.

    Für die eigene Aufstellung (Steuer, Unterlagen) wird alles gespiegelt:
    die eigene Wohnfläche, die eigenen Personen, das ganze Jahr als
    Nutzungszeitraum und keine Vorauszahlungen.
    """
    return replace(
        s,
        mieter_name=s.vermieter_name,
        mieter_wohnung="eigene Wohnung",
        anrede="",
        flaeche_mieter=max(0.0, s.flaeche_gesamt - s.flaeche_mieter),
        personen_mieter=max(0.0, s.personen_gesamt - s.personen_mieter),
        einheiten_mieter=max(0.0, s.einheiten_gesamt - s.einheiten_mieter),
        nutzung_von=s.zeitraum_von,
        nutzung_bis=s.zeitraum_bis,
        vorauszahlung_monatlich=0.0,
        vorauszahlung_manuell=None,
        co2_abzug=0.0,
        anpassung_vorschlagen=False,
    )


def as_dict(stammdaten: Stammdaten, positionen: list[Position]) -> dict:
    return {
        "version": 2,
        "stammdaten": asdict(stammdaten),
        "positionen": [asdict(p) for p in positionen],
    }


def _zaehler_aus_dict(daten: dict) -> list[Zaehlerstand]:
    """Zähler einlesen – auch aus dem alten Format mit drei festen Zählern."""
    if daten.get("zaehler"):
        felder = set(Zaehlerstand.__dataclass_fields__)
        return [Zaehlerstand(**{k: v for k, v in z.items() if k in felder})
                for z in daten["zaehler"] if isinstance(z, dict)]

    alt = [
        ("Hauptzähler", "haus", "zaehler_haus_alt", "zaehler_haus_neu"),
        ("Zähler Mieterwohnung", "mieter", "zaehler_mieter_alt", "zaehler_mieter_neu"),
        ("Zähler eigene Wohnung", "vermieter", "zaehler_eigen_alt", "zaehler_eigen_neu"),
    ]
    uebernommen = [Zaehlerstand(name, partei, float(daten.get(a) or 0), float(daten.get(n) or 0))
                   for name, partei, a, n in alt
                   if daten.get(a) or daten.get(n)]
    return uebernommen


def from_dict(daten: dict) -> tuple[Stammdaten, list[Position]]:
    stamm_felder = set(Stammdaten.__dataclass_fields__)
    pos_felder = set(Position.__dataclass_fields__) - {"zaehler"}
    stamm = Stammdaten(**{k: v for k, v in daten.get("stammdaten", {}).items()
                          if k in stamm_felder})
    positionen = []
    for p in daten.get("positionen", []):
        werte = {k: v for k, v in p.items() if k in pos_felder}
        positionen.append(Position(zaehler=_zaehler_aus_dict(p), **werte))
    return stamm, positionen or standard_positionen()
