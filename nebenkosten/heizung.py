"""Heizung und Warmwasser: eine Rechnung, zwei Kostenarten.

Für Heizung und Warmwasser gibt es fast nie zwei Rechnungen. Es kommt **eine**
Rechnung des Versorgers, und die Heizkostenverordnung verlangt, daraus den
Warmwasseranteil herauszurechnen (§ 9 Abs. 2 HeizkostenV). Genau das macht
dieses Modul – der Vermieter trägt nur ein, was auf seinen Belegen steht.

Welche Angaben gebraucht werden, hängt an der Heizart: Bei Gas zählt der Zähler
Kubikmeter, die erst über Zustandszahl und Brennwert zu Kilowattstunden werden.
Bei Öl zählt der Tank Liter, bei Pellets die Waage Kilogramm, bei Fernwärme
steht die Kilowattstundenzahl schon auf der Rechnung.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Heizart:
    """Eine Art zu heizen und die Angaben, die sie braucht."""

    schluessel: str
    name: str
    mengenfeld: str = ""            # Beschriftung; leer = keine Menge nötig
    einheit: str = ""
    energie_je_einheit: float = 0.0  # kWh je Einheit; 0 = wird eigens berechnet
    energie_beschriftung: str = ""
    zentral: bool = True             # versorgt die Anlage das ganze Haus?
    macht_warmwasser: bool = True    # erzeugt sie auch das Warmwasser?
    gasumrechnung: bool = False      # Zustandszahl und Brennwert statt fester Zahl
    hinweis: str = ""
    zaehler: tuple[str, ...] = field(default_factory=tuple)


HEIZARTEN: dict[str, Heizart] = {
    "gas_zentral": Heizart(
        "gas_zentral", "Gas-Zentralheizung",
        mengenfeld="Gasverbrauch laut Zähler", einheit="m³",
        energie_beschriftung="kWh je m³ (Brennwert)", gasumrechnung=True,
        hinweis="Eine Therme oder ein Kessel im Haus versorgt alle Wohnungen. Der "
                "Gaszähler zählt Kubikmeter; Zustandszahl und Brennwert stehen auf "
                "der Gasrechnung.",
        zaehler=("Gaszähler Haus", "Wärmemengenzähler je Wohnung")),
    "oel": Heizart(
        "oel", "Ölheizung",
        mengenfeld="verbrauchtes Heizöl", einheit="l", energie_je_einheit=10.0,
        energie_beschriftung="kWh je Liter",
        hinweis="Abgerechnet wird der Verbrauch, nicht der Einkauf: Anfangsbestand "
                "plus Zukauf minus Endbestand. Ein Liter Heizöl hat rund 10 kWh.",
        zaehler=("Wärmemengenzähler je Wohnung",)),
    "pellets": Heizart(
        "pellets", "Pellets- oder Holzheizung",
        mengenfeld="verbrauchte Pellets", einheit="kg", energie_je_einheit=4.8,
        energie_beschriftung="kWh je kg",
        hinweis="Wie beim Öl zählt der Verbrauch, nicht der Einkauf. Ein Kilogramm "
                "Holzpellets hat rund 4,8 kWh.",
        zaehler=("Wärmemengenzähler je Wohnung",)),
    "fernwaerme": Heizart(
        "fernwaerme", "Fernwärme",
        mengenfeld="gelieferte Wärme", einheit="kWh", energie_je_einheit=1.0,
        energie_beschriftung="",
        hinweis="Die Kilowattstunden stehen schon auf der Rechnung des Versorgers – "
                "umrechnen musst du nichts.",
        zaehler=("Wärmemengenzähler je Wohnung",)),
    "waermepumpe": Heizart(
        "waermepumpe", "Wärmepumpe",
        mengenfeld="Strom für die Wärmepumpe", einheit="kWh", energie_je_einheit=1.0,
        energie_beschriftung="",
        hinweis="Gemeint ist der Strom, den die Wärmepumpe verbraucht hat – am besten "
                "über einen eigenen Zähler. Der Haushaltsstrom gehört nicht dazu.",
        zaehler=("Stromzähler der Wärmepumpe", "Wärmemengenzähler je Wohnung")),
    "gas_etage": Heizart(
        "gas_etage", "Etagenheizung (jede Wohnung eigener Vertrag)",
        macht_warmwasser=False, zentral=False,
        hinweis="Jede Wohnung hat ihre eigene Therme und ihren eigenen Vertrag mit dem "
                "Versorger. Dann rechnet der Mieter direkt mit dem Versorger ab – über "
                "die Nebenkosten läuft nur die Wartung.",
        zaehler=()),
    "keine": Heizart(
        "keine", "keine Heizkosten in dieser Abrechnung",
        macht_warmwasser=False, zentral=False,
        hinweis="Zum Beispiel, weil der Mieter selbst mit dem Versorger abrechnet."),
}

STANDARD = "gas_zentral"


def heizart(schluessel: str) -> Heizart:
    return HEIZARTEN.get(schluessel or STANDARD, HEIZARTEN[STANDARD])


def warmwasser_kwh(volumen: float, temperatur: float = 60.0) -> float:
    """Wärmemenge für die Warmwasserbereitung nach § 9 Abs. 2 HeizkostenV.

    Q = 2,5 × V × (tw − 10). V ist die Warmwassermenge in Kubikmetern, tw die
    Warmwassertemperatur in Grad Celsius; ohne Messung gilt tw = 60 °C.

    Die Verordnung schreibt genau diese Formel vor, ohne Zuschlag: Der Faktor
    2,5 deckt die Verluste der Anlage bereits ab – rechnerisch braucht ein
    Kubikmeter je Grad nur rund 1,16 kWh.
    """
    return max(0.0, 2.5 * volumen * (temperatur - 10.0))


@dataclass
class Aufteilung:
    """Ergebnis: Wie viel der Rechnung entfällt auf Heizung, wie viel auf Warmwasser."""

    art: Heizart
    energie_gesamt: float = 0.0     # kWh
    energie_warmwasser: float = 0.0  # kWh
    anteil_warmwasser: float = 0.0  # 0 bis 1
    kosten_heizung: float = 0.0
    kosten_warmwasser: float = 0.0
    rechenweg: list[str] = field(default_factory=list)
    hinweise: list[str] = field(default_factory=list)

    @property
    def vollstaendig(self) -> bool:
        return self.energie_gesamt > 0 or not self.art.zentral


def aufteilen(s, warmwassermenge: float) -> Aufteilung:
    """Die Brennstoffrechnung in Heizung und Warmwasser teilen.

    `s` sind die Stammdaten, `warmwassermenge` das im ganzen Haus verbrauchte
    Warmwasser in Kubikmetern – die Summe der Warmwasserzähler.
    """
    art = heizart(getattr(s, "heizart", STANDARD))
    a = Aufteilung(art=art)
    if not art.zentral:
        a.hinweise.append(
            "Für diese Heizart rechnet die App keine Brennstoffkosten ab: "
            + art.hinweis)
        return a

    kosten = max(0.0, float(getattr(s, "brennstoff_kosten", 0.0)))
    menge = max(0.0, float(getattr(s, "brennstoff_menge", 0.0)))

    if art.gasumrechnung:
        zustandszahl = float(getattr(s, "gas_zustandszahl", 0.0) or 0.0)
        brennwert = float(getattr(s, "gas_brennwert", 0.0) or 0.0)
        a.energie_gesamt = menge * zustandszahl * brennwert
        if a.energie_gesamt:
            a.rechenweg.append(
                f"{menge:.3f} m³ × {zustandszahl:.4f} (Zustandszahl) × "
                f"{brennwert:.4f} kWh/m³ (Brennwert) = {a.energie_gesamt:.0f} kWh")
    else:
        je = float(getattr(s, "energie_je_einheit", 0.0) or art.energie_je_einheit)
        a.energie_gesamt = menge * je
        if a.energie_gesamt and art.einheit != "kWh":
            a.rechenweg.append(
                f"{menge:.1f} {art.einheit} × {je:.2f} kWh/{art.einheit} "
                f"= {a.energie_gesamt:.0f} kWh")

    if a.energie_gesamt <= 0:
        a.kosten_heizung = kosten
        if kosten:
            a.hinweise.append(
                "Ohne Verbrauchsmenge lässt sich der Warmwasseranteil nicht "
                "herausrechnen – die ganze Rechnung steht bei der Heizung.")
        return a

    if not art.macht_warmwasser or not getattr(s, "warmwasser_zentral", True):
        a.kosten_heizung = kosten
        a.hinweise.append("Das Warmwasser wird nicht mit dieser Anlage erzeugt – "
                          "die Rechnung entfällt vollständig auf die Heizung.")
        return a

    temperatur = float(getattr(s, "warmwasser_temperatur", 60.0) or 60.0)
    a.energie_warmwasser = warmwasser_kwh(warmwassermenge, temperatur)
    if a.energie_warmwasser:
        a.rechenweg.append(
            f"2,5 × {warmwassermenge:.3f} m³ × ({temperatur:.0f} °C − 10) = "
            f"{a.energie_warmwasser:.0f} kWh für das Warmwasser (§ 9 Abs. 2 HeizkostenV)")

    a.anteil_warmwasser = min(a.energie_warmwasser / a.energie_gesamt, 1.0)
    a.kosten_warmwasser = round(kosten * a.anteil_warmwasser, 2)
    a.kosten_heizung = round(kosten - a.kosten_warmwasser, 2)
    if a.energie_warmwasser > a.energie_gesamt:
        a.hinweise.append(
            "Rechnerisch bräuchte das Warmwasser mehr Energie, als insgesamt "
            "verbraucht wurde. Bitte Warmwassermenge, Temperatur und Verbrauch prüfen.")
    elif not warmwassermenge:
        a.hinweise.append(
            "Ohne Warmwasserzähler lässt sich der Warmwasseranteil nicht bestimmen – "
            "die ganze Rechnung steht bei der Heizung.")
    return a
