"""Umlage der Betriebskosten auf den Mieter."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta

from .modell import (
    NICHT_UMLAGEFAEHIG_STICHWORTE, Position, Stammdaten, sicht_vermieter,
)


def parse_datum(wert: str) -> date | None:
    try:
        return date.fromisoformat(str(wert))
    except (TypeError, ValueError):
        return None


def tage(von: date | None, bis: date | None) -> int:
    """Kalendertage inklusive beider Grenzen."""
    if not von or not bis or bis < von:
        return 0
    return (bis - von).days + 1


def eur(betrag: float) -> str:
    """1234.5 -> '1.234,50'"""
    return f"{betrag:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")


def zahl(wert: float, nachkomma: int = 2) -> str:
    return f"{wert:,.{nachkomma}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def menge(wert: float) -> str:
    """Mengen ohne überflüssige Nullen: 88.0 -> '88', 12.345 -> '12,345'."""
    text = zahl(wert, 3)
    return text.rstrip("0").rstrip(",") if "," in text else text


@dataclass
class Messung:
    """Ein Zähler mit seinen Ständen – so, wie er im PDF erscheint."""

    name: str
    partei: str
    alt: float
    neu: float
    verbrauch: float


@dataclass
class Zaehler:
    """Wie sich der Verbrauch einer Position auf die Parteien verteilt."""

    einheit: str = ""
    messungen: list[Messung] = field(default_factory=list)
    quelle: str = ""                  # Position, von der die Zähler stammen
    grundlage: str = "hauptzaehler"
    haus_verbrauch: float = 0.0
    mieter_verbrauch: float = 0.0
    vermieter_verbrauch: float = 0.0
    gemeinsam_verbrauch: float = 0.0  # z. B. Außenzapfstelle, Garten
    gemeinsam_anteil: float = 0.0     # davon auf diese Partei entfallend
    gemessen: float = 0.0             # Mieter + Vermieter + gemeinsam
    basis: float = 0.0                # Nenner für den Anteil des Mieters
    differenz: float = 0.0            # Hauptzähler minus Unterzähler
    differenz_mieter: float = 0.0
    differenz_text: str = ""
    verteiltext: str = ""             # Maßstab für gemeinsame Menge und Differenz
    menge_mieter: float = 0.0

    @property
    def mit_differenz(self) -> bool:
        return self.differenz > 0

    @property
    def mit_gemeinsam(self) -> bool:
        return self.gemeinsam_verbrauch > 0

    @property
    def quote(self) -> float:
        return self.menge_mieter / self.basis if self.basis > 0 else 0.0


@dataclass
class Zeile:
    bezeichnung: str
    gesamtkosten: float
    schluessel_text: str
    quote: float
    zeitfaktor: float
    anteil: float
    arbeitskosten_anteil: float
    hinweis: str = ""
    zaehler: Zaehler | None = None


@dataclass
class Ergebnis:
    zeilen: list[Zeile] = field(default_factory=list)
    summe_gesamtkosten: float = 0.0
    summe_anteil: float = 0.0
    co2_abzug: float = 0.0
    umlage: float = 0.0            # Anteil Mieter nach CO2-Abzug
    vorauszahlungen: float = 0.0
    saldo: float = 0.0             # > 0 Nachzahlung, < 0 Guthaben
    arbeitskosten_mieter: float = 0.0
    tage_zeitraum: int = 0
    tage_nutzung: int = 0
    monate_nutzung: float = 0.0
    empfehlung_vorauszahlung: float = 0.0
    hochrechnung_jahr: float = 0.0    # Kosten des Mieters auf zwölf Monate gerechnet
    warnungen: list[str] = field(default_factory=list)
    fehler: list[str] = field(default_factory=list)
    fuer: str = "mieter"

    @property
    def fuer_vermieter(self) -> bool:
        return self.fuer == "vermieter"

    @property
    def ist_nachzahlung(self) -> bool:
        return self.saldo > 0

    @property
    def betrag_absolut(self) -> float:
        return abs(self.saldo)


def zaehlerquelle(pos: Position, positionen: list[Position] | None) -> Position:
    """Position, deren Zähler benutzt werden (z. B. Abwasser nutzt die von Wasser)."""
    if not pos.zaehler_von or not positionen:
        return pos
    gesucht = pos.zaehler_von.strip().lower()
    for anderer in positionen:
        if anderer is not pos and anderer.bezeichnung.strip().lower() == gesucht:
            return anderer
    return pos


def warmwasser_kwh(volumen: float, temperatur: float = 60.0,
                   nutzungsgrad: float = 1.11) -> float:
    """Wärmemenge für die Warmwasserbereitung nach § 9 Abs. 2 HeizkostenV.

    Q = 2,5 × V × (tw − 10), wobei V die Warmwassermenge in m³ und tw die
    Warmwassertemperatur in °C ist; ohne gemessene Temperatur gilt tw = 60 °C.
    Der Nutzungsgrad rechnet die Verluste der Anlage hinzu.
    """
    return max(0.0, 2.5 * volumen * (temperatur - 10.0) * nutzungsgrad)


# Stufenmodell des CO2-Kostenaufteilungsgesetzes für Wohngebäude (§ 5 CO2KostAufG):
# spezifische Emissionen in kg CO2 je m² Wohnfläche und Jahr -> Anteil des Vermieters
CO2_STUFEN = [(12, 0), (17, 10), (22, 20), (27, 30), (32, 40),
              (37, 50), (42, 60), (47, 70), (52, 80), (float("inf"), 95)]


def co2_vermieteranteil(kilogramm: float, wohnflaeche: float) -> tuple[float, str]:
    """Anteil des Vermieters an den CO2-Kosten in Prozent, dazu die Stufe im Klartext."""
    if kilogramm <= 0 or wohnflaeche <= 0:
        return 0.0, "keine Angaben zu den CO2-Emissionen"
    je_qm = kilogramm / wohnflaeche
    untere = 0
    for grenze, anteil in CO2_STUFEN:
        if je_qm < grenze:
            bereich = (f"{untere} bis unter {grenze} kg" if grenze != float("inf")
                       else "52 kg und mehr")
            return float(anteil), (f"{zahl(je_qm, 1)} kg CO2 je m² und Jahr "
                                   f"({bereich}) – Vermieteranteil {anteil} %")
        untere = grenze
    return 0.0, ""


def verbrauchsaufteilung(pos: Position, s: Stammdaten,
                         positionen: list[Position] | None = None,
                         fuer: str = "mieter") -> Zaehler:
    """Verteilt den gemessenen Verbrauch einer Position auf Mieter und Vermieter.

    Zwei Fälle:

    * **Anteil am Hauptzähler** – die Kosten hängen am Hauptzähler (Wasser).
      Der Hauptzähler zeigt fast immer mehr als die Unterzähler zusammen
      (Messtoleranz, Außenzapfstelle, undichte Leitungen). Diese Differenz wird
      auf beide Wohnungen verteilt, nicht einer Seite allein angelastet.
    * **Nur die Unterzähler** – die Zähler messen in einer anderen Einheit als
      die Rechnung (Wärmemengenzähler bei einer Gasrechnung). Dann zählt allein
      das Verhältnis der Unterzähler zueinander.
    """
    quelle = zaehlerquelle(pos, positionen)
    haus = quelle.verbrauch_haus
    # Aus Sicht der eigenen Wohnung tauschen die beiden Parteien die Rollen.
    if fuer == "vermieter":
        mieter, vermieter = quelle.verbrauch_eigen, quelle.verbrauch_wohnung
    else:
        mieter, vermieter = quelle.verbrauch_wohnung, quelle.verbrauch_eigen

    gemeinsam = quelle.verbrauch_gemeinsam

    zaehler = Zaehler(
        einheit=pos.einheit or quelle.einheit or "",
        messungen=[Messung(z.name, z.partei, z.alt, z.neu, z.verbrauch)
                   for z in quelle.zaehler if z.alt or z.neu],
        quelle="" if quelle is pos else quelle.bezeichnung,
        grundlage=pos.zaehler_grundlage,
        haus_verbrauch=haus,
        mieter_verbrauch=mieter,
        vermieter_verbrauch=vermieter,
        gemeinsam_verbrauch=gemeinsam,
        gemessen=round(mieter + vermieter + gemeinsam, 2),
        menge_mieter=mieter,
    )

    # Maßstab, nach dem gemeinsame Mengen und die Differenz geteilt werden
    eigen = mieter + vermieter
    nach_verbrauch = s.zaehlerdifferenz != "flaeche" or s.flaeche_gesamt <= 0
    if nach_verbrauch and eigen > 0:
        quote = mieter / eigen
        zaehler.verteiltext = (f"nach gemessenem Verbrauch {menge(mieter)}/"
                               f"{menge(eigen)} = {zahl(quote * 100)} %")
    elif s.flaeche_gesamt > 0:
        quote = s.flaeche_mieter / s.flaeche_gesamt
        zaehler.verteiltext = (f"nach Wohnfläche {zahl(s.flaeche_mieter)}/"
                               f"{zahl(s.flaeche_gesamt)} m² = {zahl(quote * 100)} %")
    else:
        quote = 0.0

    if gemeinsam > 0:
        zaehler.gemeinsam_anteil = round(gemeinsam * quote, 2)
        zaehler.menge_mieter = round(mieter + zaehler.gemeinsam_anteil, 2)

    nach_hauptzaehler = pos.zaehler_grundlage != "unterzaehler" and haus > 0
    if not nach_hauptzaehler:
        # Die Unterzähler stehen für sich; ein Hauptzähler ist nur Information.
        zaehler.basis = zaehler.gemessen
        return zaehler

    zaehler.basis = haus
    if vermieter <= 0 or zaehler.gemessen <= 0 or haus <= zaehler.gemessen:
        # Ohne Gegenzähler bleibt die Differenz beim Vermieter.
        return zaehler

    zaehler.differenz = round(haus - zaehler.gemessen, 2)
    zaehler.differenz_text = zaehler.verteiltext
    zaehler.differenz_mieter = round(zaehler.differenz * quote, 2)
    zaehler.menge_mieter = round(zaehler.menge_mieter + zaehler.differenz_mieter, 2)
    return zaehler


def _quote(pos: Position, s: Stammdaten, positionen: list[Position] | None = None,
           fuer: str = "mieter") -> tuple[float, str, str | None]:
    """Liefert (Quote, Erläuterungstext, Fehler)."""
    if pos.schluessel == "flaeche":
        if s.flaeche_gesamt <= 0:
            return 0.0, "", "Gesamtwohnfläche fehlt (wird für den Flächenschlüssel gebraucht)."
        q = s.flaeche_mieter / s.flaeche_gesamt
        return q, f"Wohnfläche {zahl(s.flaeche_mieter)}/{zahl(s.flaeche_gesamt)} m² = {zahl(q * 100)} %", None

    if pos.schluessel == "personen":
        if s.personen_gesamt <= 0:
            return 0.0, "", "Personenzahl im Haus fehlt (wird für den Personenschlüssel gebraucht)."
        q = s.personen_mieter / s.personen_gesamt
        return q, f"Personen {zahl(s.personen_mieter, 0)}/{zahl(s.personen_gesamt, 0)} = {zahl(q * 100)} %", None

    if pos.schluessel == "einheiten":
        if s.einheiten_gesamt <= 0:
            return 0.0, "", "Anzahl der Wohneinheiten fehlt."
        q = s.einheiten_mieter / s.einheiten_gesamt
        return q, f"Wohneinheiten {zahl(s.einheiten_mieter, 0)}/{zahl(s.einheiten_gesamt, 0)} = {zahl(q * 100)} %", None

    if pos.schluessel == "verbrauch":
        aufteilung = verbrauchsaufteilung(pos, s, positionen, fuer)
        if aufteilung.basis <= 0:
            return 0.0, "", (f"„{pos.bezeichnung}“: Es fehlen Zählerstände – ohne sie "
                             "lässt sich der Anteil nicht ausrechnen.")
        einheit = aufteilung.einheit or "Einheiten"
        q = aufteilung.quote
        if aufteilung.mit_differenz or aufteilung.mit_gemeinsam:
            zusatz = []
            if aufteilung.mit_gemeinsam:
                zusatz.append(f"{menge(aufteilung.gemeinsam_anteil)} Anteil an "
                              f"{menge(aufteilung.gemeinsam_verbrauch)} gemeinsam")
            if aufteilung.mit_differenz:
                zusatz.append(f"{menge(aufteilung.differenz_mieter)} Anteil an "
                              f"{menge(aufteilung.differenz)} Differenz")
            text = (f"Zähler {menge(aufteilung.mieter_verbrauch)} + " + " + ".join(zusatz) +
                    f" = {menge(aufteilung.menge_mieter)}/{menge(aufteilung.basis)} {einheit} "
                    f"= {zahl(q * 100)} %")
        else:
            text = (f"Verbrauch {menge(aufteilung.menge_mieter)}/"
                    f"{menge(aufteilung.basis)} {einheit} = {zahl(q * 100)} %")
        if aufteilung.quelle:
            text += f" (Zähler von „{aufteilung.quelle}“)"
        return q, text, None

    if pos.schluessel == "direkt":
        # Kosten, die allein der Mieter trägt – in der eigenen Aufstellung also nichts.
        if fuer == "vermieter":
            return 0.0, "trägt allein der Mieter", None
        return 1.0, "direkt zugeordnet (100 %)", None

    if pos.schluessel == "direkt_vermieter":
        if fuer == "vermieter":
            return 1.0, "direkt zugeordnet (100 %)", None
        return 0.0, "trägt allein der Vermieter", None

    return 0.0, "", f"Unbekannter Verteilerschlüssel „{pos.schluessel}“."


def berechne(s: Stammdaten, positionen: list[Position],
             fuer: str = "mieter") -> Ergebnis:
    """Abrechnung für den Mieter (Standard) oder für die eigene Wohnung."""
    if fuer == "vermieter":
        s = sicht_vermieter(s)
    e = Ergebnis()
    e.fuer = fuer

    von, bis = parse_datum(s.zeitraum_von), parse_datum(s.zeitraum_bis)
    n_von = parse_datum(s.nutzung_von) or von
    n_bis = parse_datum(s.nutzung_bis) or bis

    # Nutzungszeitraum auf den Abrechnungszeitraum begrenzen
    if von and n_von and n_von < von:
        n_von = von
    if bis and n_bis and n_bis > bis:
        n_bis = bis

    e.tage_zeitraum = tage(von, bis)
    e.tage_nutzung = tage(n_von, n_bis)

    if not von or not bis:
        e.fehler.append("Abrechnungszeitraum ist unvollständig.")
    elif bis < von:
        e.fehler.append("Das Ende des Abrechnungszeitraums liegt vor dem Beginn.")
    elif e.tage_zeitraum > 366:
        e.fehler.append("Der Abrechnungszeitraum darf höchstens 12 Monate umfassen (§ 556 Abs. 3 S. 1 BGB).")


    zeitfaktor_basis = (e.tage_nutzung / e.tage_zeitraum) if e.tage_zeitraum else 1.0
    zeitfaktor_basis = min(zeitfaktor_basis, 1.0) if zeitfaktor_basis else 1.0

    for pos in positionen:
        if not pos.aktiv:
            continue
        if not pos.bezeichnung.strip():
            continue
        if abs(pos.betrag) < 0.005 and pos.schluessel != "direkt":
            continue

        quote, text, fehler = _quote(pos, s, positionen, fuer)
        if fehler:
            e.fehler.append(fehler)

        # Beim Verbrauchsschlüssel steckt der Nutzungszeitraum bereits im
        # gemessenen Verbrauch – dann wird nicht zusätzlich zeitanteilig gekürzt.
        zeitfaktor = 1.0
        if pos.zeitanteilig and pos.schluessel != "verbrauch":
            zeitfaktor = zeitfaktor_basis
        if zeitfaktor < 1.0:
            text = f"{text}; Zeitanteil {e.tage_nutzung}/{e.tage_zeitraum} Tage"

        zaehler = (verbrauchsaufteilung(pos, s, positionen, fuer)
                   if pos.schluessel == "verbrauch" else None)

        # Heiz- und Warmwasserkosten werden oft geteilt: ein fester Anteil nach
        # Wohnfläche (Grundkosten), der Rest nach Verbrauch.
        grund = min(max(pos.grundkosten_anteil, 0.0), 50.0) / 100
        if grund > 0 and pos.schluessel == "verbrauch" and s.flaeche_gesamt > 0:
            flaechenquote = s.flaeche_mieter / s.flaeche_gesamt
            grundzeit = zeitfaktor_basis if pos.zeitanteilig else 1.0
            grundtext = (f"Wohnfläche {zahl(s.flaeche_mieter)}/{zahl(s.flaeche_gesamt)} m² "
                         f"= {zahl(flaechenquote * 100)} %")
            if grundzeit < 1.0:
                grundtext += f"; Zeitanteil {e.tage_nutzung}/{e.tage_zeitraum} Tage"
            e.zeilen.append(Zeile(
                bezeichnung=f"{pos.bezeichnung.strip()} – Grundkosten {zahl(grund * 100, 0)} %",
                gesamtkosten=round(pos.betrag * grund, 2),
                schluessel_text=grundtext,
                quote=flaechenquote,
                zeitfaktor=grundzeit,
                anteil=round(pos.betrag * grund * flaechenquote * grundzeit, 2),
                arbeitskosten_anteil=0.0,
                hinweis=pos.hinweis,
            ))
            bezeichnung = f"{pos.bezeichnung.strip()} – Verbrauchskosten {zahl(100 - grund * 100, 0)} %"
            restanteil = 1 - grund
        else:
            bezeichnung = pos.bezeichnung.strip()
            restanteil = 1.0

        anteil = round(pos.betrag * restanteil * quote * zeitfaktor, 2)
        arbeit = (round(min(pos.arbeitskosten, pos.betrag) * quote * zeitfaktor, 2)
                  if pos.arbeitskosten else 0.0)

        e.zeilen.append(Zeile(
            bezeichnung=bezeichnung,
            gesamtkosten=round(pos.betrag * restanteil, 2),
            schluessel_text=text,
            quote=quote,
            zeitfaktor=zeitfaktor,
            anteil=anteil,
            arbeitskosten_anteil=arbeit,
            hinweis=pos.hinweis,
            zaehler=zaehler,
        ))

        if pos.schluessel == "verbrauch":
            quelle = zaehlerquelle(pos, positionen)
            for zst in quelle.zaehler:
                if zst.neu and zst.neu < zst.alt:
                    e.fehler.append(
                        f"„{quelle.bezeichnung}“, Zähler „{zst.name or 'ohne Namen'}“: "
                        "Der Endstand ist kleiner als der Anfangsstand.")
            if (pos.zaehler_grundlage != "unterzaehler"
                    and quelle.verbrauch_haus > 0 and quelle.verbrauch_eigen > 0
                    and quelle.verbrauch_wohnung + quelle.verbrauch_eigen
                    > quelle.verbrauch_haus + 0.001):
                e.warnungen.append(
                    f"„{quelle.bezeichnung}“: Die Unterzähler zeigen zusammen mehr an als der "
                    "Hauptzähler. Bitte die Stände prüfen – gerechnet wird ohne Differenz.")
            # Ein angelegter, aber nicht abgelesener Zähler ist tückisch: seine Menge
            # rutscht in die Differenz und wird dadurch mitverteilt.
            if any(z.alt or z.neu for z in quelle.zaehler):
                for zst in quelle.zaehler:
                    if not zst.alt and not zst.neu and zst.name.strip():
                        e.warnungen.append(
                            f"„{quelle.bezeichnung}“: Für den Zähler „{zst.name}“ fehlen die "
                            "Stände. Sein Verbrauch landet sonst in der Differenz und wird "
                            "mitverteilt.")
            aufteilung = zaehler
            if (aufteilung and aufteilung.differenz > 0
                    and aufteilung.haus_verbrauch > 0
                    and aufteilung.differenz > 0.10 * aufteilung.haus_verbrauch):
                e.warnungen.append(
                    f"„{quelle.bezeichnung}“: Die Differenz zum Hauptzähler ist mit "
                    f"{zahl(aufteilung.differenz / aufteilung.haus_verbrauch * 100)} % "
                    "ungewöhnlich groß. Das kommt meist daher, dass eine Wohnung zeitweise "
                    "leer stand oder die Zähler zu verschiedenen Zeitpunkten abgelesen wurden. "
                    "Dann gehört die Differenz nicht anteilig auf den Mieter – prüfe die "
                    "Zeiträume oder stelle die Position auf „nur die Unterzähler“.")
            if (pos.zaehler_grundlage != "unterzaehler" and quelle.verbrauch_haus > 0
                    and quelle.verbrauch_wohnung > quelle.verbrauch_haus):
                e.fehler.append(f"„{pos.bezeichnung}“: Die Mietwohnung verbraucht mehr als der "
                                "Hauptzähler anzeigt – bitte die Zählerstände prüfen.")
            if pos.zaehler_von and zaehlerquelle(pos, positionen) is pos:
                e.warnungen.append(
                    f"„{pos.bezeichnung}“: Die Position „{pos.zaehler_von}“, deren Zähler "
                    "benutzt werden sollen, gibt es nicht (mehr).")
        if quote > 1.0001:
            e.fehler.append(f"„{pos.bezeichnung}“: Der berechnete Anteil ist größer als 100 %.")
        if any(w in pos.bezeichnung.lower() for w in NICHT_UMLAGEFAEHIG_STICHWORTE):
            e.warnungen.append(
                f"„{pos.bezeichnung}“ klingt nach nicht umlagefähigen Kosten "
                "(Instandhaltung, Reparatur, Verwaltung). Diese trägt der Vermieter."
            )

    e.summe_gesamtkosten = round(sum(z.gesamtkosten for z in e.zeilen), 2)
    e.summe_anteil = round(sum(z.anteil for z in e.zeilen), 2)
    e.arbeitskosten_mieter = round(sum(z.arbeitskosten_anteil for z in e.zeilen), 2)
    e.co2_abzug = round(max(0.0, s.co2_abzug), 2)
    e.umlage = round(e.summe_anteil - e.co2_abzug, 2)
    e.vorauszahlungen = round(s.vorauszahlung_gesamt, 2)
    e.saldo = round(e.umlage - e.vorauszahlungen, 2)

    e.monate_nutzung = (e.tage_nutzung / 365 * 12) if e.tage_nutzung else 0.0
    if e.monate_nutzung > 0:
        e.empfehlung_vorauszahlung = float(math.ceil(e.umlage / e.monate_nutzung))
        e.hochrechnung_jahr = round(e.umlage / e.tage_nutzung * 365, 2)

    _plausibilitaet(s, e, bis)
    e.fehler = list(dict.fromkeys(e.fehler))
    e.warnungen = list(dict.fromkeys(e.warnungen))
    return e


def _plausibilitaet(s: Stammdaten, e: Ergebnis, bis: date | None) -> None:
    if s.ist_zwischenabrechnung:
        e.warnungen.append(
            "Zwischenabrechnung: Sie zeigt nur den Stand und begründet noch keine "
            "Nachzahlung. Verbindlich wird erst die Abrechnung nach Ablauf des "
            "Abrechnungszeitraums (§ 556 Abs. 3 BGB).")
    if s.flaeche_gesamt and s.flaeche_mieter > s.flaeche_gesamt:
        e.fehler.append("Die Wohnfläche des Mieters ist größer als die Gesamtwohnfläche.")
    if s.personen_gesamt and s.personen_mieter > s.personen_gesamt:
        e.fehler.append("Es wohnen mehr Personen in der Mietwohnung als im ganzen Haus.")
    if s.einheiten_gesamt and s.einheiten_mieter > s.einheiten_gesamt:
        e.fehler.append("Der Mieter kann nicht mehr Wohneinheiten als das Haus haben.")

    if bis and not s.ist_zwischenabrechnung:
        frist = date(bis.year + 1, bis.month, bis.day) if (bis.month, bis.day) != (2, 29) \
            else date(bis.year + 1, 2, 28)
        if date.today() > frist:
            e.warnungen.append(
                f"Die Abrechnungsfrist ist am {frist.strftime('%d.%m.%Y')} abgelaufen. "
                "Eine Nachforderung ist nach § 556 Abs. 3 S. 3 BGB in der Regel ausgeschlossen; "
                "ein Guthaben muss trotzdem ausgezahlt werden."
            )
        elif date.today() > frist - timedelta(days=60):
            e.warnungen.append(
                f"Die Abrechnung muss dem Mieter bis zum {frist.strftime('%d.%m.%Y')} zugehen "
                "(§ 556 Abs. 3 S. 2 BGB)."
            )

    if e.vorauszahlungen <= 0 and not s.ist_zwischenabrechnung:
        e.warnungen.append("Es sind keine Vorauszahlungen erfasst – der gesamte Betrag wird nachgefordert.")

    if s.einheiten_gesamt and s.einheiten_gesamt > 2:
        e.warnungen.append(
            "Bei mehr als zwei Wohnungen greift die Ausnahme des § 2 HeizkostenV nicht: "
            "Heiz- und Warmwasserkosten müssen dann zu 50–70 % verbrauchsabhängig abgerechnet werden."
        )

    heiz_nach_flaeche = [z for z in e.zeilen
                         if ("heiz" in z.bezeichnung.lower()
                             or "warmwasser" in z.bezeichnung.lower())
                         and "Wohnfläche" in z.schluessel_text
                         and "Grundkosten" not in z.bezeichnung]
    if heiz_nach_flaeche and s.einheiten_gesamt <= 2:
        e.warnungen.append(
            "Heiz-/Warmwasserkosten werden nach Fläche verteilt. Das ist im selbst bewohnten "
            "Zweifamilienhaus nach § 2 HeizkostenV zulässig – sofern der Mietvertrag nichts "
            "anderes vorschreibt."
        )
