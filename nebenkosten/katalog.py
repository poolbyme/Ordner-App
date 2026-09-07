"""Alle Kosten, die ein Vermieter auf den Mieter umlegen darf – und was nicht.

Grundlage ist § 2 der Betriebskostenverordnung (BetrKV). Die Verordnung zählt
17 Nummern auf; was dort nicht steht, darf nur unter Nummer 17 abgerechnet
werden und auch nur dann, wenn es im Mietvertrag ausdrücklich benannt ist.

Was hier nicht steht, ist keine Betriebskostenart. Die Liste ist deshalb
gleichzeitig die Auswahl in der App und die Sperre gegen unzulässige Zeilen.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Kostenart:
    """Eine abrechenbare Kostenart mit ihrer Fundstelle in der Verordnung."""

    name: str
    nummer: str                 # Fundstelle, z. B. "§ 2 Nr. 4a BetrKV"
    kategorie: str              # wasser, gas oder sonstiges
    schluessel: str = "flaeche"
    erlaeuterung: str = ""
    vertrag_noetig: bool = False   # nur bei „sonstige Betriebskosten“
    hinweis: str = ""


KATALOG: tuple[Kostenart, ...] = (
    # --- Nr. 1: laufende öffentliche Lasten ------------------------------
    Kostenart("Grundsteuer", "§ 2 Nr. 1 BetrKV", "sonstiges",
              erlaeuterung="Grundsteuerbescheid der Gemeinde"),

    # --- Nr. 2: Wasserversorgung -----------------------------------------
    Kostenart("Wasser", "§ 2 Nr. 2 BetrKV", "wasser", "verbrauch",
              erlaeuterung="Verbrauchsgebühr des Wasserversorgers"),
    Kostenart("Grundgebühr Wasser / Zählermiete", "§ 2 Nr. 2 BetrKV", "wasser",
              erlaeuterung="verbrauchsunabhängiger Teil der Wasserrechnung"),
    Kostenart("Eichung und Wartung der Wasserzähler", "§ 2 Nr. 2 BetrKV", "wasser",
              erlaeuterung="Miete, Eichung und Ablesung der Zähler"),
    Kostenart("Wasseraufbereitung / Enthärtungsanlage", "§ 2 Nr. 2 BetrKV", "wasser",
              erlaeuterung="Betrieb und Aufbereitungsstoffe, keine Anschaffung"),
    Kostenart("Betrieb einer eigenen Wasserversorgung", "§ 2 Nr. 2 BetrKV", "wasser",
              erlaeuterung="Hausbrunnen oder eigene Pumpe: Strom und Wartung"),

    # --- Nr. 3: Entwässerung ---------------------------------------------
    Kostenart("Abwasser", "§ 2 Nr. 3 BetrKV", "wasser", "verbrauch",
              erlaeuterung="Schmutzwassergebühr der Gemeinde"),
    Kostenart("Niederschlagswasser", "§ 2 Nr. 3 BetrKV", "wasser",
              erlaeuterung="Regenwassergebühr, meist nach versiegelter Fläche"),
    Kostenart("Abwasserhebeanlage / Pumpe", "§ 2 Nr. 3 BetrKV", "wasser",
              erlaeuterung="Strom und Wartung, keine Reparatur"),
    Kostenart("Entleerung von Grube oder Kleinkläranlage", "§ 2 Nr. 3 BetrKV", "wasser",
              erlaeuterung="regelmäßige Entleerung und Überprüfung"),

    # --- Nr. 4: Heizung ---------------------------------------------------
    Kostenart("Heizung (Gas)", "§ 2 Nr. 4a BetrKV", "gas", "verbrauch",
              erlaeuterung="Erdgas für die Heizung, ohne den Warmwasseranteil"),
    Kostenart("Heizung (Öl)", "§ 2 Nr. 4a BetrKV", "gas", "verbrauch",
              erlaeuterung="Heizöl einschließlich Lieferung"),
    Kostenart("Heizung (Pellets, Holz)", "§ 2 Nr. 4a BetrKV", "gas", "verbrauch",
              erlaeuterung="Brennstoff einschließlich Lieferung"),
    Kostenart("Fernwärme", "§ 2 Nr. 4c BetrKV", "gas", "verbrauch",
              erlaeuterung="Wärmelieferung und Betrieb der Hausanlage"),
    Kostenart("Betriebsstrom der Heizung", "§ 2 Nr. 4a BetrKV", "gas",
              erlaeuterung="Strom für Brenner, Pumpen und Steuerung"),
    Kostenart("Heizungswartung", "§ 2 Nr. 4a BetrKV", "gas",
              erlaeuterung="jährliche Wartung, Einstellung durch die Fachkraft"),
    Kostenart("Reinigung der Heizanlage und des Heizraums", "§ 2 Nr. 4a BetrKV", "gas",
              erlaeuterung="Reinigung von Anlage, Betriebsraum und Öltank"),
    Kostenart("Schornsteinfeger", "§ 2 Nr. 12 BetrKV", "gas",
              erlaeuterung="Kehr- und Messgebühren, Feuerstättenschau"),
    Kostenart("Tankreinigung / Immissionsmessung", "§ 2 Nr. 4a BetrKV", "gas",
              erlaeuterung="bei Öl- oder Flüssiggasheizung"),
    Kostenart("Miete und Eichung der Wärmezähler", "§ 2 Nr. 4a BetrKV", "gas",
              erlaeuterung="Ausstattung zur Verbrauchserfassung"),
    Kostenart("Kosten der Heizkostenabrechnung", "§ 2 Nr. 4a BetrKV", "gas",
              erlaeuterung="Ablesung, Berechnung und Aufteilung durch einen Dienstleister"),
    Kostenart("Wartung der Etagenheizung", "§ 2 Nr. 4d BetrKV", "gas",
              erlaeuterung="Reinigung und Wartung von Gasetagenheizungen"),

    # --- Nr. 5 und 6: Warmwasser -----------------------------------------
    Kostenart("Warmwasser (Gas)", "§ 2 Nr. 5a BetrKV", "gas", "verbrauch",
              erlaeuterung="Anteil der Gaskosten für die Warmwasserbereitung"),
    Kostenart("Warmwasser (Strom, Boiler)", "§ 2 Nr. 5c BetrKV", "gas", "verbrauch",
              erlaeuterung="Strom für gesonderte Warmwassergeräte"),
    Kostenart("Legionellenprüfung", "§ 2 Nr. 5a BetrKV", "wasser",
              erlaeuterung="nur bei zentraler Warmwasseranlage über 400 l Speicher"),

    # --- Nr. 7: Aufzug ----------------------------------------------------
    Kostenart("Aufzug", "§ 2 Nr. 7 BetrKV", "sonstiges",
              erlaeuterung="Strom, Wartung, Notruf, Überwachung, Reinigung"),

    # --- Nr. 8: Straßenreinigung und Müll --------------------------------
    Kostenart("Straßenreinigung und Winterdienst", "§ 2 Nr. 8 BetrKV", "sonstiges",
              erlaeuterung="Gebühr der Gemeinde oder Rechnung des Dienstleisters"),
    Kostenart("Müllabfuhr", "§ 2 Nr. 8 BetrKV", "sonstiges", "personen",
              erlaeuterung="Gebührenbescheid; bei eigener Tonne direkt zuordnen"),
    Kostenart("Sperrmüll (regelmäßig)", "§ 2 Nr. 8 BetrKV", "sonstiges",
              erlaeuterung="nur wiederkehrende Abfuhr, keine einmalige Entrümpelung"),

    # --- Nr. 9: Reinigung und Ungeziefer ---------------------------------
    Kostenart("Gebäudereinigung", "§ 2 Nr. 9 BetrKV", "sonstiges",
              erlaeuterung="Treppenhaus, Keller, Zugänge, Waschküche"),
    Kostenart("Ungezieferbekämpfung", "§ 2 Nr. 9 BetrKV", "sonstiges",
              erlaeuterung="laufende Vorbeugung, keine einmalige Beseitigung"),

    # --- Nr. 10: Gartenpflege --------------------------------------------
    Kostenart("Gartenpflege", "§ 2 Nr. 10 BetrKV", "sonstiges",
              erlaeuterung="Pflege der Grünflächen, Zugänge und Spielplätze; "
                           "eigene Arbeit zum üblichen Preis ohne Mehrwertsteuer"),
    Kostenart("Baumpflege und Baumfällung", "§ 2 Nr. 10 BetrKV", "sonstiges",
              erlaeuterung="Schnitt und das Fällen kranker Bäume samt Ersatzpflanzung"),

    # --- Nr. 11: Beleuchtung ---------------------------------------------
    Kostenart("Allgemeinstrom", "§ 2 Nr. 11 BetrKV", "sonstiges",
              erlaeuterung="Licht in Flur, Keller, Hof und Außenbereich"),

    # --- Nr. 13: Versicherungen ------------------------------------------
    Kostenart("Versicherungen", "§ 2 Nr. 13 BetrKV", "sonstiges",
              erlaeuterung="Gebäude-, Elementar-, Glas- und Haftpflichtversicherung"),

    # --- Nr. 14: Hauswart -------------------------------------------------
    Kostenart("Hausmeister", "§ 2 Nr. 14 BetrKV", "sonstiges",
              erlaeuterung="Lohn ohne Reparatur- und Verwaltungsanteil"),

    # --- Nr. 16: Wascheinrichtungen --------------------------------------
    Kostenart("Gemeinsame Waschmaschine", "§ 2 Nr. 16 BetrKV", "sonstiges", "einheiten",
              erlaeuterung="Strom, Wasser und Wartung gemeinsam genutzter Geräte"),

    # --- Nr. 17: sonstige Betriebskosten (nur mit Vereinbarung) ----------
    Kostenart("Rauchwarnmelder – Wartung", "§ 2 Nr. 17 BetrKV", "sonstiges", "einheiten",
              erlaeuterung="nur die Wartung; die Miete der Geräte ist nicht umlagefähig",
              vertrag_noetig=True),
    Kostenart("Dachrinnenreinigung", "§ 2 Nr. 17 BetrKV", "sonstiges",
              erlaeuterung="nur bei regelmäßiger Wiederkehr", vertrag_noetig=True),
    Kostenart("Wartung der Lüftungsanlage", "§ 2 Nr. 17 BetrKV", "sonstiges",
              erlaeuterung="Lüftung, Dunstabzug, Wärmerückgewinnung", vertrag_noetig=True),
    Kostenart("Prüfung der Elektroanlage", "§ 2 Nr. 17 BetrKV", "sonstiges",
              erlaeuterung="wiederkehrender E-Check", vertrag_noetig=True),
    Kostenart("Wartung der Feuerlöscher", "§ 2 Nr. 17 BetrKV", "sonstiges",
              erlaeuterung="wiederkehrende Prüfung", vertrag_noetig=True),
    Kostenart("Prüfung der Blitzschutzanlage", "§ 2 Nr. 17 BetrKV", "sonstiges",
              erlaeuterung="wiederkehrende Prüfung", vertrag_noetig=True),
    Kostenart("Wartung von Tür- und Toranlagen", "§ 2 Nr. 17 BetrKV", "sonstiges",
              erlaeuterung="Garagentor, Türschließanlage, Gegensprechanlage",
              vertrag_noetig=True),
    Kostenart("Betrieb von Schwimmbad oder Sauna", "§ 2 Nr. 17 BetrKV", "sonstiges",
              erlaeuterung="laufender Betrieb gemeinschaftlicher Anlagen",
              vertrag_noetig=True),

    # --- Nr. 15: seit 01.07.2024 gestrichen ------------------------------
    Kostenart("Kabelanschluss (bis 30.06.2024)", "§ 2 Nr. 15 BetrKV", "sonstiges", "einheiten",
              erlaeuterung="Seit dem 01.07.2024 nicht mehr über die Nebenkosten umlegbar. "
                           "Nur für Zeiträume davor.",
              hinweis="läuft aus"),
)

# Was in keine Betriebskostenabrechnung gehört – mit dem Grund dafür.
VERBOTEN: tuple[tuple[tuple[str, ...], str], ...] = (
    (("reparatur", "instandhaltung", "instandsetzung", "reparieren", "defekt",
      "schaden", "notdienst"),
     "Reparatur und Instandhaltung halten das Haus in Ordnung. Diese Kosten trägt der "
     "Eigentümer (§ 1 Abs. 2 Nr. 2 BetrKV)."),
    (("renovierung", "renovieren", "schönheitsrepar", "schoenheitsrepar", "malerarbeit",
      "maler ", "tapezier", "streichen", "bodenbelag", "laminat"),
     "Renovierung und Schönheitsreparaturen sind keine laufenden Betriebskosten."),
    (("sanierung", "modernisierung", "dämmung", "daemmung", "neubau", "umbau",
      "neuanschaffung", "anschaffung"),
     "Sanierung und Modernisierung sind Investitionen in das Haus, keine Betriebskosten. "
     "Sie können nur über eine Mieterhöhung weitergegeben werden."),
    (("verwaltung", "verwalter", "hausverwaltung", "kontoführung", "kontofuehrung",
      "bankgebühr", "bankgebuehr", "porto", "buchhaltung", "steuerberat"),
     "Verwaltungskosten trägt der Vermieter (§ 1 Abs. 2 Nr. 1 BetrKV) – auch dein eigener "
     "Aufwand fürs Abrechnen."),
    (("rücklage", "ruecklage", "instandhaltungsrücklage"),
     "Rücklagen sind Vorsorge für künftige Reparaturen, keine angefallenen Betriebskosten."),
    (("mietausfall", "leerstand", "kaution", "mietminderung"),
     "Das ist das unternehmerische Risiko des Vermieters."),
    (("rechtsschutz", "anwalt", "gericht", "inkasso", "mahnkosten", "räumung"),
     "Rechtsverfolgung gehört nicht zu den Betriebskosten."),
)


def verboten(bezeichnung: str) -> str:
    """Grund, warum die Bezeichnung nicht abrechenbar ist – sonst leerer Text."""
    name = f" {bezeichnung.lower()} "
    for woerter, grund in VERBOTEN:
        if any(wort in name for wort in woerter):
            return grund
    return ""


def nach_kategorie(kategorie: str) -> list[Kostenart]:
    return [k for k in KATALOG if k.kategorie == kategorie]


def finde(name: str) -> Kostenart | None:
    gesucht = name.strip().lower()
    for art in KATALOG:
        if art.name.lower() == gesucht:
            return art
    return None
