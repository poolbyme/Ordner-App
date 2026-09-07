"""Erzeugt die Nebenkostenabrechnung als PDF (fpdf2)."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.fonts import FontFace

from .berechnung import Ergebnis, eur, menge, parse_datum, zahl
from .modell import Stammdaten

# Falls eine Unicode-Schrift verfügbar ist, wird sie benutzt (echtes €-Zeichen).
# Sonst greift die eingebaute Helvetica, die nur Latin-1 kann.
_FONT_KANDIDATEN = [
    (Path(__file__).parent / "fonts" / "DejaVuSans.ttf",
     Path(__file__).parent / "fonts" / "DejaVuSans-Bold.ttf"),
    (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
     Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
    (Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
     Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf")),
]

_ERSATZ = {
    "€": "EUR", "–": "-", "—": "-", "„": '"', "“": '"', "”": '"',
    "‚": "'", "‘": "'", "’": "'", "…": "...", "≈": "ca. ", "·": "-",
}

GRAU = (245, 246, 248)
LINIE = (170, 175, 185)


def _fmt_datum(wert: str | date | None) -> str:
    d = wert if isinstance(wert, date) else parse_datum(str(wert or ""))
    return d.strftime("%d.%m.%Y") if d else "—"


class Abrechnung(FPDF):
    def __init__(self, stammdaten: Stammdaten):
        super().__init__(format="A4", unit="mm")
        self.s = stammdaten
        self.set_margins(20, 15, 20)
        self.set_auto_page_break(True, margin=20)
        self.unicode = False
        self.font_family = "helvetica"
        for regular, bold in _FONT_KANDIDATEN:
            if regular.exists() and bold.exists():
                self.add_font("body", "", str(regular))
                self.add_font("body", "B", str(bold))
                self.font_family = "body"
                self.unicode = True
                break
        self.abschnitt = 0
        self.set_title("Betriebskostenabrechnung")

    # --- Hilfen -----------------------------------------------------------
    def t(self, text: str) -> str:
        """Text für die aktive Schrift aufbereiten."""
        if self.unicode:
            return text
        for alt, neu in _ERSATZ.items():
            text = text.replace(alt, neu)
        return text.encode("latin-1", "replace").decode("latin-1")

    def geld(self, betrag: float) -> str:
        return f"{eur(betrag)} {'€' if self.unicode else 'EUR'}"

    def font(self, size: float = 10, bold: bool = False) -> None:
        self.set_font(self.font_family, "B" if bold else "", size)

    def zeile(self, text: str, size: float = 10, bold: bool = False,
              h: float = 5.0, align: str = "L") -> None:
        self.font(size, bold)
        self.multi_cell(0, h, self.t(text), align=align,
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def abstand(self, h: float = 3.0) -> None:
        self.ln(h)

    def abschnitt_ueberschrift(self, text: str, platzbedarf: float = 32.0) -> None:
        self.abschnitt += 1
        self.ueberschrift(f"{self.abschnitt}. {text}", platzbedarf)

    def ueberschrift(self, text: str, platzbedarf: float = 32.0) -> None:
        # Keine Überschrift am Seitenfuß stehen lassen
        if self.get_y() + platzbedarf > self.h - self.b_margin:
            self.add_page()
        self.abstand(4)
        self.zeile(text, size=11, bold=True, h=6)
        self.set_draw_color(*LINIE)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.abstand(2)

    def betragszeile(self, beschriftung: str, betrag: float, bold: bool = False,
                     vorzeichen: bool = False) -> None:
        self.font(10, bold)
        wert = self.geld(betrag)
        if vorzeichen and betrag > 0:
            wert = "- " + wert
        breite = self.w - self.l_margin - self.r_margin
        self.cell(breite - 40, 6, self.t(beschriftung), align="L")
        self.cell(40, 6, self.t(wert), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def footer(self) -> None:
        self.set_y(-15)
        self.font(8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, self.t(f"Seite {self.page_no()} von {{nb}}"), align="C")
        self.set_text_color(0, 0, 0)


def _kopf(pdf: Abrechnung) -> None:
    s = pdf.s
    absender = " · ".join(x for x in [s.vermieter_name, s.vermieter_strasse, s.vermieter_plz_ort] if x)
    pdf.font(8)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 4, pdf.t(absender), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.set_draw_color(*LINIE)
    pdf.line(pdf.l_margin, pdf.get_y() + 0.5, pdf.l_margin + 85, pdf.get_y() + 0.5)
    pdf.abstand(4)

    empfaenger = [s.mieter_name, s.mieter_wohnung, s.objekt_strasse, s.objekt_plz_ort]
    pdf.font(11)
    for teil in [x for x in empfaenger if x]:
        pdf.cell(0, 5.5, pdf.t(teil), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.abstand(6)
    pdf.font(10)
    ort = s.ort or s.vermieter_plz_ort.split(" ", 1)[-1]
    pdf.cell(0, 5, pdf.t(f"{ort}, den {_fmt_datum(s.datum)}".lstrip(", ")),
             align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.abstand(4)

    pdf.zeile("Betriebskostenabrechnung (Nebenkostenabrechnung)", size=14, bold=True, h=8)
    pdf.zeile(f"{s.bezeichnung_abrechnung} für den Zeitraum "
              f"{_fmt_datum(s.zeitraum_von)} bis {_fmt_datum(s.zeitraum_bis)}", size=10)
    pdf.abstand(3)
    if s.anrede:
        pdf.zeile(s.anrede, size=10.5)
        pdf.abstand(1)
    if s.ist_endabrechnung:
        ende = f" zum {_fmt_datum(s.auszug_am)}" if s.auszug_am else ""
        pdf.zeile(f"mit dem Ende des Mietverhältnisses{ende} rechne ich die Betriebskosten "
                  "für den oben genannten Zeitraum abschließend ab.", size=10.5)
        pdf.abstand(1)
    elif s.ist_zwischenabrechnung:
        anlass = f" Anlass: {s.anlass}." if s.anlass else ""
        pdf.zeile("diese Zwischenabrechnung zeigt den Stand der Betriebskosten für den oben "
                  f"genannten Zeitraum.{anlass} Sie dient der Information und ersetzt nicht "
                  "die Abrechnung nach Ablauf des Abrechnungszeitraums.", size=10.5)
        pdf.abstand(1)


def _objektdaten(pdf: Abrechnung, e: Ergebnis) -> None:
    s = pdf.s
    zeilen = [
        ("Mietobjekt", ", ".join(x for x in [s.objekt_strasse, s.objekt_plz_ort] if x) or "—"),
        ("Wohneinheit", s.mieter_wohnung or "—"),
        ("Mieter", s.mieter_name or "—"),
        ("Nutzungszeitraum", f"{_fmt_datum(s.nutzung_von or s.zeitraum_von)} bis "
                             f"{_fmt_datum(s.nutzung_bis or s.zeitraum_bis)} "
                             f"({e.tage_nutzung} von {e.tage_zeitraum} Tagen)"),
        ("Wohnfläche", f"{zahl(s.flaeche_mieter)} m² von {zahl(s.flaeche_gesamt)} m² Gesamtwohnfläche"),
    ]
    if s.grundstuecksflaeche:
        zeilen.append(("Grundstück", f"{zahl(s.grundstuecksflaeche)} m²"))
    if s.personen_gesamt:
        zeilen.append(("Personen im Haus",
                       f"{zahl(s.personen_mieter, 0)} von {zahl(s.personen_gesamt, 0)}"))
    if s.ist_endabrechnung and s.auszug_am:
        zeilen.append(("Mietende", _fmt_datum(s.auszug_am)))

    pdf.font(9.5)
    for name, wert in zeilen:
        pdf.set_text_color(90, 90, 90)
        pdf.cell(38, 5, pdf.t(name))
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 5, pdf.t(wert), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _kostentabelle(pdf: Abrechnung, e: Ergebnis) -> None:
    pdf.abschnitt_ueberschrift("Zusammenstellung der Gesamtkosten und Verteilung")
    waehrung = "€" if pdf.unicode else "EUR"
    pdf.font(8.5)
    kopf = FontFace(emphasis="BOLD", fill_color=GRAU, size_pt=8)
    with pdf.table(
        col_widths=(48, 29, 59, 34),
        text_align=("LEFT", "RIGHT", "LEFT", "RIGHT"),
        headings_style=kopf,
        line_height=4.4,
        padding=(1.3, 1.6, 1.3, 1.6),
        borders_layout="HORIZONTAL_LINES",
    ) as tabelle:
        kopfzeile = tabelle.row()
        for titel in ("Kostenart", f"Gesamtkosten\n({waehrung})", "Verteilerschlüssel",
                      f"Anteil Mieter\n({waehrung})"):
            kopfzeile.cell(pdf.t(titel))
        for z in e.zeilen:
            reihe = tabelle.row()
            reihe.cell(pdf.t(z.bezeichnung))
            reihe.cell(eur(z.gesamtkosten))
            reihe.cell(pdf.t(z.schluessel_text))
            reihe.cell(eur(z.anteil))
        summe = tabelle.row(style=FontFace(emphasis="BOLD"))
        summe.cell(pdf.t("Summe"))
        summe.cell(eur(e.summe_gesamtkosten))
        summe.cell("")
        summe.cell(eur(e.summe_anteil))


PARTEI_KURZ = {"haus": "Haus gesamt", "mieter": "Mieter", "vermieter": "Vermieter"}


def _zaehlerstaende(pdf: Abrechnung, e: Ergebnis) -> None:
    eigene = [z for z in e.zeilen if z.zaehler and z.zaehler.messungen and not z.zaehler.quelle]
    geliehen = [z for z in e.zeilen if z.zaehler and z.zaehler.quelle]
    if not eigene and not geliehen:
        return
    pdf.abschnitt_ueberschrift("Zählerstände")
    breite = pdf.w - pdf.l_margin - pdf.r_margin

    def messzeile(name: str, partei: str, alt: float, neu: float, verbrauch: float,
                  einheit: str) -> None:
        pdf.font(9)
        namensbreite = breite - 110
        text = pdf.t(name)
        # Lange Zählernamen kleiner setzen, damit sie die Spalte nicht überlaufen
        for groesse in (9, 8.5, 8, 7.5, 7):
            pdf.font(groesse)
            if pdf.get_string_width(text) <= namensbreite - 1:
                break
        else:
            while text and pdf.get_string_width(text + "...") > namensbreite - 1:
                text = text[:-1]
            text += "..."
        pdf.cell(namensbreite, 5, text)
        pdf.font(9)
        pdf.set_text_color(90, 90, 90)
        pdf.cell(30, 5, pdf.t(partei))
        pdf.set_text_color(0, 0, 0)
        pdf.cell(25, 5, pdf.t(menge(alt)), align="R")
        pdf.cell(25, 5, pdf.t(menge(neu)), align="R")
        pdf.cell(30, 5, pdf.t(f"{menge(verbrauch)} {einheit}".strip()), align="R",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def summenzeile(name: str, wert: str, bold: bool = False) -> None:
        pdf.font(9, bold)
        pdf.cell(breite - 30, 5, pdf.t(name))
        pdf.cell(30, 5, pdf.t(wert), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    for zeile in eigene:
        zae = zeile.zaehler
        einheit = zae.einheit
        nur_unterzaehler = zae.grundlage == "unterzaehler"
        platz = 12 + 5 * (len(zae.messungen) + (4 if zae.mit_differenz else 1))
        if pdf.get_y() + min(platz, 60) > pdf.h - pdf.b_margin:
            pdf.add_page()
        pdf.abstand(2)

        pdf.font(9.5, bold=True)
        pdf.cell(breite - 80, 5.5, pdf.t(zeile.bezeichnung))
        pdf.set_text_color(90, 90, 90)
        pdf.font(8)
        pdf.cell(25, 5.5, pdf.t("Anfang"), align="R")
        pdf.cell(25, 5.5, pdf.t("Ende"), align="R")
        pdf.cell(30, 5.5, pdf.t("Verbrauch"), align="R",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        pdf.set_draw_color(*LINIE)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())

        for m in zae.messungen:
            partei = PARTEI_KURZ.get(m.partei, m.partei)
            zeileneinheit = einheit
            if nur_unterzaehler and m.partei == "haus":
                partei, zeileneinheit = "nachrichtlich", ""
            messzeile(m.name or "Zähler", partei, m.alt, m.neu, m.verbrauch, zeileneinheit)

        if zae.mit_differenz:
            summenzeile("Summe der Wohnungszähler",
                        f"{menge(zae.gemessen)} {einheit}".strip())
            summenzeile("nicht durch Wohnungszähler erfasste Differenz",
                        f"{menge(zae.differenz)} {einheit}".strip())
            summenzeile(f"davon auf den Mieter entfallend ({zae.differenz_text})",
                        f"{menge(zae.differenz_mieter)} {einheit}".strip())
        elif nur_unterzaehler:
            summenzeile("Summe der Unterzähler", f"{menge(zae.basis)} {einheit}".strip())

        summenzeile(f"angerechnet für die Mietwohnung – {zahl(zae.quote * 100)} % von "
                    f"{menge(zae.basis)} {einheit}".strip(),
                    f"{menge(zae.menge_mieter)} {einheit}".strip(), bold=True)
        pdf.abstand(1)

    if geliehen:
        pdf.abstand(2)
        pdf.font(9)
        for zeile in geliehen:
            pdf.multi_cell(0, 4.6, pdf.t(f"{zeile.bezeichnung}: abgerechnet nach den "
                                         f"Zählerständen von „{zeile.zaehler.quelle}“."),
                           align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _abrechnung(pdf: Abrechnung, e: Ergebnis) -> None:
    s = pdf.s
    pdf.abschnitt_ueberschrift("Abrechnung")
    pdf.betragszeile("Auf den Mieter entfallende Betriebskosten", e.summe_anteil)
    if e.co2_abzug > 0:
        pdf.betragszeile("abzüglich CO2-Kostenanteil des Vermieters (CO2KostAufG)",
                         e.co2_abzug, vorzeichen=True)
        pdf.betragszeile("umlagefähige Kosten", e.umlage)
    vz_text = "abzüglich geleisteter Vorauszahlungen"
    if s.vorauszahlung_manuell is None and s.vorauszahlung_monatlich:
        vz_text += (f" ({s.vorauszahlung_monate} × {eur(s.vorauszahlung_monatlich)}"
                    f" {'€' if pdf.unicode else 'EUR'})")
    pdf.betragszeile(vz_text, e.vorauszahlungen, vorzeichen=True)

    pdf.abstand(1)
    y = pdf.get_y()
    breite = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_fill_color(*GRAU)
    pdf.rect(pdf.l_margin, y, breite, 10, style="F")
    pdf.set_xy(pdf.l_margin + 2, y + 2)
    pdf.font(11.5, bold=True)
    if s.ist_zwischenabrechnung:
        titel = ("bisher nicht gedeckte Kosten" if e.ist_nachzahlung
                 else "bisher zu viel gezahlt")
    else:
        titel = "Nachzahlung des Mieters" if e.ist_nachzahlung else "Guthaben des Mieters"
    if abs(e.saldo) < 0.005:
        titel = "Ergebnis: ausgeglichen"
    pdf.cell(breite - 44, 6, pdf.t(titel), align="L")
    pdf.cell(40, 6, pdf.t(pdf.geld(e.betrag_absolut)), align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_y(y + 12)

    faellig = None
    d = parse_datum(s.datum)
    if d and s.zahlungsfrist_tage:
        faellig = d + timedelta(days=int(s.zahlungsfrist_tage))

    if s.ist_zwischenabrechnung:
        _zwischenstand(pdf, e)
        return

    if e.ist_nachzahlung and e.betrag_absolut >= 0.01:
        konto = ""
        if s.vermieter_iban:
            konto = f" auf das Konto IBAN {s.vermieter_iban}" + (f" ({s.vermieter_bank})" if s.vermieter_bank else "")
        frist = f" bis zum {_fmt_datum(faellig)}" if faellig else ""
        pdf.zeile(f"Bitte überweisen Sie den Nachzahlungsbetrag{frist}{konto}.", size=10)
    elif e.betrag_absolut >= 0.01:
        frist = f" bis zum {_fmt_datum(faellig)}" if faellig else " zeitnah"
        pdf.zeile(f"Das Guthaben wird Ihnen{frist} auf Ihr bekanntes Konto überwiesen.", size=10)

    if s.anpassung_vorschlagen and e.empfehlung_vorauszahlung > 0 and not s.ist_endabrechnung:
        alt = s.vorauszahlung_monatlich
        neu = e.empfehlung_vorauszahlung
        if not alt or abs(neu - alt) >= 5:
            pdf.abstand(1)
            w = "€" if pdf.unicode else "EUR"
            bisher = f" (bisher {eur(alt)} {w})" if alt else ""
            pdf.zeile(
                f"Nach § 560 Abs. 4 BGB wird die monatliche Vorauszahlung auf die Betriebskosten "
                f"ab dem übernächsten Monat auf {eur(neu)} {w}{bisher} angepasst.", size=10)


def _zwischenstand(pdf: Abrechnung, e: Ergebnis) -> None:
    """Was bei einer Zwischenabrechnung statt der Zahlungsaufforderung steht."""
    w = "€" if pdf.unicode else "EUR"
    pdf.zeile("Aus dieser Zwischenabrechnung ergibt sich noch keine Nachzahlung und kein "
              "Guthaben. Verbindlich abgerechnet wird nach Ablauf des Abrechnungszeitraums.",
              size=10)
    if e.hochrechnung_jahr > 0 and e.tage_nutzung < 360:
        pdf.abstand(1)
        pdf.betragszeile("auf zwölf Monate hochgerechnete Kosten", e.hochrechnung_jahr)
        if e.empfehlung_vorauszahlung > 0:
            pdf.betragszeile("das wären monatlich", round(e.hochrechnung_jahr / 12, 2))
    if e.empfehlung_vorauszahlung > 0:
        pdf.abstand(1)
        pdf.zeile(f"Rechnerisch angemessen wäre nach diesem Zwischenstand eine monatliche "
                  f"Vorauszahlung von {eur(e.empfehlung_vorauszahlung)} {w}. Eine Anpassung "
                  "der Vorauszahlungen ist erst nach der nächsten regulären Abrechnung "
                  "möglich.", size=10)


def _erlaeuterungen(pdf: Abrechnung, e: Ergebnis) -> None:
    s = pdf.s
    pdf.abschnitt_ueberschrift("Erläuterungen")
    punkte = [
        "Die Umlage erfolgt auf Grundlage des Mietvertrags und der Betriebskostenverordnung "
        "(§ 2 BetrKV). Nicht umlagefähige Kosten (Instandhaltung, Reparaturen, Verwaltung) "
        "sind in dieser Abrechnung nicht enthalten.",
    ]
    if s.flaeche_gesamt:
        punkte.append(
            f"Flächenschlüssel: {zahl(s.flaeche_mieter)} m² Wohnfläche der Mietwohnung zu "
            f"{zahl(s.flaeche_gesamt)} m² Gesamtwohnfläche des Gebäudes."
        )
    if any("Personen" in z.schluessel_text for z in e.zeilen) and s.personen_gesamt:
        punkte.append(
            f"Personenschlüssel: {zahl(s.personen_mieter, 0)} Personen der Mietwohnung zu "
            f"{zahl(s.personen_gesamt, 0)} Personen im Gebäude."
        )
    if any("Verbrauch" in z.schluessel_text or "Zähler" in z.schluessel_text for z in e.zeilen):
        punkte.append("Verbrauchsabhängige Positionen wurden nach den abgelesenen Zählerständen verteilt.")
    if any(z.zaehler and z.zaehler.mit_differenz for z in e.zeilen):
        punkte.append(
            "Der Hauptzähler des Hauses weist regelmäßig einen höheren Verbrauch aus als die "
            "Wohnungszähler zusammen (Messtoleranzen, Außenzapfstellen, Leitungsverluste). "
            "Diese Differenz wurde nicht einseitig angelastet, sondern auf beide Wohnungen "
            "verteilt; der Maßstab ist oben bei den Zählerständen angegeben.")
    if e.tage_nutzung and e.tage_zeitraum and e.tage_nutzung < e.tage_zeitraum:
        punkte.append(
            f"Das Mietverhältnis bestand {e.tage_nutzung} von {e.tage_zeitraum} Tagen des "
            "Abrechnungszeitraums; die nicht verbrauchsabhängigen Kosten wurden zeitanteilig umgelegt."
        )
    if e.arbeitskosten_mieter > 0:
        punkte.append(
            f"In den umgelegten Kosten sind anteilige Lohn- und Arbeitskosten für haushaltsnahe "
            f"Dienstleistungen und Handwerkerleistungen in Höhe von {eur(e.arbeitskosten_mieter)} "
            f"{'€' if pdf.unicode else 'EUR'} enthalten. Diese Bescheinigung kann für die "
            "Steuererklärung nach § 35a EStG verwendet werden."
        )
    if s.ist_zwischenabrechnung:
        punkte.append(
            "Die Belege können nach vorheriger Terminabsprache eingesehen werden. Diese "
            "Zwischenabrechnung ist keine Abrechnung im Sinne des § 556 Abs. 3 BGB; Fristen "
            "für Nachforderungen und Einwendungen laufen erst mit der regulären Abrechnung."
        )
    else:
        punkte.append(
            "Die Belege können nach vorheriger Terminabsprache eingesehen werden. Einwendungen "
            "gegen diese Abrechnung sind spätestens zwölf Monate nach ihrem Zugang mitzuteilen "
            "(§ 556 Abs. 3 S. 5 BGB)."
        )
    pdf.font(9.5)
    for punkt in punkte:
        pdf.multi_cell(0, 4.6, pdf.t(("•  " if pdf.unicode else "-  ") + punkt),
                       align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1.2)


def _unterschrift(pdf: Abrechnung) -> None:
    pdf.abstand(8)
    pdf.zeile("Mit freundlichen Grüßen", size=10)
    pdf.abstand(14)
    pdf.set_draw_color(*LINIE)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + 60, pdf.get_y())
    pdf.abstand(1)
    pdf.zeile(pdf.s.vermieter_name or "Vermieter", size=9)


def erzeuge_pdf(stammdaten: Stammdaten, ergebnis: Ergebnis) -> bytes:
    pdf = Abrechnung(stammdaten)
    pdf.add_page()
    _kopf(pdf)
    _objektdaten(pdf, ergebnis)
    _kostentabelle(pdf, ergebnis)
    _zaehlerstaende(pdf, ergebnis)
    _abrechnung(pdf, ergebnis)
    _erlaeuterungen(pdf, ergebnis)
    _unterschrift(pdf)
    return bytes(pdf.output())


def dateiname(stammdaten: Stammdaten) -> str:
    jahr = (parse_datum(stammdaten.zeitraum_bis) or date.today()).year
    name = "".join(c for c in stammdaten.mieter_name if c.isalnum() or c in " -_").strip()
    name = name.replace(" ", "_") or "Mieter"
    return f"Nebenkostenabrechnung_{jahr}_{name}.pdf"
