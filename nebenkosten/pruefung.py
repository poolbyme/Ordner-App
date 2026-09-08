"""Prüft vor dem Abschließen, was in der Abrechnung noch fehlt.

Unterschieden wird nach:

* **Pflicht** – ohne diese Angaben rechnet die App falsch oder die Abrechnung
  ist formal unbrauchbar. Solange etwas fehlt, gibt es kein PDF.
* **Kann** – Dinge, die man üblicherweise abrechnet, dieses Jahr aber vielleicht
  gar nicht hatte. Nur eine Erinnerung.
* **Achtung** – Zeilen, die so nicht in eine Nebenkostenabrechnung gehören.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .berechnung import Ergebnis, eur
from .modell import NICHT_UMLAGEFAEHIG_STICHWORTE, Position, Stammdaten

# Kostenarten, die fast jedes Haus hat. Fehlen sie, wird nachgefragt.
UEBLICH = {
    "Grundsteuer": "Der Bescheid kommt jedes Jahr von der Gemeinde.",
    "Versicherungen": "Gebäude- und Haftpflichtversicherung zahlst du jährlich.",
    "Müllabfuhr": "Gebührenbescheid der Gemeinde.",
    "Niederschlagswasser": "Steht meist auf demselben Bescheid wie das Abwasser.",
    "Allgemeinstrom": "Strom für Flur, Keller und Außenbeleuchtung.",
    "Schornsteinfeger": "Kehr- und Messgebühren.",
    "Straßenreinigung und Winterdienst": "Gebühr oder Rechnung des Dienstleisters.",
    "Heizungswartung": "Die jährliche Wartung der Anlage.",
}


@dataclass
class Punkt:
    """Ein fehlender oder auffälliger Posten mit dem Ort zum Nachtragen."""

    was: str
    bereich: str
    warum: str = ""


@dataclass
class Bericht:
    pflicht: list[Punkt] = field(default_factory=list)
    kann: list[Punkt] = field(default_factory=list)
    achtung: list[Punkt] = field(default_factory=list)

    @property
    def vollstaendig(self) -> bool:
        return not self.pflicht


def _benutzte_schluessel(positionen: list[Position]) -> set[str]:
    return {p.schluessel for p in positionen if p.aktiv and p.betrag}


def pruefe(s: Stammdaten, positionen: list[Position], e: Ergebnis,
           vorjahr: list[Position] | None = None) -> Bericht:
    bericht = Bericht()
    schluessel = _benutzte_schluessel(positionen)

    # --- Pflicht ---------------------------------------------------------
    if not s.vermieter_name.strip():
        bericht.pflicht.append(Punkt("Dein Name", "vermieter", "steht im Briefkopf der Abrechnung"))
    if not s.vermieter_plz_ort.strip():
        bericht.pflicht.append(Punkt("Deine Anschrift", "vermieter", "gehört in den Briefkopf"))
    if not s.mieter_name.strip():
        bericht.pflicht.append(Punkt("Name des Mieters", "mieter", "die Abrechnung ist an ihn gerichtet"))
    if not s.objekt_strasse.strip():
        bericht.pflicht.append(Punkt("Adresse des Hauses", "vermieter", "muss auf der Abrechnung stehen"))

    if "flaeche" in schluessel or any(p.grundkosten_anteil for p in positionen if p.aktiv):
        if s.flaeche_gesamt <= 0:
            bericht.pflicht.append(Punkt("Wohnfläche des ganzen Hauses", "vermieter",
                                         "danach werden die meisten Kosten verteilt"))
        if s.flaeche_mieter <= 0:
            bericht.pflicht.append(Punkt("Wohnfläche der Mietwohnung", "objekt",
                                         "ohne sie lässt sich kein Anteil ausrechnen"))
    if "personen" in schluessel and s.personen_gesamt <= 0:
        bericht.pflicht.append(Punkt("Personen im Haus", "vermieter",
                                     "eine Kostenart wird nach Personenzahl verteilt"))

    if not any(p.aktiv and p.betrag for p in positionen):
        bericht.pflicht.append(Punkt("Mindestens eine Kostenart mit Betrag", "kosten",
                                     "sonst gibt es nichts abzurechnen"))

    for fehler in e.fehler:
        bericht.pflicht.append(Punkt(fehler, "zaehler" if "Zähler" in fehler else "kosten"))

    # --- Kann ------------------------------------------------------------
    if e.ist_nachzahlung and e.betrag_absolut >= 0.01 and not s.vermieter_iban.strip():
        bericht.kann.append(Punkt("Deine IBAN", "vermieter",
                                  "dein Mieter muss nachzahlen und braucht ein Konto"))
    if e.vorauszahlungen <= 0 and not s.ist_zwischenabrechnung:
        bericht.kann.append(Punkt("Vorauszahlungen des Mieters", "vz",
                                  "ohne sie wird der ganze Betrag nachgefordert"))

    for pos in positionen:
        if pos.aktiv and not pos.betrag and pos.schluessel != "direkt_vermieter":
            bericht.kann.append(Punkt(f"Betrag für „{pos.bezeichnung}“", "kosten",
                                      "die Zeile ist angehakt, aber ohne Betrag"))

    vorhanden = {p.bezeichnung: p for p in positionen}
    for name, warum in UEBLICH.items():
        pos = vorhanden.get(name)
        if pos is None or (not pos.aktiv):
            bericht.kann.append(Punkt(f"„{name}“ ist nicht dabei", "kosten", warum))

    # Vergleich mit der letzten Abrechnung: was damals drin war und jetzt fehlt
    if vorjahr:
        for alt in vorjahr:
            if not (alt.aktiv and alt.betrag):
                continue
            jetzt = vorhanden.get(alt.bezeichnung)
            if jetzt is None or not jetzt.aktiv or not jetzt.betrag:
                bericht.kann.append(Punkt(
                    f"„{alt.bezeichnung}“ fehlt gegenüber der letzten Abrechnung", "kosten",
                    f"damals {eur(alt.betrag)} €"))

    # --- Achtung ---------------------------------------------------------
    for pos in positionen:
        if not pos.aktiv or not pos.betrag:
            continue
        name = pos.bezeichnung.lower()
        if any(wort in name for wort in NICHT_UMLAGEFAEHIG_STICHWORTE):
            bericht.achtung.append(Punkt(
                f"„{pos.bezeichnung}“ gehört vermutlich nicht in die Abrechnung", "kosten",
                "Reparatur, Renovierung, Instandhaltung und Verwaltung trägt der Vermieter"))

    # doppelte Meldungen entfernen, Reihenfolge behalten
    for liste in (bericht.pflicht, bericht.kann, bericht.achtung):
        gesehen: set[str] = set()
        liste[:] = [p for p in liste if not (p.was in gesehen or gesehen.add(p.was))]
    return bericht
