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
    "renovierung", "renovieren", "schönheitsrepar", "schoenheitsrepar",
    "malerarbeit", "tapezier", "streichen", "kaution", "leerstand",
]


KATEGORIEN = {
    "wasser": "Wasser und Abwasser",
    "gas": "Heizung und Warmwasser",
    "sonstiges": "Sonstige Betriebskosten",
}

SICHTEN = {
    "mieter": "Abrechnung für den Mieter",
    "vermieter": "Abrechnung für die eigene Wohnung",
}

PARTEIEN = {
    "haus": "Hauptzähler (ganzes Haus)",
    "mieter": "Wohnung des Mieters",
    "vermieter": "Deine Wohnung",
    "gemeinsam": "gemeinsam genutzt (wird verteilt)",
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
    # Leer heißt: die Einheit der Kostenart. Gebraucht wird das, wo an einer
    # Kostenart Zähler mit verschiedenen Einheiten hängen - beim Gas etwa der
    # Hauszähler in m³ und die Wärmemengenzähler in kWh.
    einheit: str = ""

    @property
    def verbrauch(self) -> float:
        return max(0.0, float(self.neu) - float(self.alt))


@dataclass
class Position:
    """Eine Kostenart der Abrechnung (i. d. R. eine Position nach § 2 BetrKV)."""

    bezeichnung: str
    kategorie: str = "sonstiges"   # wasser, gas oder sonstiges
    betrag: float = 0.0            # Gesamtkosten des Hauses im Abrechnungszeitraum
    schluessel: str = "flaeche"
    einheit: str = ""              # z. B. m³ oder kWh
    zaehler: list[Zaehlerstand] = field(default_factory=list)
    zaehler_grundlage: str = "hauptzaehler"
    zaehler_von: str = ""          # Zähler einer anderen Position mitbenutzen
    # Nur diese Zähler der anderen Position benutzen (leer = alle). Damit
    # braucht das Warmwasser die Warmwasserzähler nicht ein zweites Mal.
    zaehler_nur: list[str] = field(default_factory=list)
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
    def verbrauch_gemeinsam(self) -> float:
        """Zähler, die keiner Wohnung allein gehören – etwa die Außenzapfstelle."""
        return self._summe("gemeinsam")

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

    # Umrechnung des Gaszählers von Kubikmetern in Kilowattstunden.
    # Beide Werte stehen auf der Gasrechnung und ändern sich jedes Jahr etwas.
    gas_zustandszahl: float = 0.95
    gas_brennwert: float = 10.5

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


# Diese Kostenarten sind beim ersten Start dabei; alles Weitere lässt sich in
# der App aus dem Katalog hinzufügen.
VORBELEGT = (
    "Wasser", "Abwasser", "Niederschlagswasser",
    "Heizung (Gas)", "Warmwasser (Gas)", "Heizungswartung", "Schornsteinfeger",
    "Grundsteuer", "Müllabfuhr", "Straßenreinigung und Winterdienst",
    "Gartenpflege", "Allgemeinstrom", "Versicherungen",
)


def aus_katalog(name: str, **abweichungen) -> Position:
    """Position aus dem Katalog der abrechenbaren Kostenarten bauen."""
    from .katalog import finde

    art = finde(name)
    if art is None:
        return Position(name, **abweichungen)
    werte = dict(kategorie=art.kategorie, schluessel=art.schluessel,
                 hinweis=f"{art.erlaeuterung} ({art.nummer})")
    werte.update(abweichungen)
    return Position(art.name, **werte)


def standard_positionen() -> list[Position]:
    """Die Kostenarten, mit denen die App startet – ein üblicher Zweifamilienhaus-Satz.

    Jede Zeile stammt aus dem Katalog in `nebenkosten/katalog.py`; dort steht
    auch die Fundstelle in der Betriebskostenverordnung.
    """
    wasserzaehler = [
        Zaehlerstand("Hauptzähler Wasser", "haus"),
        Zaehlerstand("Kaltwasser Mieter", "mieter"),
        Zaehlerstand("Warmwasser Mieter", "mieter"),
        Zaehlerstand("Kaltwasser eigene Wohnung", "vermieter"),
        Zaehlerstand("Warmwasser eigene Wohnung", "vermieter"),
        Zaehlerstand("Außenzapfstelle / Garten", "vermieter"),
    ]
    besonderheiten = {
        "Wasser": dict(einheit="m³", zaehler=wasserzaehler),
        "Abwasser": dict(einheit="m³", zaehler_von="Wasser"),
        # Der Gaszähler des Hauses zählt Kubikmeter, die Wärmemengenzähler
        # Kilowattstunden. Beides an einer Kostenart, deshalb steht die Einheit
        # am einzelnen Zähler und nicht nur an der Kostenart.
        "Heizung (Gas)": dict(
            einheit="kWh", zaehler_grundlage="unterzaehler", grundkosten_anteil=30.0,
            zaehler=[
                Zaehlerstand("Gaszähler Haus (nur zur Information)", "haus", einheit="m³"),
                Zaehlerstand("Wärmemenge Fußbodenheizung Mieter", "mieter", einheit="kWh"),
                Zaehlerstand("Wärmemenge Fußbodenheizung eigene Wohnung", "vermieter",
                             einheit="kWh"),
                Zaehlerstand("Wärmemenge Heizkörper eigene Wohnung", "vermieter",
                             einheit="kWh"),
            ]),
        # Es sind dieselben Warmwasserzähler wie bei „Wasser". Zweimal eintippen
        # heißt zweimal Gelegenheit für einen Zahlendreher - und wenn die beiden
        # Eingaben auseinanderlaufen, rechnet die App mit zwei Wahrheiten.
        "Warmwasser (Gas)": dict(
            einheit="m³", zaehler_grundlage="unterzaehler", grundkosten_anteil=30.0,
            zaehler_von="Wasser",
            zaehler_nur=["Warmwasser Mieter", "Warmwasser eigene Wohnung"]),
    }
    return [aus_katalog(name, **besonderheiten.get(name, {})) for name in VORBELEGT]


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


# Angaben, die Jahr für Jahr gleich bleiben. Sie überstehen „Neue Abrechnung
# beginnen" und lassen sich nur von Hand ändern - alles andere gehört zu genau
# einer Abrechnung und wird dabei geleert.
FESTE_ANGABEN = (
    "vermieter_name", "vermieter_strasse", "vermieter_plz_ort",
    "vermieter_iban", "vermieter_bank",
    "mieter_name", "anrede", "mieter_wohnung",
    "objekt_strasse", "objekt_plz_ort",
    "flaeche_gesamt", "flaeche_mieter",
    "personen_gesamt", "personen_mieter",
    "einheiten_gesamt", "einheiten_mieter", "grundstuecksflaeche",
    "zaehlerdifferenz", "ort", "zahlungsfrist_tage", "anpassung_vorschlagen",
)


def neue_abrechnung(alt: Stammdaten) -> Stammdaten:
    """Alles auf null - bis auf die Angaben, die dauerhaft gelten.

    Gedacht fuer den Jahreswechsel und fuers Aufraeumen nach dem Ausprobieren:
    Namen, Anschriften, Wohnflaechen und Personenzahl bleiben stehen,
    Zeitraum, Betraege, Zaehlerstaende und Vorauszahlungen sind leer.
    """
    return replace(Stammdaten(), **{feld: getattr(alt, feld) for feld in FESTE_ANGABEN})


def as_dict(stammdaten: Stammdaten, positionen: list[Position]) -> dict:
    return {
        "version": 2,
        "stammdaten": asdict(stammdaten),
        "positionen": [asdict(p) for p in positionen],
    }


_WASSERWOERTER = ("wasser", "abwasser", "niederschlag", "kanal", "hebeanlage",
                  "legionell", "entwässerung", "entwaesserung")
_GASWOERTER = ("heiz", "warmwasser", "gas", "öl", "oel", "brennstoff", "schornstein",
               "wärme", "waerme", "tank", "kamin")


def kategorie_raten(bezeichnung: str) -> str:
    """Bereich aus dem Namen ableiten – für Daten aus früheren Fassungen."""
    name = bezeichnung.lower()
    if any(wort in name for wort in _GASWOERTER):
        return "gas"
    if any(wort in name for wort in _WASSERWOERTER):
        return "wasser"
    return "sonstiges"


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


def _warmwasser_zusammenlegen(wasser: Position, warm: Position) -> None:
    """Die Warmwasserzaehler beim Warmwasser entfernen und die des Wassers nehmen.

    Es sind dieselben Zaehler. Abgelesen und eingetragen werden sie beim Wasser;
    fuer die Gaskosten wird nur darauf zugegriffen. Beim Warmwasser bleibt
    deshalb nichts stehen, was man eintippen koennte.
    """
    vorhanden = {z.name.strip().lower(): z.name for z in wasser.zaehler}
    namen = []
    for z in warm.zaehler:
        treffer = vorhanden.get(z.name.strip().lower())
        if treffer is None:
            wasser.zaehler.append(z)
            treffer = z.name
        namen.append(treffer)
    warm.zaehler_nur = namen
    warm.zaehler_von = wasser.bezeichnung
    warm.zaehler = []


def _nachziehen(positionen: list[Position]) -> list[Position]:
    """Gespeicherte Daten auf den heutigen Aufbau bringen.

    Zwei Dinge, die frueher falsch angelegt waren:

    * Das Warmwasser hatte eigene Zaehler, obwohl es dieselben sind wie beim
      Wasser - zweimal eintippen, zwei Gelegenheiten fuer einen Zahlendreher.
    * Am Gas hingen Zaehler mit verschiedenen Einheiten (Hauszaehler m³,
      Waermemengenzaehler kWh), angezeigt wurde aber ueberall die Einheit der
      Kostenart.
    """
    nach_name = {p.bezeichnung.strip().lower(): p for p in positionen}
    wasser = nach_name.get("wasser")
    warm = nach_name.get("warmwasser (gas)")
    if wasser and warm:
        if warm.zaehler and not warm.zaehler_von:
            _warmwasser_zusammenlegen(wasser, warm)
        if not warm.zaehler_nur:
            # Ohne diese Liste naehme das Warmwasser alle Wasserzaehler, also
            # auch Kaltwasser und Garten. Zwischenstaende aus aelteren Fassungen
            # haben sie nicht - deshalb hier aus den Namen erschliessen.
            gefunden = [z.name for z in wasser.zaehler
                        if "warmwasser" in z.name.strip().lower()]
            if gefunden:
                warm.zaehler_nur = gefunden
                warm.zaehler_von = wasser.bezeichnung

    for pos in positionen:
        for z in pos.zaehler:
            if z.einheit:
                continue
            name = z.name.strip().lower()
            if name.startswith("gaszähler") or name.startswith("gaszaehler"):
                z.einheit = "m³"
            elif name.startswith("wärmemenge") or name.startswith("waermemenge"):
                z.einheit = "kWh"
    return positionen


def from_dict(daten: dict) -> tuple[Stammdaten, list[Position]]:
    stamm_felder = set(Stammdaten.__dataclass_fields__)
    pos_felder = set(Position.__dataclass_fields__) - {"zaehler"}
    stamm = Stammdaten(**{k: v for k, v in daten.get("stammdaten", {}).items()
                          if k in stamm_felder})
    positionen = []
    for p in daten.get("positionen", []):
        werte = {k: v for k, v in p.items() if k in pos_felder}
        if not werte.get("kategorie"):
            werte["kategorie"] = kategorie_raten(str(p.get("bezeichnung", "")))
        positionen.append(Position(zaehler=_zaehler_aus_dict(p), **werte))
    return stamm, _nachziehen(positionen) if positionen else standard_positionen()
