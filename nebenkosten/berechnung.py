"""Umlage der Betriebskosten auf den Mieter."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta

from .modell import NICHT_UMLAGEFAEHIG_STICHWORTE, Position, Stammdaten


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
class Zaehler:
    """Abgelesene Zählerstände einer verbrauchsabhängigen Position."""

    einheit: str
    haus_alt: float
    haus_neu: float
    haus_verbrauch: float
    mieter_alt: float
    mieter_neu: float
    mieter_verbrauch: float
    eigen_alt: float = 0.0
    eigen_neu: float = 0.0
    eigen_verbrauch: float = 0.0
    differenz: float = 0.0            # Hauptzähler minus Summe der Wohnungszähler
    differenz_mieter: float = 0.0     # davon auf den Mieter verteilt
    differenz_text: str = ""
    menge_mieter: float = 0.0         # eigener Verbrauch + Anteil an der Differenz

    @property
    def mit_differenz(self) -> bool:
        return self.eigen_verbrauch > 0


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
    warnungen: list[str] = field(default_factory=list)
    fehler: list[str] = field(default_factory=list)

    @property
    def ist_nachzahlung(self) -> bool:
        return self.saldo > 0

    @property
    def betrag_absolut(self) -> float:
        return abs(self.saldo)


def verbrauchsaufteilung(pos: Position, s: Stammdaten) -> Zaehler:
    """Verteilt den Verbrauch einer Zählerposition auf Mieter und Vermieter.

    Der Hauptzähler zeigt fast immer mehr an als die Wohnungszähler zusammen
    (Messtoleranz, Gartenwasser, undichte Leitungen). Diese Differenz darf nicht
    allein dem Mieter angelastet werden; sie wird auf beide Wohnungen verteilt –
    ohne andere Vereinbarung nach Wohnfläche (§ 556a Abs. 1 S. 1 BGB).
    """
    haus = pos.verbrauch_haus
    mieter = pos.verbrauch_wohnung
    eigen = pos.verbrauch_eigen

    zaehler = Zaehler(
        einheit=pos.einheit or "",
        haus_alt=pos.zaehler_haus_alt, haus_neu=pos.zaehler_haus_neu, haus_verbrauch=haus,
        mieter_alt=pos.zaehler_mieter_alt, mieter_neu=pos.zaehler_mieter_neu,
        mieter_verbrauch=mieter,
        eigen_alt=pos.zaehler_eigen_alt, eigen_neu=pos.zaehler_eigen_neu,
        eigen_verbrauch=eigen,
        menge_mieter=mieter,
    )

    gemessen = mieter + eigen
    if eigen <= 0 or gemessen <= 0 or haus <= gemessen:
        # Ohne zweiten Wohnungszähler bleibt die Differenz beim Vermieter.
        return zaehler

    zaehler.differenz = round(haus - gemessen, 2)
    nach_flaeche = s.zaehlerdifferenz != "verbrauch" and s.flaeche_gesamt > 0
    if nach_flaeche:
        quote = s.flaeche_mieter / s.flaeche_gesamt
        zaehler.differenz_text = (f"nach Wohnfläche {zahl(s.flaeche_mieter)}/"
                                  f"{zahl(s.flaeche_gesamt)} m² = {zahl(quote * 100)} %")
    else:
        quote = mieter / gemessen
        zaehler.differenz_text = (f"nach gemessenem Verbrauch {menge(mieter)}/"
                                  f"{menge(gemessen)} = {zahl(quote * 100)} %")
    zaehler.differenz_mieter = round(zaehler.differenz * quote, 2)
    zaehler.menge_mieter = round(mieter + zaehler.differenz_mieter, 2)
    return zaehler


def _quote(pos: Position, s: Stammdaten) -> tuple[float, str, str | None]:
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
        haus = pos.verbrauch_haus
        if haus <= 0:
            return 0.0, "", (f"„{pos.bezeichnung}“: Der Verbrauch des Hauses fehlt – "
                             "bitte die Zählerstände eintragen.")
        einheit = pos.einheit or "Einheiten"
        aufteilung = verbrauchsaufteilung(pos, s)
        q = aufteilung.menge_mieter / haus
        if aufteilung.differenz > 0:
            text = (f"Zähler {menge(aufteilung.mieter_verbrauch)} + "
                    f"{menge(aufteilung.differenz_mieter)} Anteil an "
                    f"{menge(aufteilung.differenz)} {einheit} Differenz = "
                    f"{menge(aufteilung.menge_mieter)}/{menge(haus)} {einheit} "
                    f"= {zahl(q * 100)} %")
        else:
            text = (f"Verbrauch {menge(aufteilung.menge_mieter)}/{menge(haus)} {einheit} "
                    f"= {zahl(q * 100)} %")
        return q, text, None

    if pos.schluessel == "direkt":
        return 1.0, "direkt zugeordnet (100 %)", None

    return 0.0, "", f"Unbekannter Verteilerschlüssel „{pos.schluessel}“."


def berechne(s: Stammdaten, positionen: list[Position]) -> Ergebnis:
    e = Ergebnis()

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

        quote, text, fehler = _quote(pos, s)
        if fehler:
            e.fehler.append(fehler)

        # Beim Verbrauchsschlüssel steckt der Nutzungszeitraum bereits im
        # gemessenen Verbrauch – dann wird nicht zusätzlich zeitanteilig gekürzt.
        zeitfaktor = 1.0
        if pos.zeitanteilig and pos.schluessel != "verbrauch":
            zeitfaktor = zeitfaktor_basis
        if zeitfaktor < 1.0:
            text = f"{text}; Zeitanteil {e.tage_nutzung}/{e.tage_zeitraum} Tage"

        anteil = round(pos.betrag * quote * zeitfaktor, 2)
        arbeit = round(min(pos.arbeitskosten, pos.betrag) * quote * zeitfaktor, 2) if pos.arbeitskosten else 0.0

        e.zeilen.append(Zeile(
            bezeichnung=pos.bezeichnung.strip(),
            gesamtkosten=round(pos.betrag, 2),
            schluessel_text=text,
            quote=quote,
            zeitfaktor=zeitfaktor,
            anteil=anteil,
            arbeitskosten_anteil=arbeit,
            hinweis=pos.hinweis,
            zaehler=(verbrauchsaufteilung(pos, s)
                     if pos.schluessel == "verbrauch" and pos.hat_zaehlerstaende else None),
        ))

        if pos.schluessel == "verbrauch":
            if pos.zaehler_haus_neu and pos.zaehler_haus_neu < pos.zaehler_haus_alt:
                e.fehler.append(f"„{pos.bezeichnung}“: Der Endstand des Hauszählers ist "
                                "kleiner als der Anfangsstand.")
            if pos.zaehler_mieter_neu and pos.zaehler_mieter_neu < pos.zaehler_mieter_alt:
                e.fehler.append(f"„{pos.bezeichnung}“: Der Endstand des Wohnungszählers ist "
                                "kleiner als der Anfangsstand.")
            if (pos.verbrauch_eigen > 0 and pos.verbrauch_haus > 0
                    and pos.verbrauch_wohnung + pos.verbrauch_eigen > pos.verbrauch_haus + 0.001):
                e.warnungen.append(
                    f"„{pos.bezeichnung}“: Die beiden Wohnungszähler zeigen zusammen mehr an "
                    "als der Hauptzähler. Bitte die Stände prüfen – gerechnet wird mit dem "
                    "gemessenen Verbrauch der Mietwohnung.")
            if pos.zaehler_eigen_neu and pos.zaehler_eigen_neu < pos.zaehler_eigen_alt:
                e.fehler.append(f"„{pos.bezeichnung}“: Der Endstand deines eigenen Zählers ist "
                                "kleiner als der Anfangsstand.")
            if pos.verbrauch_haus > 0 and pos.verbrauch_wohnung > pos.verbrauch_haus:
                e.fehler.append(f"„{pos.bezeichnung}“: Die Wohnung verbraucht mehr als das "
                                "ganze Haus – bitte die Zählerstände prüfen.")
        if quote > 1.0001:
            e.fehler.append(f"„{pos.bezeichnung}“: Der Anteil des Mieters ist größer als 100 %.")
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

    _plausibilitaet(s, e, bis)
    return e


def _plausibilitaet(s: Stammdaten, e: Ergebnis, bis: date | None) -> None:
    if s.flaeche_gesamt and s.flaeche_mieter > s.flaeche_gesamt:
        e.fehler.append("Die Wohnfläche des Mieters ist größer als die Gesamtwohnfläche.")
    if s.personen_gesamt and s.personen_mieter > s.personen_gesamt:
        e.fehler.append("Es wohnen mehr Personen in der Mietwohnung als im ganzen Haus.")
    if s.einheiten_gesamt and s.einheiten_mieter > s.einheiten_gesamt:
        e.fehler.append("Der Mieter kann nicht mehr Wohneinheiten als das Haus haben.")

    if bis:
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

    if e.vorauszahlungen <= 0:
        e.warnungen.append("Es sind keine Vorauszahlungen erfasst – der gesamte Betrag wird nachgefordert.")

    if s.einheiten_gesamt and s.einheiten_gesamt > 2:
        e.warnungen.append(
            "Bei mehr als zwei Wohnungen greift die Ausnahme des § 2 HeizkostenV nicht: "
            "Heiz- und Warmwasserkosten müssen dann zu 50–70 % verbrauchsabhängig abgerechnet werden."
        )

    heiz_nach_flaeche = [z for z in e.zeilen
                         if ("heiz" in z.bezeichnung.lower() or "warmwasser" in z.bezeichnung.lower())
                         and "Wohnfläche" in z.schluessel_text]
    if heiz_nach_flaeche and s.einheiten_gesamt <= 2:
        e.warnungen.append(
            "Heiz-/Warmwasserkosten werden nach Fläche verteilt. Das ist im selbst bewohnten "
            "Zweifamilienhaus nach § 2 HeizkostenV zulässig – sofern der Mietvertrag nichts "
            "anderes vorschreibt."
        )
