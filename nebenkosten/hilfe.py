"""Erklärungen zu jedem Bereich und eine Suche über die ganze App.

Beides hängt an einer einzigen Liste: `THEMEN`. Jeder Eintrag sagt, wo etwas
steht, was dort hineingehört und unter welchen Wörtern man danach sucht.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import streamlit as st

# Reihenfolge der Bereiche; die Schlüssel steuern auch die Navigation.
BEREICHE = {
    "vermieter": "1 · Vermieter",
    "mieter": "2 · Mieter",
    "objekt": "3 · Mietobjekt",
    "art": "4 · Abrechnungsart",
    "kosten": "5 · Kosten",
    "zaehler": "6 · Zählerstände",
    "weitere": "7 · Sonstige Angaben",
    "vz": "8 · Vorauszahlungen",
    "ergebnis": "9 · Fertige Abrechnung",
}


@dataclass
class Thema:
    """Ein Stichwort mit dem Ort, an dem es in der App eingetragen wird."""

    titel: str
    bereich: str
    wo: str                                  # genaue Stelle im Bereich
    woerter: list[str] = field(default_factory=list)
    hinweis: str = ""


THEMEN: list[Thema] = [
    # --- Gas und Heizung --------------------------------------------------
    Thema("Gasrechnung", "kosten", "Aufklapper „Gasrechnung auf Heizung und Warmwasser aufteilen“",
          ["gas", "gasrechnung", "erdgas", "brennstoff", "gasabrechnung", "kwh"],
          "Dort wird der Betrag auf die Zeilen „Heizung (Gas)“ und „Warmwasser (Gas)“ verteilt."),
    Thema("Zustandszahl und Brennwert", "kosten", "im Gasrechner, Block „Gasverbrauch“",
          ["zustandszahl", "brennwert", "z-zahl", "umrechnung", "kubikmeter", "m3"],
          "Beide Werte stehen auf der Gasrechnung. kWh = m³ × Zustandszahl × Brennwert."),
    Thema("Gaszähler ablesen", "zaehler", "Position „Heizung (Gas)“, Zeile „Gaszähler Haus“",
          ["gaszähler", "gasuhr", "gaszaehler", "gasstand"],
          "Anfangs- und Endstand in m³. Der Zähler läuft nur zur Information mit."),
    Thema("Wärmemengenzähler", "zaehler", "Position „Heizung (Gas)“",
          ["wärmemenge", "waermemenge", "wmz", "heizkörper", "heizkoerper",
           "fußbodenheizung", "fussbodenheizung", "heizung"],
          "Je eine Zeile pro Zähler, mit Angabe wem er gehört."),
    Thema("Heizungswartung", "kosten", "Bereich „Heizung und Warmwasser“",
          ["wartung", "heizungswartung", "kundendienst", "therme"],
          "Nur die Wartung, keine Reparaturen."),
    Thema("Schornsteinfeger", "kosten", "Bereich „Heizung und Warmwasser“",
          ["schornsteinfeger", "kaminkehrer", "kehrgebühr", "feuerstättenschau"]),

    # --- Wasser -----------------------------------------------------------
    Thema("Wasserrechnung", "kosten", "Bereich „Wasser und Abwasser“, Zeile „Wasser“",
          ["wasser", "frischwasser", "trinkwasser", "wasserversorgung", "wasserwerk"]),
    Thema("Abwasser", "kosten", "Bereich „Wasser und Abwasser“, Zeile „Abwasser“",
          ["abwasser", "schmutzwasser", "kanal", "entwässerung", "entwaesserung"],
          "Rechnet mit den Zählerständen von „Wasser“ – nichts doppelt eintragen."),
    Thema("Niederschlagswasser", "kosten", "Bereich „Wasser und Abwasser“",
          ["niederschlag", "regenwasser", "oberflächenwasser", "versiegelt"]),
    Thema("Kalt- und Warmwasserzähler", "zaehler", "Position „Wasser“",
          ["kaltwasser", "warmwasser", "wasseruhr", "wasserzähler", "wasserzaehler",
           "hauptzähler", "hauptzaehler", "zählerstand", "zaehlerstand", "ablesen"],
          "Hauptzähler, beide Wohnungen und die Außenzapfstelle stehen dort untereinander."),
    Thema("Gartenwasser", "zaehler", "Position „Wasser“, Zeile „Außenzapfstelle / Garten“",
          ["garten", "außenzapfstelle", "aussenzapfstelle", "bewässerung", "gartenwasser",
           "außenhahn", "aussenhahn"],
          "Gehört der Hahn nur dir, steht der Zähler auf „Deine Wohnung“."),

    # --- Sonstige Kosten --------------------------------------------------
    Thema("Grundsteuer", "kosten", "Bereich „Sonstige Betriebskosten“",
          ["grundsteuer", "finanzamt", "steuerbescheid", "gemeinde"]),
    Thema("Müllabfuhr", "kosten", "Bereich „Sonstige Betriebskosten“",
          ["müll", "muell", "abfall", "tonne", "restmüll", "biotonne"],
          "Eigene Tonne des Mieters: Verteilung auf „nur der Mieter“ stellen."),
    Thema("Versicherungen", "kosten", "Bereich „Sonstige Betriebskosten“",
          ["versicherung", "gebäudeversicherung", "haftpflicht", "elementar", "police"],
          "Keine Rechtsschutz-, Reparatur- oder Mietausfallversicherung."),
    Thema("Allgemeinstrom", "kosten", "Bereich „Sonstige Betriebskosten“",
          ["strom", "allgemeinstrom", "beleuchtung", "flur", "keller", "außenlicht"]),
    Thema("Gartenpflege", "kosten", "Bereich „Sonstige Betriebskosten“",
          ["gartenpflege", "rasen", "hecke", "gärtner", "gaertner", "laub"],
          "Eigene Arbeit darf zum üblichen Preis ohne Mehrwertsteuer angesetzt werden."),
    Thema("Straßenreinigung und Winterdienst", "kosten", "Bereich „Sonstige Betriebskosten“",
          ["straßenreinigung", "strassenreinigung", "winterdienst", "schnee", "streuen"]),
    Thema("Selten gebrauchte Kostenarten", "kosten", "Bereich „Sonstige Betriebskosten“, Zeile anhaken",
          ["rauchmelder", "rauchwarnmelder", "dachrinne", "lüftung", "e-check", "elektro",
           "hausmeister", "aufzug", "kabel", "legionellen", "ungeziefer", "reinigung"],
          "Diese Zeilen sind vorbereitet, aber abgewählt – Häkchen links setzen."),
    Thema("Lohnkosten für die Steuer des Mieters", "kosten", "Spalte „davon Lohnkosten“ (Mehr Einstellungen)",
          ["lohnkosten", "35a", "handwerker", "steuererklärung", "arbeitskosten"]),
    Thema("Grundkosten und Verbrauchskosten", "kosten", "Spalte „Grundkosten (%)“ (Mehr Einstellungen)",
          ["grundkosten", "verbrauchskosten", "30 prozent", "70 prozent", "aufteilung"],
          "Üblich sind 30 % nach Wohnfläche, der Rest nach Verbrauch."),

    # --- Stammdaten und Abrechnung ---------------------------------------
    Thema("Wohnfläche und Grundstück", "vermieter", "Abschnitt „Das Haus insgesamt“",
          ["wohnfläche", "wohnflaeche", "quadratmeter", "qm", "grundstück", "fläche"]),
    Thema("Deine Bankverbindung", "vermieter", "Feld „Deine IBAN“",
          ["iban", "konto", "bank", "überweisung", "bankverbindung"]),
    Thema("Mieter und Personenzahl", "objekt", "Bereich „Mietobjekt“",
          ["mieter", "name", "personen", "bewohner", "anschrift"]),
    Thema("Ein- oder Auszug im Jahr", "art", "Art der Abrechnung → „Abrechnung zum Mietende“",
          ["auszug", "einzug", "mietende", "kündigung", "umzug", "zeitanteilig"]),
    Thema("Zwischenabrechnung", "art", "Art der Abrechnung → „Zwischenabrechnung“",
          ["zwischenabrechnung", "anbieterwechsel", "zwischenstand", "momentaufnahme"]),
    Thema("Abrechnungszeitraum", "art", "Abschnitt oben, „Vom“ und „Bis“",
          ["zeitraum", "jahr", "abrechnungsjahr", "von bis", "frist"]),
    Thema("Vorauszahlungen des Mieters", "vz", "Abschnitt „Was hat dein Mieter schon gezahlt?“",
          ["vorauszahlung", "abschlag", "monatlich", "vorschuss", "nebenkostenvorauszahlung"]),
    Thema("CO2-Kosten", "weitere", "Abschnitt „CO2-Kosten“",
          ["co2", "co2-kosten", "emission", "klima", "behg", "stufenmodell"],
          "Bei Gas oder Öl musst du einen Teil selbst tragen."),
    Thema("PDF erstellen", "ergebnis", "unten, Knopf „Abrechnung für den Mieter als PDF speichern“",
          ["pdf", "drucken", "herunterladen", "download", "fertig", "erstellen", "ausdrucken"]),
    Thema("Nachzahlung oder Guthaben", "ergebnis", "oben, die drei Kacheln",
          ["nachzahlung", "guthaben", "ergebnis", "saldo", "erstattung"]),
    Thema("Aufstellung für die eigene Wohnung", "ergebnis", "unten, zweiter PDF-Knopf",
          ["eigene wohnung", "eigene aufstellung", "steuer", "anlage v", "unterlagen"],
          "Muss im Tab „Vorauszahlungen“ eingeschaltet sein."),
]

# Was in jedem Bereich erklärt wird, wenn man auf das Fragezeichen klickt.
ERKLAERUNGEN = {
    "vermieter": (
        "Du und dein Haus",
        """
Das trägst du **einmal** ein, danach steht es.

**Du als Vermieter**

* **Name und Anschrift** kommen so in den Briefkopf der Abrechnung.
* **IBAN** erscheint im PDF, falls dein Mieter nachzahlen muss. Bei einem
  Guthaben braucht die App sie nicht.
* **Ort** steht in der Datumszeile über dem Anschreiben.

**Das Haus insgesamt** – die Zahlen für das ganze Gebäude, deine eigene Wohnung
mitgezählt:

* **Adresse des Hauses** muss auf der Abrechnung stehen.
* **Wohnfläche des ganzen Hauses** – die wichtigste Zahl der ganzen App: Der
  Anteil des Mieters ergibt sich aus seiner Fläche geteilt durch diese.
* **Personen im Haus insgesamt** – alle Bewohner zusammen.
* **Grundstück** ist nur eine Angabe im Kopf der Abrechnung.

Die Zahlen der **vermieteten Wohnung** stehen nicht hier, sondern unter
„3 · Mietobjekt".

Diese Angaben überstehen „Alles auf null setzen" – sie lassen sich nur hier
ändern.
        """,
    ),
    "mieter": (
        "Wer die Abrechnung bekommt",
        """
Hier steht nur die **Person**: Name und Anrede für das Anschreiben.

Alles, was zur **Wohnung** gehört – Wohnfläche, Personenzahl, Bezeichnung –
steht unter „3 · Mietobjekt". Das bleibt gleich, auch wenn ein neuer Mieter
einzieht; dann änderst du hier nur den Namen.
        """,
    ),
    "objekt": (
        "Die vermietete Wohnung",
        """
Die Zahlen der Wohnung, die du vermietest – nicht die des ganzen Hauses.

* **Bezeichnung der Wohnung** erscheint so im PDF, etwa „Wohnung Obergeschoss".
* **Wohnfläche der Mietwohnung** – danach wird der größte Teil der Kosten
  verteilt. Die Zahl steht im Mietvertrag.
* **Personen in der Mietwohnung** – nur für Kosten, die nach Köpfen geteilt
  werden, vor allem die Müllabfuhr.

Die Wohnfläche des **ganzen Hauses** steht unter „1 · Vermieter". Ändert sich
nichts an der Wohnung, fasst du das nie wieder an.
        """,
    ),
    "art": (
        "Was für eine Abrechnung ist das?",
        """
* **Art der Abrechnung** – *Jahresabrechnung* ist der Normalfall.
  *Zum Mietende* rechnet bis zum Auszugstag und teilt alles tageweise.
  *Zwischenabrechnung* ist eine unverbindliche Momentaufnahme.
* **Zeitraum** – meist 01.01. bis 31.12. Länger als zwölf Monate darf er nicht sein.
* **Mietzeit** – nur nötig, wenn der Mieter mitten im Jahr ein- oder ausgezogen ist.

Diese Angaben gelten für genau eine Abrechnung und werden von „Alles auf null
setzen" geleert.
        """,
    ),
    "weitere": (
        "Angaben, die man selten braucht",
        """
Alles, was nicht jedes Jahr anfällt oder nicht in die anderen Bereiche passt.

* **CO2-Kosten** – heizt du mit Gas oder Öl, trägst du seit 2023 einen Teil der
  CO2-Abgabe selbst. Wie viel, hängt davon ab, wie schlecht das Haus gedämmt ist
  (Stufenmodell des CO2KostAufG). Ausstoß und Kosten stehen auf der Rechnung des
  Versorgers.
* **Zählerdifferenz** – der Hauptzähler zeigt fast immer mehr an als die
  Wohnungszähler zusammen. Hier stellst du ein, nach welchem Maßstab diese
  Differenz auf die Wohnungen verteilt wird.
* **Anschreiben** – Datum der Abrechnung und die Frist, bis wann eine Nachzahlung
  überwiesen sein soll.
        """,
    ),
    "kosten": (
        "Was das Haus gekostet hat",
        """
Trag ein, was **für das ganze Haus** angefallen ist – die App rechnet den Anteil
des Mieters selbst aus. Die Zeilen sind in drei Bereiche sortiert: Wasser,
Heizung und Warmwasser, Sonstiges.

* **Kosten fürs ganze Haus** – der Betrag vom Beleg, brutto.
* **Verteilung** – nach Wohnfläche ist der Normalfall. *Nach Zählerstand* nur,
  wenn es dafür Zähler gibt. *Nur der Mieter* bzw. *nur ich selbst* für Kosten,
  die eine Seite allein trägt.
* **Welcher Beleg?** – Merkzettel für dich, steht nicht im PDF.
* Zeilen, die es bei dir nicht gibt, links abwählen; eigene unten anfügen.

Zwei Rechner helfen: die **Gasrechnung aufteilen** (Heizung/Warmwasser) und
weiter unten die Übersicht, was überhaupt umlagefähig ist.
        """,
    ),
    "zaehler": (
        "Zählerstände eintragen",
        """
Zu jeder Kostenart, die auf *nach Zählerstand* steht, gehört hier eine Tabelle.

* Jede Zeile ist **ein Zähler**: Name, wem er gehört, Stand am Anfang und am Ende.
* **Hauptzähler** ist der Zähler fürs ganze Haus, dazu die Zähler der Wohnungen.
* Was der Hauptzähler mehr anzeigt als die Unterzähler, ist die **Differenz** –
  sie wird nach dem oben gewählten Maßstab auf beide verteilt.
* **Gemeinsam genutzt** ist für Zähler, die keiner Wohnung allein gehören.
* Neue Zähler unten anfügen, nicht gebrauchte löschen.

Bitte alle Zähler am selben Tag ablesen, sonst passen die Zeiträume nicht zusammen.
        """,
    ),
    "vz": (
        "Vorauszahlungen und CO2",
        """
* **Vorauszahlung pro Monat** – der Betrag aus dem Mietvertrag, den dein Mieter
  zusätzlich zur Kaltmiete überweist, mal der Anzahl der Monate.
* Hat er tatsächlich etwas anderes gezahlt, das Häkchen setzen und die Summe
  eintragen.
* **CO2-Kosten** – bei Gas- oder Ölheizung musst du seit 2023 einen Teil selbst
  tragen. Menge und Kosten stehen auf der Energierechnung; die App rechnet
  deinen Anteil aus und zieht ihn ab.
* **Aufstellung für die eigene Wohnung** – zweites PDF für deine Unterlagen.
        """,
    ),
    "ergebnis": (
        "Prüfen und PDF erstellen",
        """
* Die drei Kacheln zeigen den Anteil des Mieters, seine Vorauszahlungen und das
  Ergebnis.
* **Rote Meldungen** musst du beheben, bevor es ein PDF gibt. **Gelbe** sind
  Hinweise, die du prüfen solltest.
* Die Tabelle zeigt für jede Zeile, wie verteilt wurde – dasselbe steht im PDF.
* Unten der Knopf für das PDF. Beim Herunterladen legt die App zusätzlich eine
  Kopie im Archiv ab, die du in der Seitenleiste wiederfindest.
        """,
    ),
}


def knopf(bereich: str) -> None:
    """Fragezeichen, das die Erklärung zum Bereich aufklappt."""
    titel, text = ERKLAERUNGEN.get(
        bereich, ("Hilfe", "Für diesen Bereich gibt es noch keine Erklärung."))
    with st.popover("?", help=f"Was gehört hier hin? – {titel}"):
        st.markdown(f"### {titel}")
        st.markdown(text)


def ueberschrift(bereich: str, text: str, unterzeile: str = "") -> None:
    """Überschrift mit Fragezeichen rechts daneben."""
    links, rechts = st.columns([12, 1], vertical_alignment="center")
    with links:
        st.subheader(text, anchor=False)
    with rechts:
        knopf(bereich)
    if unterzeile:
        st.caption(unterzeile)


def _passt(begriff: str, thema: Thema) -> int:
    """Trefferstärke: 0 = kein Treffer, größer ist besser."""
    begriff = begriff.strip().lower()
    if not begriff:
        return 0
    if any(begriff == wort for wort in thema.woerter):
        return 3
    if any(wort.startswith(begriff) or begriff in wort for wort in thema.woerter):
        return 2
    if begriff in thema.titel.lower() or begriff in thema.wo.lower():
        return 1
    return 0


def suche(begriff: str, positionen=None) -> list[tuple[int, Thema]]:
    """Themen zum Suchbegriff, beste zuerst – dazu die eigenen Kostenarten."""
    treffer = [(staerke, thema) for thema in THEMEN
               if (staerke := _passt(begriff, thema))]

    begriff_klein = begriff.strip().lower()
    if positionen and len(begriff_klein) >= 2:
        for pos in positionen:
            name = pos.bezeichnung.lower()
            if begriff_klein in name and not any(t.titel == pos.bezeichnung for _, t in treffer):
                treffer.append((2, Thema(
                    pos.bezeichnung, "kosten",
                    f"deine Zeile „{pos.bezeichnung}“ im Bereich "
                    f"{'Wasser und Abwasser' if pos.kategorie == 'wasser' else 'Heizung und Warmwasser' if pos.kategorie == 'gas' else 'Sonstige Betriebskosten'}",
                    hinweis="" if pos.aktiv else "Die Zeile ist noch abgewählt.")))
            for zst in pos.zaehler:
                if begriff_klein in zst.name.lower():
                    treffer.append((2, Thema(
                        zst.name, "zaehler",
                        f"Zähler „{zst.name}“ in der Position „{pos.bezeichnung}“")))
    treffer.sort(key=lambda t: -t[0])
    return treffer[:8]
