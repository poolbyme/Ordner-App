"""Tests für die Nebenkostenabrechnung: python -m pytest tests/ (oder direkt ausführen)."""

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nebenkosten.berechnung import berechne, eur, menge, tage  # noqa: E402
from nebenkosten.modell import (  # noqa: E402
    Position, Stammdaten, Zaehlerstand, as_dict, from_dict, standard_positionen,
)
from nebenkosten.pdf import dateiname, erzeuge_pdf  # noqa: E402


def basis_stammdaten(**abweichungen) -> Stammdaten:
    werte = dict(
        vermieter_name="Vermieter", mieter_name="Mieter",
        objekt_strasse="Musterweg 5", objekt_plz_ort="12345 Musterstadt",
        zeitraum_von="2025-01-01", zeitraum_bis="2025-12-31",
        nutzung_von="2025-01-01", nutzung_bis="2025-12-31",
        flaeche_gesamt=200.0, flaeche_mieter=80.0,
        personen_gesamt=4.0, personen_mieter=1.0,
        vorauszahlung_monatlich=100.0, vorauszahlung_monate=12,
        datum="2026-03-01",
    )
    werte.update(abweichungen)
    return Stammdaten(**werte)


def test_flaechenschluessel():
    e = berechne(basis_stammdaten(), [Position("Grundsteuer", betrag=1000.0)])
    assert e.summe_anteil == 400.0
    assert "Wohnfläche" in e.zeilen[0].schluessel_text


def test_personenschluessel():
    e = berechne(basis_stammdaten(), [Position("Müll", betrag=400.0, schluessel="personen")])
    assert e.summe_anteil == 100.0


def test_verbrauchsschluessel():
    pos = Position("Wasser", betrag=600.0, schluessel="verbrauch", einheit="m³", zaehler=[
        Zaehlerstand("Hauptzähler", "haus", 1000.0, 1200.0),
        Zaehlerstand("Mieter", "mieter", 100.0, 150.0),
    ])
    assert berechne(basis_stammdaten(), [pos]).summe_anteil == 150.0


def test_direkte_zuordnung():
    e = berechne(basis_stammdaten(), [Position("Eigener Zähler", betrag=88.5, schluessel="direkt")])
    assert e.summe_anteil == 88.5


def test_zeitanteilige_umlage():
    s = basis_stammdaten(nutzung_von="2025-07-01")  # 184 von 365 Tagen
    e = berechne(s, [Position("Grundsteuer", betrag=1000.0)])
    assert e.tage_nutzung == 184
    assert e.summe_anteil == round(1000 * 0.4 * 184 / 365, 2)


def test_verbrauch_wird_nicht_zusaetzlich_gekuerzt():
    """Der gemessene Verbrauch enthält den Nutzungszeitraum bereits."""
    s = basis_stammdaten(nutzung_von="2025-07-01")
    pos = Position("Wasser", betrag=600.0, schluessel="verbrauch",
                   verbrauch_gesamt=200.0, verbrauch_mieter=50.0)
    assert berechne(s, [pos]).summe_anteil == 150.0


def test_saldo_und_vorauszahlungen():
    e = berechne(basis_stammdaten(), [Position("Grundsteuer", betrag=1000.0)])
    assert e.vorauszahlungen == 1200.0
    assert e.saldo == -800.0 and not e.ist_nachzahlung and e.betrag_absolut == 800.0

    e2 = berechne(basis_stammdaten(vorauszahlung_monatlich=10.0),
                  [Position("Grundsteuer", betrag=1000.0)])
    assert e2.ist_nachzahlung and e2.saldo == 280.0


def test_manuelle_vorauszahlung_hat_vorrang():
    s = basis_stammdaten(vorauszahlung_manuell=555.0)
    assert berechne(s, [Position("Grundsteuer", betrag=1000.0)]).vorauszahlungen == 555.0


def test_co2_abzug():
    s = basis_stammdaten(co2_abzug=50.0)
    e = berechne(s, [Position("Heizung", betrag=1000.0)])
    assert e.summe_anteil == 400.0 and e.umlage == 350.0


def test_arbeitskosten_paragraf_35a():
    pos = Position("Gartenpflege", betrag=500.0, arbeitskosten=400.0)
    assert berechne(basis_stammdaten(), [pos]).arbeitskosten_mieter == 160.0


def test_inaktive_und_leere_positionen_fehlen():
    positionen = [
        Position("Aktiv", betrag=100.0),
        Position("Inaktiv", betrag=100.0, aktiv=False),
        Position("Ohne Betrag", betrag=0.0),
    ]
    e = berechne(basis_stammdaten(), positionen)
    assert [z.bezeichnung for z in e.zeilen] == ["Aktiv"]


def test_fehler_bei_zu_langem_zeitraum():
    s = basis_stammdaten(zeitraum_bis="2026-06-30")
    assert any("12 Monate" in f for f in berechne(s, [Position("X", betrag=1.0)]).fehler)


def test_fehler_bei_zu_grosser_mieterflaeche():
    s = basis_stammdaten(flaeche_mieter=300.0)
    assert any("größer als die Gesamtwohnfläche" in f
               for f in berechne(s, [Position("X", betrag=1.0)]).fehler)


def test_warnung_bei_abgelaufener_abrechnungsfrist():
    vorletztes_jahr = date.today().year - 2
    s = basis_stammdaten(zeitraum_von=date(vorletztes_jahr, 1, 1).isoformat(),
                         zeitraum_bis=date(vorletztes_jahr, 12, 31).isoformat(),
                         nutzung_von=date(vorletztes_jahr, 1, 1).isoformat(),
                         nutzung_bis=date(vorletztes_jahr, 12, 31).isoformat())
    assert any("Abrechnungsfrist" in w for w in berechne(s, [Position("X", betrag=1.0)]).warnungen)


def test_warnung_bei_nicht_umlagefaehiger_position():
    e = berechne(basis_stammdaten(), [Position("Reparatur Heizung", betrag=300.0)])
    assert any("nicht umlagefähig" in w for w in e.warnungen)


def test_nutzungszeitraum_wird_auf_abrechnungszeitraum_begrenzt():
    s = basis_stammdaten(nutzung_von="2024-06-01", nutzung_bis="2026-06-01")
    e = berechne(s, [Position("X", betrag=100.0)])
    assert e.tage_nutzung == e.tage_zeitraum == 365


def test_tage_inklusive():
    assert tage(date(2025, 1, 1), date(2025, 1, 31)) == 31
    assert tage(date(2025, 1, 31), date(2025, 1, 1)) == 0


def test_geldformat():
    assert eur(1234.5) == "1.234,50"
    assert eur(-0.5) == "-0,50"


def test_json_roundtrip():
    s = basis_stammdaten()
    positionen = standard_positionen()
    positionen[0].betrag = 123.45
    daten = json.loads(json.dumps(as_dict(s, positionen), ensure_ascii=False))
    s2, p2 = from_dict(daten)
    assert s2 == s
    assert p2[0].betrag == 123.45 and len(p2) == len(positionen)


def test_pdf_wird_erzeugt():
    s = basis_stammdaten()
    e = berechne(s, [Position("Grundsteuer", betrag=1000.0),
                     Position("Wasser", betrag=600.0, schluessel="verbrauch",
                              verbrauch_gesamt=200.0, verbrauch_mieter=50.0, einheit="m³")])
    daten = erzeuge_pdf(s, e)
    assert daten.startswith(b"%PDF") and len(daten) > 1000
    assert dateiname(s).endswith(".pdf") and "2025" in dateiname(s)


def wasser(haus=(1000.0, 1200.0), mieter=(500.0, 580.0), eigen=None, **abweichungen):
    """Wasserposition mit Hauptzähler, Mieter- und optionalem Vermieterzähler."""
    staende = [Zaehlerstand("Hauptzähler", "haus", *haus),
               Zaehlerstand("Mieter kalt", "mieter", *mieter)]
    if eigen:
        staende.append(Zaehlerstand("Eigene Wohnung", "vermieter", *eigen))
    werte = dict(bezeichnung="Wasser", betrag=600.0, schluessel="verbrauch",
                 einheit="m³", zaehler=staende)
    werte.update(abweichungen)
    return Position(**werte)


def test_zaehlerstaende_ergeben_den_verbrauch():
    pos = wasser(eigen=(200.0, 250.0))   # Haus 200, Mieter 80, Vermieter 50
    assert pos.verbrauch_haus == 200.0
    assert pos.verbrauch_wohnung == 80.0
    assert pos.verbrauch_eigen == 50.0


def test_mehrere_zaehler_je_partei_werden_addiert():
    pos = Position("Wasser", betrag=600.0, schluessel="verbrauch", einheit="m³", zaehler=[
        Zaehlerstand("Hauptzähler", "haus", 1000.0, 1200.0),
        Zaehlerstand("Mieter kalt", "mieter", 500.0, 580.0),
        Zaehlerstand("Mieter warm", "mieter", 100.0, 130.0),
        Zaehlerstand("Eigene kalt", "vermieter", 200.0, 240.0),
        Zaehlerstand("Eigene warm", "vermieter", 50.0, 70.0),
    ])
    assert pos.verbrauch_wohnung == 110.0     # 80 + 30
    assert pos.verbrauch_eigen == 60.0        # 40 + 20
    e = berechne(basis_stammdaten(), [pos])
    z = e.zeilen[0].zaehler
    assert z.gemessen == 170.0 and z.differenz == 30.0


def test_verbrauch_ohne_zaehler_bleibt_moeglich():
    pos = Position("Wasser", betrag=600.0, schluessel="verbrauch",
                   verbrauch_gesamt=200.0, verbrauch_mieter=50.0)
    e = berechne(basis_stammdaten(), [pos])
    assert e.summe_anteil == 150.0
    assert e.zeilen[0].zaehler.messungen == []


def test_fehler_bei_ruecklaeufigem_zaehler():
    pos = wasser(haus=(1400.0, 1200.0))
    assert any("kleiner als der Anfangsstand" in f
               for f in berechne(basis_stammdaten(), [pos]).fehler)


def test_fehler_wenn_wohnung_mehr_verbraucht_als_das_haus():
    pos = wasser(haus=(1200.0, 1250.0), mieter=(300.0, 500.0))
    assert any("mehr als der Hauptzähler" in f
               for f in berechne(basis_stammdaten(), [pos]).fehler)


def test_fehlender_verbrauch_wird_gemeldet():
    pos = Position("Wasser", betrag=600.0, schluessel="verbrauch")
    assert any("fehlen Zählerstände" in f
               for f in berechne(basis_stammdaten(), [pos]).fehler)


def test_mengenformat():
    assert menge(88.0) == "88"
    assert menge(12.345) == "12,345"
    assert menge(210.5) == "210,5"


def test_pdf_mit_zaehlerstaenden():
    s = basis_stammdaten()
    positionen = [wasser_mit_differenz(), waermezaehler(),
                  Position("Abwasser", betrag=300.0, schluessel="verbrauch",
                           einheit="m³", zaehler_von="Wasser"),
                  Position("Grundsteuer", betrag=500.0)]
    daten = erzeuge_pdf(s, berechne(s, positionen))
    assert daten.startswith(b"%PDF") and len(daten) > 1000


# --- Zählerdifferenz zwischen Hauptzähler und Wohnungszählern ---------------

def wasser_mit_differenz() -> Position:
    # Haus 200, Mieter 80, Vermieter 100 -> 20 Differenz
    return wasser(haus=(1000.0, 1200.0), mieter=(500.0, 580.0), eigen=(200.0, 300.0))


def test_differenz_wird_nach_verbrauch_verteilt():
    s = basis_stammdaten()   # Voreinstellung: nach gemessenem Verbrauch
    z = berechne(s, [wasser_mit_differenz()]).zeilen[0].zaehler
    assert z.differenz == 20.0
    assert z.differenz_mieter == round(20 * 80 / 180, 2)     # 8,89
    assert z.menge_mieter == 88.89
    assert "gemessenem Verbrauch" in z.differenz_text


def test_differenz_wird_nach_wohnflaeche_verteilt():
    s = basis_stammdaten(zaehlerdifferenz="flaeche")   # Mieter 80 von 200 m² = 40 %
    e = berechne(s, [wasser_mit_differenz()])
    z = e.zeilen[0].zaehler
    assert z.differenz_mieter == 8.0
    assert z.menge_mieter == 88.0
    assert e.summe_anteil == round(600 * 88 / 200, 2)
    assert "Wohnfläche" in z.differenz_text


def test_ohne_eigenen_zaehler_bleibt_die_differenz_beim_vermieter():
    e = berechne(basis_stammdaten(), [wasser()])
    assert e.zeilen[0].zaehler.differenz == 0.0
    assert e.summe_anteil == round(600 * 80 / 200, 2)


def test_warnung_wenn_unterzaehler_mehr_zeigen_als_der_hauptzaehler():
    pos = wasser(haus=(1000.0, 1100.0), mieter=(500.0, 580.0), eigen=(200.0, 300.0))
    e = berechne(basis_stammdaten(), [pos])
    assert any("mehr an als der Hauptzähler" in w for w in e.warnungen)
    assert e.zeilen[0].zaehler.differenz == 0.0


# --- Wärmemengenzähler: nur die Unterzähler im Verhältnis -------------------

def waermezaehler() -> Position:
    return Position("Heizung (Gas)", betrag=2400.0, schluessel="verbrauch", einheit="kWh",
                    zaehler_grundlage="unterzaehler", zaehler=[
                        Zaehlerstand("Gaszähler Haus", "haus", 18450.0, 20890.0),
                        Zaehlerstand("Fußbodenheizung Mieter", "mieter", 4000.0, 7200.0),
                        Zaehlerstand("Fußbodenheizung eigene", "vermieter", 2000.0, 4100.0),
                        Zaehlerstand("Heizkörper eigene", "vermieter", 1000.0, 3600.0),
                    ])


def test_gas_wird_nach_den_waermemengenzaehlern_verteilt():
    """Der Gaszähler misst m³, die Wärmemengenzähler kWh – gerechnet wird mit kWh."""
    e = berechne(basis_stammdaten(), [waermezaehler()])
    z = e.zeilen[0].zaehler
    assert z.basis == 7900.0                      # 3200 + 2100 + 2600
    assert z.menge_mieter == 3200.0
    assert z.differenz == 0.0                     # Gaszähler bleibt außen vor
    assert e.summe_anteil == round(2400 * 3200 / 7900, 2)


def test_infozaehler_erzeugt_keine_warnung():
    e = berechne(basis_stammdaten(), [waermezaehler()])
    assert not any("Hauptzähler" in w for w in e.warnungen)


# --- Zähler einer anderen Position mitbenutzen -----------------------------

def test_abwasser_nutzt_die_wasserzaehler():
    wasserposition = wasser_mit_differenz()
    abwasser = Position("Abwasser", betrag=300.0, schluessel="verbrauch",
                        einheit="m³", zaehler_von="Wasser")
    e = berechne(basis_stammdaten(), [wasserposition, abwasser])
    anteil_wasser, anteil_abwasser = e.zeilen[0], e.zeilen[1]
    assert anteil_abwasser.quote == anteil_wasser.quote
    assert anteil_abwasser.zaehler.quelle == "Wasser"
    assert "Zähler von" in anteil_abwasser.schluessel_text


def test_hinweis_wenn_die_quelle_der_zaehler_fehlt():
    abwasser = Position("Abwasser", betrag=300.0, schluessel="verbrauch",
                        zaehler_von="Gibt es nicht")
    e = berechne(basis_stammdaten(), [abwasser])
    assert any("gibt es nicht (mehr)" in w for w in e.warnungen)


def test_meldungen_erscheinen_nur_einmal():
    pos = wasser(haus=(1000.0, 1100.0), mieter=(500.0, 580.0), eigen=(200.0, 300.0))
    abwasser = Position("Abwasser", betrag=300.0, schluessel="verbrauch", zaehler_von="Wasser")
    e = berechne(basis_stammdaten(), [pos, abwasser])
    assert len(e.warnungen) == len(set(e.warnungen))


def test_alte_gespeicherte_daten_werden_uebernommen():
    """Dateien aus der Fassung mit drei festen Zählern müssen weiter lesbar sein."""
    alt = {"stammdaten": {"flaeche_gesamt": 200.0},
           "positionen": [{"bezeichnung": "Wasser", "betrag": 600.0, "schluessel": "verbrauch",
                           "zaehler_haus_alt": 1000, "zaehler_haus_neu": 1200,
                           "zaehler_mieter_alt": 500, "zaehler_mieter_neu": 580,
                           "zaehler_eigen_alt": 200, "zaehler_eigen_neu": 300}]}
    _, positionen = from_dict(alt)
    pos = positionen[0]
    assert [z.partei for z in pos.zaehler] == ["haus", "mieter", "vermieter"]
    assert pos.verbrauch_haus == 200.0 and pos.verbrauch_eigen == 100.0


def test_endabrechnung_bei_auszug():
    s = basis_stammdaten(abrechnungsart="mietende", auszug_am="2025-06-30",
                         zeitraum_bis="2025-06-30", nutzung_bis="2025-06-30")
    e = berechne(s, [Position("Grundsteuer", betrag=1000.0)])
    assert s.ist_endabrechnung and s.bezeichnung_abrechnung == "Abrechnung zum Mietende"
    assert e.tage_zeitraum == e.tage_nutzung == 181
    assert e.summe_anteil == 400.0             # voller Zeitraum = volle Umlage


def test_speichern_und_laden(tmp_ordner=None):
    import tempfile
    from pathlib import Path
    from nebenkosten import speicher

    with tempfile.TemporaryDirectory() as ordner:
        original_ordner, original_datei, original_archiv = (
            speicher.ORDNER, speicher.AKTUELL, speicher.ARCHIV)
        try:
            speicher.ORDNER = Path(ordner)
            speicher.AKTUELL = Path(ordner) / "abrechnung.json"
            speicher.ARCHIV = Path(ordner) / "archiv"

            assert speicher.laden() is None
            s = basis_stammdaten(flaeche_gesamt=222.0)
            positionen = standard_positionen()
            positionen[0].betrag = 481.0
            speicher.speichern(s, positionen)

            s2, p2 = speicher.laden()
            assert s2.flaeche_gesamt == 222.0 and p2[0].betrag == 481.0
            assert speicher.gespeichert_am() is not None

            speicher.archivieren(s, positionen)
            assert len(speicher.archiv()) == 1
            assert speicher.aus_archiv(speicher.archiv()[0])[0].flaeche_gesamt == 222.0
        finally:
            speicher.ORDNER, speicher.AKTUELL, speicher.ARCHIV = (
                original_ordner, original_datei, original_archiv)


def test_ablage_laesst_sich_umstellen():
    """Statt in eine Datei kann alles in eine Google-Tabelle geschrieben werden."""
    from datetime import datetime as _dt
    from nebenkosten import speicher

    class Tabelle:
        beschreibung = "Google-Tabelle"
        adresse = "https://docs.google.com/spreadsheets/d/test"

        def __init__(self):
            self.zeilen = {}

        def lesen(self, schluessel):
            return self.zeilen.get(schluessel)

        def schreiben(self, schluessel, daten):
            self.zeilen[schluessel] = daten

        def zeitpunkt(self, schluessel):
            return _dt.now() if schluessel in self.zeilen else None

        def schluessel(self):
            return [k for k in self.zeilen if k != "aktuell"]

    tabelle = Tabelle()
    try:
        speicher.konfiguriere(tabelle)
        assert speicher.laden() is None
        assert speicher.beschreibung() == "Google-Tabelle"

        s = basis_stammdaten(flaeche_gesamt=321.0)
        positionen = standard_positionen()
        speicher.speichern(s, positionen)
        assert "aktuell" in tabelle.zeilen
        assert speicher.laden()[0].flaeche_gesamt == 321.0
        assert speicher.gespeichert_am() is not None

        name = speicher.archivieren(s, positionen)
        assert speicher.archiv() == [name]
        assert speicher.aus_archiv(name)[0].flaeche_gesamt == 321.0
        assert " " in speicher.archivname(name)
    finally:
        speicher.konfiguriere(None)
    assert speicher.beschreibung() == "Datei auf diesem Gerät"


# --- Zwischenabrechnung ----------------------------------------------------

def halbjahr(**abweichungen) -> Stammdaten:
    werte = dict(abrechnungsart="zwischen", zeitraum_von="2025-01-01",
                 zeitraum_bis="2025-06-30", nutzung_von="2025-01-01",
                 nutzung_bis="2025-06-30", vorauszahlung_monate=6)
    werte.update(abweichungen)
    return basis_stammdaten(**werte)


def test_zwischenabrechnung_ist_unverbindlich():
    s = halbjahr()
    assert s.bezeichnung_abrechnung == "Zwischenabrechnung" and not s.ist_verbindlich
    e = berechne(s, [Position("Heizung", betrag=1400.0)])
    assert any("begründet noch keine Nachzahlung" in w for w in e.warnungen)


def test_zwischenabrechnung_kennt_keine_abrechnungsfrist():
    """Die Zwölfmonatsfrist läuft erst mit der regulären Abrechnung."""
    vorletztes = date.today().year - 2
    s = halbjahr(zeitraum_von=date(vorletztes, 1, 1).isoformat(),
                 zeitraum_bis=date(vorletztes, 6, 30).isoformat(),
                 nutzung_von=date(vorletztes, 1, 1).isoformat(),
                 nutzung_bis=date(vorletztes, 6, 30).isoformat())
    e = berechne(s, [Position("Heizung", betrag=1400.0)])
    assert not any("Abrechnungsfrist" in w for w in e.warnungen)


def test_hochrechnung_aufs_ganze_jahr():
    s = halbjahr(vorauszahlung_monatlich=100.0)
    e = berechne(s, [Position("Heizung", betrag=1000.0)])   # Mieter 40 % = 400 EUR
    assert e.tage_nutzung == 181
    assert e.umlage == 400.0
    assert e.hochrechnung_jahr == round(400 / 181 * 365, 2)
    assert e.empfehlung_vorauszahlung == 68.0               # aufgerundet je Monat


def test_jahresabrechnung_ohne_hochrechnungsbedarf():
    e = berechne(basis_stammdaten(), [Position("Heizung", betrag=1000.0)])
    assert e.hochrechnung_jahr == 400.0                     # voller Zeitraum


def test_zwischenabrechnung_als_pdf():
    s = halbjahr(anlass="Wechsel des Gasanbieters")
    daten = erzeuge_pdf(s, berechne(s, [Position("Heizung", betrag=1400.0)]))
    assert daten.startswith(b"%PDF") and len(daten) > 1000


def test_archivname_nennt_die_art():
    from nebenkosten import speicher

    assert "Zwischenabrechnung" in speicher._dateiname(halbjahr(mieter_name="Meier"))
    assert "Mietende" in speicher._dateiname(
        basis_stammdaten(abrechnungsart="mietende", mieter_name="Meier"))
    assert "Jahresabrechnung" in speicher._dateiname(basis_stammdaten(mieter_name="Meier"))


# --- Grundkosten, Warmwasserformel, CO2, eigene Aufstellung ----------------

def test_grundkosten_und_verbrauchskosten_getrennt():
    """Heizkosten: 30 % nach Wohnfläche, 70 % nach Verbrauch – wie beim Abrechner."""
    pos = Position("Heizung", betrag=1000.0, schluessel="verbrauch", einheit="kWh",
                   zaehler_grundlage="unterzaehler", grundkosten_anteil=30.0, zaehler=[
                       Zaehlerstand("Mieter", "mieter", 0.0, 4000.0),
                       Zaehlerstand("eigene", "vermieter", 0.0, 6000.0)])
    e = berechne(basis_stammdaten(), [pos])          # Mieter 80 von 200 m² = 40 %
    assert [z.bezeichnung for z in e.zeilen] == [
        "Heizung – Grundkosten 30 %", "Heizung – Verbrauchskosten 70 %"]
    assert e.zeilen[0].anteil == 120.0               # 300 × 40 %
    assert e.zeilen[1].anteil == 280.0               # 700 × 40 % Verbrauch
    assert e.summe_gesamtkosten == 1000.0 and e.summe_anteil == 400.0


def test_ohne_grundkostenanteil_bleibt_eine_zeile():
    pos = Position("Wasser", betrag=600.0, schluessel="verbrauch",
                   verbrauch_gesamt=200.0, verbrauch_mieter=50.0)
    assert len(berechne(basis_stammdaten(), [pos]).zeilen) == 1


def test_warmwasserformel_nach_paragraf_9_heizkostenv():
    from nebenkosten.berechnung import warmwasser_kwh

    # Beispiel aus einer echten Abrechnung: 61,271 m³ bei 40 °C
    # 2,5 x 61,271 x 30 = 4.595,3 kWh - ohne jeden Zuschlag, so steht es im Gesetz.
    assert round(warmwasser_kwh(61.271, 40.0), 1) == 4595.3
    # ohne gemessene Temperatur schreibt die Verordnung 60 °C vor
    assert round(warmwasser_kwh(61.271), 1) == 7658.9
    assert warmwasser_kwh(0.0) == 0.0
    # Gegenprobe: der Faktor 2,5 deckt die Anlagenverluste schon ab. Rechnerisch
    # braucht ein Kubikmeter je Grad rund 1,16 kWh - wer zusaetzlich aufschlaegt,
    # verschiebt Kosten zwischen Heizung und Warmwasser.
    assert warmwasser_kwh(10.0, 60.0) == 1250.0


def test_co2_stufenmodell():
    from nebenkosten.berechnung import co2_vermieteranteil

    assert co2_vermieteranteil(1000.0, 245.0)[0] == 0.0      # 4,1 kg/m² – Mieter allein
    assert co2_vermieteranteil(5699.0, 245.0)[0] == 30.0     # 23,3 kg/m²
    assert co2_vermieteranteil(20000.0, 245.0)[0] == 95.0    # 81,6 kg/m²
    assert co2_vermieteranteil(0.0, 245.0)[0] == 0.0
    assert "Vermieteranteil 30 %" in co2_vermieteranteil(5699.0, 245.0)[1]


def test_aufstellung_fuer_die_eigene_wohnung():
    s = basis_stammdaten()                    # 200 m² gesamt, 80 m² Mietwohnung
    positionen = [Position("Grundsteuer", betrag=1000.0),
                  Position("Müll Mietwohnung", betrag=200.0, schluessel="direkt")]
    mieter = berechne(s, positionen)
    eigene = berechne(s, positionen, fuer="vermieter")
    assert eigene.fuer_vermieter and not mieter.fuer_vermieter
    assert mieter.summe_anteil == 400.0 + 200.0
    assert eigene.summe_anteil == 600.0            # 60 % der Grundsteuer, kein Müll
    assert eigene.vorauszahlungen == 0.0
    # zusammen ergeben beide Sichten die Gesamtkosten
    assert round(mieter.summe_anteil + eigene.summe_anteil, 2) == 1200.0


def test_direkte_zuordnung_an_den_vermieter():
    pos = Position("Eigene Tonne", betrag=150.0, schluessel="direkt_vermieter")
    assert berechne(basis_stammdaten(), [pos]).summe_anteil == 0.0
    assert berechne(basis_stammdaten(), [pos], fuer="vermieter").summe_anteil == 150.0


def test_eigene_aufstellung_als_pdf():
    s = basis_stammdaten()
    eigene = berechne(s, [Position("Grundsteuer", betrag=1000.0)], fuer="vermieter")
    daten = erzeuge_pdf(s, eigene)
    assert daten.startswith(b"%PDF") and len(daten) > 1000
    assert dateiname(s, fuer="vermieter") == "Nebenkosten_2025_eigene_Wohnung.pdf"


def test_warnung_bei_sehr_grosser_zaehlerdifferenz():
    """Leerstand oder verschiedene Ablesetermine – dann darf nicht anteilig verteilt werden."""
    pos = wasser(haus=(0.0, 188.0), mieter=(0.0, 27.85), eigen=(0.0, 118.02))
    e = berechne(basis_stammdaten(), [pos])
    assert any("ungewöhnlich groß" in w for w in e.warnungen)


# --- Gemeinsam genutzte Zähler (Außenzapfstelle) ---------------------------

def wasser_mit_garten(garten_partei: str = "gemeinsam") -> Position:
    return Position("Wasser", betrag=922.0, schluessel="verbrauch", einheit="m³", zaehler=[
        Zaehlerstand("Hauptzähler", "haus", 0.0, 188.0),
        Zaehlerstand("Mieter", "mieter", 0.0, 60.0),
        Zaehlerstand("eigene Wohnung", "vermieter", 0.0, 110.0),
        Zaehlerstand("Außenzapfstelle", garten_partei, 0.0, 15.0)])


def test_gartenwasser_dem_vermieter_zugeordnet():
    """Nutzt nur der Vermieter den Außenhahn, zahlt der Mieter nichts davon."""
    e = berechne(basis_stammdaten(), [wasser_mit_garten("vermieter")])
    z = e.zeilen[0].zaehler
    assert z.gemeinsam_verbrauch == 0.0
    assert z.differenz == 3.0                    # 188 - (60 + 110 + 15)
    assert z.menge_mieter == 60.0 + round(3.0 * 60 / 185, 2)


def test_gartenwasser_gemeinsam_wird_verteilt():
    e = berechne(basis_stammdaten(), [wasser_mit_garten("gemeinsam")])
    z = e.zeilen[0].zaehler
    assert z.gemeinsam_verbrauch == 15.0
    assert z.gemeinsam_anteil == round(15.0 * 60 / 170, 2)   # nach gemessenem Verbrauch
    assert z.differenz == 3.0
    assert z.menge_mieter > 60.0


def test_gartenzaehler_senkt_den_mieteranteil():
    """Ohne eigenen Zähler steckt das Gartenwasser in der Differenz."""
    ohne = Position("Wasser", betrag=922.0, schluessel="verbrauch", einheit="m³", zaehler=[
        Zaehlerstand("Hauptzähler", "haus", 0.0, 188.0),
        Zaehlerstand("Mieter", "mieter", 0.0, 60.0),
        Zaehlerstand("eigene Wohnung", "vermieter", 0.0, 110.0)])
    mit = wasser_mit_garten("vermieter")
    assert berechne(basis_stammdaten(), [ohne]).summe_anteil > \
           berechne(basis_stammdaten(), [mit]).summe_anteil


def test_gemeinsame_menge_nach_wohnflaeche():
    s = basis_stammdaten(zaehlerdifferenz="flaeche")     # Mieter 80 von 200 m² = 40 %
    z = berechne(s, [wasser_mit_garten("gemeinsam")]).zeilen[0].zaehler
    assert z.gemeinsam_anteil == 6.0                     # 15 × 40 %
    assert "Wohnfläche" in z.verteiltext


def test_warnung_bei_nicht_abgelesenem_zaehler():
    """Ein leerer Zähler wandert sonst unbemerkt in die Differenz."""
    pos = Position("Wasser", betrag=922.0, schluessel="verbrauch", einheit="m³", zaehler=[
        Zaehlerstand("Hauptzähler", "haus", 0.0, 188.0),
        Zaehlerstand("Mieter", "mieter", 0.0, 60.0),
        Zaehlerstand("eigene Wohnung", "vermieter", 0.0, 110.0),
        Zaehlerstand("Außenzapfstelle / Garten", "vermieter", 0.0, 0.0)])
    e = berechne(basis_stammdaten(), [pos])
    assert any("Außenzapfstelle" in w and "fehlen die Stände" in w for w in e.warnungen)


def test_keine_warnung_wenn_gar_keine_zaehler_abgelesen_sind():
    pos = Position("Wasser", betrag=922.0, schluessel="verbrauch", zaehler=[
        Zaehlerstand("Hauptzähler", "haus", 0.0, 0.0),
        Zaehlerstand("Mieter", "mieter", 0.0, 0.0)])
    assert not any("fehlen die Stände" in w for w in berechne(basis_stammdaten(), [pos]).warnungen)


# --- Kategorien ------------------------------------------------------------

def test_katalog_ist_nach_kategorien_sortiert():
    from nebenkosten.modell import KATEGORIEN

    positionen = standard_positionen()
    assert {p.kategorie for p in positionen} <= set(KATEGORIEN)
    for schluessel in ("wasser", "gas", "sonstiges"):
        assert any(p.kategorie == schluessel and p.aktiv for p in positionen)
    # jede Position hat einen Hinweis, welcher Beleg dazugehört
    assert all(p.hinweis for p in positionen)


def test_ergebnis_gruppiert_nach_kategorie():
    positionen = [Position("Wasser", "wasser", betrag=400.0),
                  Position("Abwasser", "wasser", betrag=500.0),
                  Position("Heizung", "gas", betrag=2000.0),
                  Position("Grundsteuer", "sonstiges", betrag=1000.0)]
    e = berechne(basis_stammdaten(), positionen)
    gruppen = e.nach_kategorie()
    assert [g[0] for g in gruppen] == ["wasser", "gas", "sonstiges"]
    assert gruppen[0][2] == 900.0 and gruppen[0][3] == 360.0     # 40 % Wohnfläche
    assert round(sum(g[3] for g in gruppen), 2) == e.summe_anteil


def test_katalog_enthaelt_die_umlagefaehigen_kostenarten():
    from nebenkosten import katalog

    namen = {k.name for k in katalog.KATALOG}
    for pflicht in ("Niederschlagswasser", "Kosten der Heizkostenabrechnung",
                    "Rauchwarnmelder – Wartung", "Grundgebühr Wasser / Zählermiete",
                    "Legionellenprüfung", "Betriebsstrom der Heizung",
                    "Baumpflege und Baumfällung", "Aufzug", "Hausmeister"):
        assert pflicht in namen, pflicht


def test_warnung_nur_wenn_waerme_gar_nicht_nach_verbrauch_geht():
    s = basis_stammdaten()
    nur_flaeche = [Position("Heizung", "gas", betrag=2000.0, schluessel="flaeche")]
    assert any("nur nach Fläche" in w for w in berechne(s, nur_flaeche).warnungen)

    mit_zaehler = [Position("Heizung", "gas", betrag=2000.0, schluessel="verbrauch",
                            verbrauch_gesamt=100.0, verbrauch_mieter=30.0),
                   Position("Heizungswartung", "gas", betrag=180.0, schluessel="flaeche")]
    assert not any("nur nach Fläche" in w for w in berechne(s, mit_zaehler).warnungen)


# --- Aussehen und Startbildschirm ------------------------------------------

def test_alte_dateien_bekommen_eine_kategorie():
    """Vor der Gliederung gespeicherte Daten kannten kein Feld „kategorie“."""
    alt = {"stammdaten": {},
           "positionen": [{"bezeichnung": "Wasser", "betrag": 402.52},
                          {"bezeichnung": "Abwasser", "betrag": 519.18},
                          {"bezeichnung": "Heizung (Gas)", "betrag": 1970.53},
                          {"bezeichnung": "Schornsteinfeger", "betrag": 95.0},
                          {"bezeichnung": "Grundsteuer", "betrag": 421.44}]}
    positionen = from_dict(alt)[1]
    assert [p.kategorie for p in positionen] == [
        "wasser", "wasser", "gas", "gas", "sonstiges"]
    assert positionen[0].betrag == 402.52     # Cents bleiben erhalten


def test_kategorie_raten():
    from nebenkosten.modell import kategorie_raten

    assert kategorie_raten("Niederschlagswasser") == "wasser"
    assert kategorie_raten("Wärmemengenzähler-Miete") == "gas"
    assert kategorie_raten("Gartenpflege") == "sonstiges"


def test_gestaltung_laesst_sich_laden():
    from nebenkosten import design

    stil = design._stil()
    assert stil.startswith("\n<style>") and stil.rstrip().endswith("</style>")
    assert "--nk-akzent" in stil and "prefers-color-scheme: dark" in stil
    # Die Symbolschrift darf nicht überschrieben werden, sonst erscheinen
    # die Namen der Symbole als Text.
    assert "font-family" not in stil.split("/* ---------- Kopfzeile")[0]


def test_symbol_und_manifest_liegen_bereit():
    from pathlib import Path

    from nebenkosten import design

    statisch = Path(__file__).resolve().parents[1] / "static"
    for name in ("app-icon.png", "app-icon-180.png", "app-icon-apple.png"):
        assert (statisch / name).exists(), name

    angaben = design._startbildschirm_angaben()
    manifest = angaben["manifest"]
    assert manifest["display"] == "standalone"
    assert manifest["icons"], "ohne Symbol kein Startbildschirm-Eintrag"
    assert angaben["apfel"], "ohne apple-touch-icon bleibt das iPhone beim Streamlit-Symbol"
    # start_url und scope traegt erst das Skript ein - relative Angaben waeren
    # in einer Datenadresse ungueltig und der Browser wuerde das Manifest wegwerfen.
    assert "start_url" not in manifest and "scope" not in manifest


def test_manifest_symbole_haengen_an_keiner_dateiablage():
    """Die Streamlit Community Cloud liefert static/ nicht aus."""
    from nebenkosten import design

    manifest = design._startbildschirm_angaben()["manifest"]
    assert all(s["src"].startswith("data:image/png;base64,") for s in manifest["icons"])


def test_kein_symbol_zeigt_auf_die_tote_dateiablage():
    """/app/static/... liefert die Streamlit Community Cloud nicht aus. Zeigt ein
    Symbol dorthin, laeuft es ins Leere und der Browser nimmt sein eigenes
    Ersatzbild - genau das landet dann auf dem Startbildschirm."""
    from nebenkosten import design

    angaben = design._startbildschirm_angaben()
    adressen = [s["src"] for s in angaben["manifest"]["icons"]]
    adressen += [angaben["symbol"], angaben["apfel"]]
    for adresse in adressen:
        assert adresse.startswith("data:image/png;base64,"), adresse


def test_apple_symbol_ist_randfuellend_und_undurchsichtig():
    """iOS rundet selbst ab und faerbt alles Durchsichtige schwarz."""
    from PIL import Image

    bild = Image.open(design_pfad()).convert("RGBA")
    ecken = [(0, 0), (bild.width - 1, 0), (0, bild.height - 1),
             (bild.width - 1, bild.height - 1)]
    for x, y in ecken:
        assert bild.getpixel((x, y))[3] == 255, "durchsichtige Ecke wird auf dem iPhone schwarz"


def design_pfad():
    from nebenkosten import design

    return design.ICON_APPLE


def test_warmwasser_benutzt_die_wasserzaehler_mit():
    """Dieselben Zaehler zweimal eintippen heisst zweimal Gelegenheit fuer einen
    Zahlendreher - und wenn beide Eingaben auseinanderlaufen, rechnet die App
    mit zwei Wahrheiten."""
    from nebenkosten.berechnung import zaehlerquelle
    from nebenkosten.modell import standard_positionen

    positionen = standard_positionen()
    nach_name = {p.bezeichnung: p for p in positionen}
    warm = nach_name["Warmwasser (Gas)"]

    assert warm.zaehler == [], "Warmwasser darf keine eigenen Zaehler mehr haben"
    assert warm.zaehler_von == "Wasser"

    quelle = zaehlerquelle(warm, positionen)
    namen = [z.name for z in quelle.zaehler]
    assert namen == ["Warmwasser Mieter", "Warmwasser eigene Wohnung"]
    # Die Wasserposition selbst bleibt vollstaendig.
    assert len(nach_name["Wasser"].zaehler) == 6


def test_abwasser_nimmt_weiter_alle_wasserzaehler():
    from nebenkosten.berechnung import zaehlerquelle
    from nebenkosten.modell import standard_positionen

    positionen = standard_positionen()
    abwasser = next(p for p in positionen if p.bezeichnung == "Abwasser")
    assert len(zaehlerquelle(abwasser, positionen).zaehler) == 6


def test_gaszaehler_in_kubikmetern_waermemenge_in_kilowattstunden():
    from nebenkosten.modell import standard_positionen

    heizung = next(p for p in standard_positionen()
                   if p.bezeichnung == "Heizung (Gas)")
    einheiten = {z.name: z.einheit for z in heizung.zaehler}
    assert einheiten["Gaszähler Haus (nur zur Information)"] == "m³"
    assert all(e == "kWh" for name, e in einheiten.items() if name.startswith("Wärmemenge"))


def test_einheit_steht_je_zaehler_im_ergebnis():
    from nebenkosten.berechnung import verbrauchsaufteilung
    from nebenkosten.modell import Position, Zaehlerstand

    pos = Position("Heizung (Gas)", "gas", betrag=1000.0, schluessel="verbrauch",
                   einheit="kWh", zaehler_grundlage="unterzaehler",
                   zaehler=[Zaehlerstand("Gaszähler Haus", "haus", 0, 2440, einheit="m³"),
                            Zaehlerstand("Wärmemenge Mieter", "mieter", 0, 9000),
                            Zaehlerstand("Wärmemenge eigen", "vermieter", 0, 11000)])
    z = verbrauchsaufteilung(pos, basis_stammdaten(), [pos])
    nach_name = {m.name: m.einheit for m in z.messungen}
    assert nach_name["Gaszähler Haus"] == "m³"
    # Ohne eigene Angabe gilt die Einheit der Kostenart.
    assert nach_name["Wärmemenge Mieter"] == "kWh"


def _alter_stand() -> dict:
    """Gespeicherte Daten im Aufbau von frueher: Warmwasser mit eigenen Zaehlern."""
    return {
        "stammdaten": {"vermieter_name": "Vermieter"},
        "positionen": [
            {"bezeichnung": "Wasser", "kategorie": "wasser", "schluessel": "verbrauch",
             "einheit": "m³", "zaehler": [
                 {"name": "Hauptzähler Wasser", "partei": "haus", "alt": 0, "neu": 0},
                 {"name": "Warmwasser Mieter", "partei": "mieter", "alt": 0, "neu": 0},
                 {"name": "Warmwasser eigene Wohnung", "partei": "vermieter",
                  "alt": 0, "neu": 0}]},
            {"bezeichnung": "Warmwasser (Gas)", "kategorie": "gas", "schluessel": "verbrauch",
             "einheit": "m³", "zaehler": [
                 {"name": "Warmwasser Mieter", "partei": "mieter", "alt": 0, "neu": 0},
                 {"name": "Warmwasser eigene Wohnung", "partei": "vermieter",
                  "alt": 0, "neu": 0}]},
            {"bezeichnung": "Heizung (Gas)", "kategorie": "gas", "schluessel": "verbrauch",
             "einheit": "kWh", "zaehler": [
                 {"name": "Gaszähler Haus (nur zur Information)", "partei": "haus",
                  "alt": 0, "neu": 0},
                 {"name": "Wärmemenge Fußbodenheizung Mieter", "partei": "mieter",
                  "alt": 0, "neu": 0}]},
        ],
    }


def test_gespeicherte_daten_ziehen_das_warmwasser_nach():
    from nebenkosten.modell import from_dict

    _, positionen = from_dict(_alter_stand())
    warm = next(p for p in positionen if p.bezeichnung == "Warmwasser (Gas)")
    assert warm.zaehler == []
    assert warm.zaehler_von == "Wasser"
    assert warm.zaehler_nur == ["Warmwasser Mieter", "Warmwasser eigene Wohnung"]


def test_gespeicherte_daten_bekommen_die_einheit_je_zaehler():
    from nebenkosten.modell import from_dict

    _, positionen = from_dict(_alter_stand())
    heizung = next(p for p in positionen if p.bezeichnung == "Heizung (Gas)")
    einheiten = {z.name: z.einheit for z in heizung.zaehler}
    assert einheiten["Gaszähler Haus (nur zur Information)"] == "m³"
    assert einheiten["Wärmemenge Fußbodenheizung Mieter"] == "kWh"


def test_warmwasser_behaelt_keine_eigenen_felder():
    """Der Zaehler wird beim Wasser abgelesen und dort eingetragen. Beim
    Warmwasser darf gar nichts zum Eintippen uebrig bleiben."""
    from nebenkosten.modell import from_dict

    daten = _alter_stand()
    daten["positionen"][1]["zaehler"][0]["alt"] = 100
    daten["positionen"][1]["zaehler"][0]["neu"] = 148

    _, positionen = from_dict(daten)
    warm = next(p for p in positionen if p.bezeichnung == "Warmwasser (Gas)")
    assert warm.zaehler == []
    assert warm.zaehler_von == "Wasser"


def test_unbekannter_zaehler_wandert_zum_wasser():
    """Steht beim Warmwasser ein Zaehler, den es beim Wasser gar nicht gibt,
    muss er dorthin - sonst verschwaende er samt Stand."""
    from nebenkosten.modell import from_dict

    daten = _alter_stand()
    daten["positionen"][1]["zaehler"].append(
        {"name": "Warmwasser Einliegerwohnung", "partei": "mieter", "alt": 10, "neu": 30})

    _, positionen = from_dict(daten)
    nach_name = {p.bezeichnung: p for p in positionen}
    gewandert = next(z for z in nach_name["Wasser"].zaehler
                     if z.name == "Warmwasser Einliegerwohnung")
    assert (gewandert.alt, gewandert.neu) == (10, 30)
    assert nach_name["Warmwasser (Gas)"].zaehler == []


def test_halb_umgestellte_daten_werden_repariert():
    """Zwischenstand aus einer aelteren Fassung: verknuepft, aber ohne die Liste
    der Zaehler - dann naehme das Warmwasser alle Wasserzaehler, auch Kaltwasser
    und Garten."""
    from nebenkosten.berechnung import zaehlerquelle
    from nebenkosten.modell import from_dict

    daten = _alter_stand()
    daten["positionen"][1]["zaehler"] = []
    daten["positionen"][1]["zaehler_von"] = "Wasser"

    _, positionen = from_dict(daten)
    warm = next(p for p in positionen if p.bezeichnung == "Warmwasser (Gas)")
    assert warm.zaehler_nur == ["Warmwasser Mieter", "Warmwasser eigene Wohnung"]
    benutzt = [z.name for z in zaehlerquelle(warm, positionen).zaehler]
    assert benutzt == ["Warmwasser Mieter", "Warmwasser eigene Wohnung"]


def test_gleiche_staende_werden_einfach_zusammengelegt():
    from nebenkosten.modell import from_dict

    daten = _alter_stand()
    for eintrag in (daten["positionen"][0]["zaehler"][1], daten["positionen"][1]["zaehler"][0]):
        eintrag["alt"], eintrag["neu"] = 100, 148

    _, positionen = from_dict(daten)
    warm = next(p for p in positionen if p.bezeichnung == "Warmwasser (Gas)")
    assert warm.zaehler == [] and warm.zaehler_von == "Wasser"


def test_wasserstand_hat_vorrang():
    """Es ist derselbe Zaehler. Massgeblich ist, was beim Wasser steht - dort
    traegt man ihn ein."""
    from nebenkosten.modell import from_dict

    daten = _alter_stand()
    daten["positionen"][0]["zaehler"][1]["alt"] = 100
    daten["positionen"][0]["zaehler"][1]["neu"] = 148
    daten["positionen"][1]["zaehler"][0]["alt"] = 100
    daten["positionen"][1]["zaehler"][0]["neu"] = 184   # alter Tippfehler

    _, positionen = from_dict(daten)
    nach_name = {p.bezeichnung: p for p in positionen}
    assert nach_name["Warmwasser (Gas)"].zaehler == []
    behalten = next(z for z in nach_name["Wasser"].zaehler if z.name == "Warmwasser Mieter")
    assert (behalten.alt, behalten.neu) == (100, 148)


# --- Gas: Kubikmeter in Kilowattstunden ------------------------------------

def test_gasumrechnung():
    from nebenkosten.berechnung import gas_kwh

    # 2.440 m³ mit Zustandszahl 0,95 und Brennwert 10,5 kWh/m³
    assert round(gas_kwh(2440.0, 0.95, 10.5)) == 24339
    assert gas_kwh(0.0, 0.95, 10.5) == 0.0
    assert gas_kwh(2440.0, 0.0, 10.5) == 0.0     # fehlende Zustandszahl
    assert gas_kwh(2440.0, 0.95, 0.0) == 0.0     # fehlender Brennwert


def test_pdf_erklaert_die_gasumrechnung():
    s = basis_stammdaten(gas_zustandszahl=0.9563, gas_brennwert=11.024)
    heizung = Position("Heizung (Gas)", "gas", betrag=2000.0, schluessel="verbrauch",
                       einheit="kWh", zaehler_grundlage="unterzaehler", zaehler=[
                           Zaehlerstand("Gaszähler Haus", "haus", 18450.0, 20890.0),
                           Zaehlerstand("Wärmemenge Mieter", "mieter", 0.0, 4000.0),
                           Zaehlerstand("Wärmemenge eigene", "vermieter", 0.0, 6000.0)])
    daten = erzeuge_pdf(s, berechne(s, [heizung]))
    assert daten.startswith(b"%PDF")


def test_umrechnungswerte_werden_mitgespeichert():
    s = basis_stammdaten(gas_zustandszahl=0.9563, gas_brennwert=11.024)
    wieder = from_dict(as_dict(s, standard_positionen()))[0]
    assert wieder.gas_zustandszahl == 0.9563 and wieder.gas_brennwert == 11.024


# --- Hilfe und Suche -------------------------------------------------------

def test_jeder_bereich_hat_eine_erklaerung():
    from nebenkosten import hilfe

    assert set(hilfe.ERKLAERUNGEN) == set(hilfe.BEREICHE)
    for titel, text in hilfe.ERKLAERUNGEN.values():
        assert titel and len(text.strip()) > 80


def test_themen_zeigen_auf_vorhandene_bereiche():
    from nebenkosten import hilfe

    for thema in hilfe.THEMEN:
        assert thema.bereich in hilfe.BEREICHE, thema.titel
        assert thema.wo, thema.titel
        assert thema.woerter, thema.titel


def test_suche_findet_die_richtige_stelle():
    from nebenkosten import hilfe

    def bereiche(begriff):
        return {t.bereich for _, t in hilfe.suche(begriff)}

    assert "kosten" in bereiche("gasrechnung")
    assert "zaehler" in bereiche("gaszähler")
    assert "weitere" in bereiche("co2")
    assert "ergebnis" in bereiche("pdf")
    assert "art" in bereiche("auszug")
    assert "vermieter" in bereiche("iban")
    assert "objekt" in bereiche("personen")
    assert hilfe.suche("") == []
    assert hilfe.suche("xyzabc") == []


def test_suche_findet_eigene_zeilen_und_zaehler():
    from nebenkosten import hilfe

    positionen = standard_positionen()
    treffer = hilfe.suche("außenzapfstelle", positionen)
    assert any(t.bereich == "zaehler" for _, t in treffer)
    assert any("Außenzapfstelle" in t.titel for _, t in treffer)

    treffer = hilfe.suche("niederschlag", positionen)
    assert any(t.bereich == "kosten" for _, t in treffer)


def test_suche_sortiert_genaue_treffer_nach_vorne():
    from nebenkosten import hilfe

    treffer = hilfe.suche("brennwert")
    assert treffer and treffer[0][1].titel == "Zustandszahl und Brennwert"


# --- Prüfung vor dem Abschließen -------------------------------------------

def vollstaendige_daten():
    # Erfundene Angaben. Echte Namen, Anschriften und Kontodaten gehoeren nicht
    # ins Repository, sondern nur in die gespeicherten Daten der laufenden App.
    s = basis_stammdaten(vermieter_name="Max Mustermann", vermieter_plz_ort="12345 Musterstadt",
                         objekt_strasse="Musterweg 1", mieter_name="Familie Beispiel",
                         vermieter_iban="DE02 1203 0000 0000 2020 51")
    positionen = [Position("Grundsteuer", "sonstiges", betrag=421.44),
                  Position("Versicherungen", "sonstiges", betrag=388.12),
                  Position("Müllabfuhr", "sonstiges", betrag=188.0),
                  Position("Niederschlagswasser", "wasser", betrag=135.70),
                  Position("Allgemeinstrom", "sonstiges", betrag=210.0),
                  Position("Schornsteinfeger", "gas", betrag=95.0),
                  Position("Straßenreinigung und Winterdienst", "sonstiges", betrag=120.0),
                  Position("Heizungswartung", "gas", betrag=180.0)]
    return s, positionen


def test_pruefung_meldet_fehlende_pflichtangaben():
    from nebenkosten import hilfe, pruefung

    s = basis_stammdaten(vermieter_name="", mieter_name="", objekt_strasse="",
                         flaeche_gesamt=0.0, flaeche_mieter=0.0)
    positionen = [Position("Grundsteuer", "sonstiges", betrag=500.0)]
    bericht = pruefung.pruefe(s, positionen, berechne(s, positionen))
    fehlt = {p.was for p in bericht.pflicht}
    assert "Dein Name" in fehlt
    assert "Name des Mieters" in fehlt
    assert "Adresse des Hauses" in fehlt
    assert "Wohnfläche des ganzen Hauses" in fehlt
    assert not bericht.vollstaendig
    # jeder Punkt sagt, wo er nachzutragen ist
    assert all(p.bereich in hilfe.BEREICHE
               for p in bericht.pflicht)


def test_pruefung_ist_zufrieden_wenn_alles_da_ist():
    from nebenkosten import pruefung

    s, positionen = vollstaendige_daten()
    bericht = pruefung.pruefe(s, positionen, berechne(s, positionen))
    assert bericht.vollstaendig and not bericht.achtung


def test_pruefung_trennt_muss_von_kann():
    """Fehlende Kostenarten sind kein Grund, die Abrechnung zu blockieren."""
    from nebenkosten import pruefung

    s, positionen = vollstaendige_daten()
    ohne_versicherung = [p for p in positionen if p.bezeichnung != "Versicherungen"]
    bericht = pruefung.pruefe(s, ohne_versicherung, berechne(s, ohne_versicherung))
    assert bericht.vollstaendig                      # PDF bleibt möglich
    assert any("Versicherungen" in p.was for p in bericht.kann)


def test_pruefung_meldet_zeilen_ohne_betrag():
    from nebenkosten import pruefung

    s, positionen = vollstaendige_daten()
    positionen.append(Position("Gartenpflege", "sonstiges", betrag=0.0))
    bericht = pruefung.pruefe(s, positionen, berechne(s, positionen))
    assert any("Gartenpflege" in p.was and "ohne Betrag" in p.warum for p in bericht.kann)


def test_pruefung_warnt_vor_renovierungskosten():
    """Renovierung und Reparatur sind nicht umlagefähig."""
    from nebenkosten import pruefung

    s, positionen = vollstaendige_daten()
    for name in ("Renovierung Treppenhaus", "Reparatur Heizung", "Schönheitsreparaturen"):
        pruefling = positionen + [Position(name, "sonstiges", betrag=800.0)]
        bericht = pruefung.pruefe(s, pruefling, berechne(s, pruefling))
        assert any(name in p.was for p in bericht.achtung), name
        assert bericht.vollstaendig      # blockiert nicht, weist nur hin


def test_pruefung_vermisst_zeilen_aus_dem_vorjahr():
    from nebenkosten import pruefung

    s, positionen = vollstaendige_daten()
    vorjahr = positionen + [Position("Gartenpflege", "sonstiges", betrag=450.0)]
    bericht = pruefung.pruefe(s, positionen, berechne(s, positionen), vorjahr)
    treffer = [p for p in bericht.kann if "Gartenpflege" in p.was]
    assert treffer and "450,00" in treffer[0].warum


def test_pruefung_erinnert_an_die_iban_nur_bei_nachzahlung():
    from nebenkosten import pruefung

    s, positionen = vollstaendige_daten()
    s.vermieter_iban = ""
    s.vorauszahlung_monatlich = 10.0        # zu wenig -> Nachzahlung
    bericht = pruefung.pruefe(s, positionen, berechne(s, positionen))
    assert any("IBAN" in p.was for p in bericht.kann)

    s.vorauszahlung_monatlich = 500.0       # Guthaben -> keine IBAN nötig
    bericht = pruefung.pruefe(s, positionen, berechne(s, positionen))
    assert not any("IBAN" in p.was for p in bericht.kann)


# --- Katalog: was rein darf und was gesperrt ist ---------------------------

def test_jede_kostenart_nennt_ihre_fundstelle():
    from nebenkosten import katalog

    for art in katalog.KATALOG:
        assert art.nummer.startswith("§ 2 Nr."), art.name
        assert art.kategorie in ("wasser", "gas", "sonstiges"), art.name
        assert art.erlaeuterung, art.name
        assert art.schluessel in SCHLUESSEL_ERLAUBT, art.name


SCHLUESSEL_ERLAUBT = {"flaeche", "personen", "einheiten", "verbrauch",
                      "direkt", "direkt_vermieter"}


def test_verbotene_kosten_werden_erkannt():
    from nebenkosten import katalog

    for name in ("Renovierung Treppenhaus", "Reparatur der Heizung",
                 "Schönheitsreparaturen", "Malerarbeiten Flur", "Hausverwaltung",
                 "Kontoführungsgebühren", "Instandhaltungsrücklage", "Mietausfallwagnis",
                 "Anwaltskosten", "Sanierung Bad", "Modernisierung Fenster",
                 "Neuanschaffung Rasenmäher", "Kaution"):
        assert katalog.verboten(name), name


def test_erlaubte_kosten_werden_nicht_gesperrt():
    """Wartung, Pflege und Abrechnungsdienst sind zulässig – trotz ähnlicher Wörter."""
    from nebenkosten import katalog

    for art in katalog.KATALOG:
        assert not katalog.verboten(art.name), art.name
    for name in ("Heizungswartung", "Wartung der Lüftungsanlage", "Baumpflege",
                 "Kosten der Heizkostenabrechnung", "Eichung und Wartung der Wasserzähler",
                 "Gartenpflege", "Ungezieferbekämpfung"):
        assert not katalog.verboten(name), name


def test_katalog_deckt_die_startzeilen_ab():
    from nebenkosten import katalog

    for pos in standard_positionen():
        art = katalog.finde(pos.bezeichnung)
        assert art is not None, pos.bezeichnung
        assert pos.kategorie == art.kategorie
        assert art.nummer in pos.hinweis


def test_uebliche_kostenarten_der_pruefung_gibt_es_wirklich():
    from nebenkosten import katalog, pruefung

    for name in pruefung.UEBLICH:
        assert katalog.finde(name) is not None, name


def test_sonstige_betriebskosten_brauchen_eine_vereinbarung():
    from nebenkosten import katalog

    mit_vertrag = [k for k in katalog.KATALOG if k.vertrag_noetig]
    assert mit_vertrag
    for art in mit_vertrag:
        assert "Nr. 17" in art.nummer, art.name


def test_ohne_hinterlegte_benutzer_bleibt_die_app_offen():
    """Auf dem eigenen Rechner soll keine Anmeldung im Weg stehen."""
    from nebenkosten import zugang

    assert zugang.benutzerliste() == {}    # keine secrets.toml in den Tests


def test_ausweis_gilt_nur_mit_passender_unterschrift():
    from nebenkosten import zugang

    benutzer = {"andreas": "geheim", "claudia": "anders"}
    ausweis = zugang._ausweis_bauen("andreas", benutzer)
    assert zugang._ausweis_pruefen(ausweis, benutzer) == "andreas"

    # Passwort geaendert: alle alten Ausweise sind wertlos.
    assert zugang._ausweis_pruefen(ausweis, {"andreas": "neu", "claudia": "anders"}) == ""
    # Benutzer entfernt.
    assert zugang._ausweis_pruefen(ausweis, {"claudia": "anders"}) == ""
    # Unsinn faellt nicht durch.
    assert zugang._ausweis_pruefen("kaputt", benutzer) == ""
    assert zugang._ausweis_pruefen("", benutzer) == ""


def test_ausweis_laeuft_ab():
    import base64
    import hashlib
    import hmac

    from nebenkosten import zugang

    benutzer = {"andreas": "geheim"}
    nutzlast = "andreas|1"      # 1970, also laengst abgelaufen
    unterschrift = hmac.new(zugang._unterschriftsgeheimnis(benutzer),
                            nutzlast.encode(), hashlib.sha256).hexdigest()[:32]
    alt = base64.urlsafe_b64encode(f"{nutzlast}|{unterschrift}".encode()).decode()
    assert zugang._ausweis_pruefen(alt, benutzer) == ""


def test_ausweis_traegt_kein_passwort():
    """Auf dem Geraet liegt nur ein Ausweis, nicht das Passwort."""
    import base64

    from nebenkosten import zugang

    benutzer = {"andreas": "streng-geheim"}
    klartext = base64.urlsafe_b64decode(
        zugang._ausweis_bauen("andreas", benutzer).encode()).decode()
    assert "streng-geheim" not in klartext


def test_abmelden_raeumt_die_daten_des_benutzers_weg():
    """Sonst saehe der naechste Benutzer auf demselben Geraet die Daten des
    vorigen - in derselben Sitzung wird nichts neu geladen."""
    from nebenkosten import zugang

    class Sitzung(dict):
        pass

    class StreamlitAttrappe:
        def __init__(self):
            self.session_state = Sitzung()

    echt = zugang.st
    zugang.st = StreamlitAttrappe()
    try:
        zugang.st.session_state.update({
            "_benutzer": "andreas", "_ablage_geprueft": "andreas",
            "_ablagegrund": "irgendwas", "stamm": object(), "positionen": [1, 2],
            "bereich": "kosten",
        })
        zugang.abmelden()
        uebrig = set(zugang.st.session_state)
        assert uebrig == {"_abmelden", "bereich"}, uebrig
    finally:
        zugang.st = echt


def test_die_app_laesst_sich_ohne_fehlende_namen_uebersetzen():
    """Faengt Tippfehler und vergessene Importe ab, die erst beim Klicken
    auffallen wuerden - etwa ein fehlendes aus_katalog beim „Hinzufuegen"."""
    import ast
    import builtins
    from pathlib import Path

    wurzel = Path(__file__).resolve().parents[1]
    datei = wurzel / "streamlit_app.py"
    if not datei.exists():                       # in der anderen Ablage anders benannt
        datei = wurzel / "nebenkosten_app.py"
    baum = ast.parse(datei.read_text(encoding="utf-8"))

    bekannt = set(dir(builtins))
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Import):
            bekannt.update((a.asname or a.name.split(".")[0]) for a in knoten.names)
        elif isinstance(knoten, ast.ImportFrom):
            bekannt.update((a.asname or a.name) for a in knoten.names)
        elif isinstance(knoten, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bekannt.add(knoten.name)
        elif isinstance(knoten, ast.Name) and isinstance(knoten.ctx, ast.Store):
            bekannt.add(knoten.id)
        elif isinstance(knoten, ast.arg):
            bekannt.add(knoten.arg)
        elif isinstance(knoten, ast.ExceptHandler) and knoten.name:
            bekannt.add(knoten.name)
        elif isinstance(knoten, (ast.comprehension,)):
            for ziel in ast.walk(knoten.target):
                if isinstance(ziel, ast.Name):
                    bekannt.add(ziel.id)

    unbekannt = {k.id for k in ast.walk(baum)
                 if isinstance(k, ast.Name) and isinstance(k.ctx, ast.Load)
                 and k.id not in bekannt}
    assert not unbekannt, f"nirgends definiert: {sorted(unbekannt)}"


def test_kabelanschluss_ist_seit_juli_2024_nicht_mehr_umlagefaehig():
    """Das Nebenkostenprivileg fuer Kabel und Antenne ist zum 30.06.2024
    entfallen. Wer es danach abrechnet, bekommt vom Mieter Aerger."""
    kabel = Position("Kabelanschluss (bis 30.06.2024)", "sonstiges", betrag=240.0,
                     schluessel="einheiten")

    # Zeitraum komplett danach: Fehler, kein PDF.
    e = berechne(basis_stammdaten(zeitraum_von="2025-01-01", zeitraum_bis="2025-12-31",
                                  nutzung_von="2025-01-01", nutzung_bis="2025-12-31"),
                 [kabel])
    assert any("nicht mehr umlagefähig" in f for f in e.fehler), e.fehler

    # Zeitraum ueber den Stichtag: nur der Teil davor waere erlaubt - Warnung.
    e = berechne(basis_stammdaten(zeitraum_von="2024-01-01", zeitraum_bis="2024-12-31",
                                  nutzung_von="2024-01-01", nutzung_bis="2024-12-31"),
                 [kabel])
    assert not any("nicht mehr umlagefähig" in f for f in e.fehler)
    assert any("höchstens der Teil" in w for w in e.warnungen), e.warnungen

    # Zeitraum komplett davor: in Ordnung.
    e = berechne(basis_stammdaten(zeitraum_von="2023-01-01", zeitraum_bis="2023-12-31",
                                  nutzung_von="2023-01-01", nutzung_bis="2023-12-31"),
                 [kabel])
    assert not e.fehler and not any("umlagefähig" in w for w in e.warnungen)


def test_katalog_deckt_alle_nummern_der_betriebskostenverordnung_ab():
    import re

    from nebenkosten.katalog import KATALOG

    gefunden = set()
    for art in KATALOG:
        treffer = re.search(r"Nr\.\s*(\d+)", art.nummer)
        if treffer:
            gefunden.add(int(treffer.group(1)))
    fehlt = sorted(set(range(1, 18)) - gefunden)
    assert not fehlt, f"§ 2 BetrKV Nr. {fehlt} kommen im Katalog nicht vor"


# --- Heizung: eine Rechnung, zwei Kostenarten ------------------------------

def _heizdaten(**abweichungen):
    from nebenkosten.modell import Stammdaten

    werte = dict(heizart="gas_zentral", brennstoff_kosten=2740.0,
                 brennstoff_menge=2440.0, gas_zustandszahl=0.95, gas_brennwert=10.5,
                 warmwasser_zentral=True, warmwasser_temperatur=60.0)
    werte.update(abweichungen)
    return basis_stammdaten(**werte) if False else Stammdaten(**werte)


def test_gasrechnung_wird_in_heizung_und_warmwasser_geteilt():
    from nebenkosten.heizung import aufteilen

    a = aufteilen(_heizdaten(), 61.271)
    assert round(a.energie_gesamt) == 24339          # 2440 x 0,95 x 10,5
    assert round(a.energie_warmwasser) == 7659       # 2,5 x 61,271 x 50
    assert round(a.kosten_warmwasser + a.kosten_heizung, 2) == 2740.0
    assert round(a.kosten_warmwasser, 2) == 862.21


def test_ohne_warmwasserzaehler_steht_alles_bei_der_heizung():
    from nebenkosten.heizung import aufteilen

    a = aufteilen(_heizdaten(), 0.0)
    assert a.kosten_warmwasser == 0.0
    assert a.kosten_heizung == 2740.0
    assert any("ganze Rechnung" in h for h in a.hinweise)


def test_oel_und_pellets_rechnen_mit_ihrem_eigenen_energiegehalt():
    from nebenkosten.heizung import aufteilen

    oel = aufteilen(_heizdaten(heizart="oel", brennstoff_menge=3000.0), 61.271)
    assert round(oel.energie_gesamt) == 30000        # 3000 l x 10 kWh

    pellets = aufteilen(_heizdaten(heizart="pellets", brennstoff_menge=6000.0), 61.271)
    assert round(pellets.energie_gesamt) == 28800    # 6000 kg x 4,8 kWh


def test_fernwaerme_braucht_keine_umrechnung():
    from nebenkosten.heizung import aufteilen

    a = aufteilen(_heizdaten(heizart="fernwaerme", brennstoff_menge=24339.0), 61.271)
    assert round(a.energie_gesamt) == 24339
    assert not a.rechenweg or "kWh/kWh" not in a.rechenweg[0]


def test_etagenheizung_rechnet_keine_brennstoffkosten_ab():
    """Jede Wohnung hat einen eigenen Vertrag - da laeuft nichts ueber die
    Nebenkosten."""
    from nebenkosten.heizung import aufteilen

    a = aufteilen(_heizdaten(heizart="gas_etage"), 61.271)
    assert a.kosten_heizung == 0.0 and a.kosten_warmwasser == 0.0
    assert a.hinweise


def test_warmwasser_ueber_eigene_anlage_bleibt_bei_der_heizung():
    from nebenkosten.heizung import aufteilen

    a = aufteilen(_heizdaten(warmwasser_zentral=False), 61.271)
    assert a.kosten_warmwasser == 0.0
    assert a.kosten_heizung == 2740.0


def test_zu_viel_warmwasser_wird_gemeldet():
    """Rechnerisch mehr Warmwasser als Gesamtenergie - da stimmt eine Eingabe nicht."""
    from nebenkosten.heizung import aufteilen

    a = aufteilen(_heizdaten(brennstoff_menge=100.0), 200.0)
    assert a.anteil_warmwasser == 1.0
    assert any("mehr Energie" in h for h in a.hinweise)


def test_heizzeilen_stehen_nicht_in_der_kostentabelle():
    """Fuer Warmwasser gibt es keine Rechnung - ein Eingabefeld dafuer verwirrt."""
    from nebenkosten.modell import standard_positionen

    berechnet = [p.bezeichnung for p in standard_positionen() if p.berechnet]
    assert sorted(berechnet) == ["Heizung (Gas)", "Warmwasser (Gas)"]


def test_wohnung_kann_eine_eigene_anschrift_haben():
    """Der Anbau hat die 27a, das Haus die 27 - im PDF muss die Wohnung stehen."""
    s = basis_stammdaten(objekt_strasse="Raiffeisenring 27",
                         objekt_plz_ort="66903 Gries")
    assert s.wohnung_anschrift == ("Raiffeisenring 27", "66903 Gries")

    s = basis_stammdaten(objekt_strasse="Raiffeisenring 27", objekt_plz_ort="66903 Gries",
                         wohnung_strasse="Raiffeisenring 27a")
    assert s.wohnung_anschrift == ("Raiffeisenring 27a", "66903 Gries")

    s = basis_stammdaten(objekt_strasse="Raiffeisenring 27", objekt_plz_ort="66903 Gries",
                         wohnung_strasse="Nebenweg 3", wohnung_plz_ort="66903 Gries-Nord")
    assert s.wohnung_anschrift == ("Nebenweg 3", "66903 Gries-Nord")


def test_pdf_zeigt_die_anschrift_der_wohnung():
    from nebenkosten.berechnung import berechne
    from nebenkosten.pdf import erzeuge_pdf

    s = basis_stammdaten(objekt_strasse="Raiffeisenring 27", objekt_plz_ort="66903 Gries",
                         wohnung_strasse="Raiffeisenring 27a")
    positionen = [Position("Grundsteuer", "sonstiges", betrag=400.0)]
    daten = erzeuge_pdf(s, berechne(s, positionen))
    assert daten[:4] == b"%PDF"
    assert len(daten) > 1000


def test_eigene_wohnungsanschrift_ueberlebt_das_zuruecksetzen():
    from nebenkosten.modell import neue_abrechnung

    s = basis_stammdaten(wohnung_strasse="Raiffeisenring 27a", wohnung_plz_ort="66903 Gries")
    frisch = neue_abrechnung(s)
    assert frisch.wohnung_strasse == "Raiffeisenring 27a"
    assert frisch.wohnung_plz_ort == "66903 Gries"


def test_kein_test_verdeckt_einen_anderen():
    """Zwei Tests mit demselben Namen: Der zweite verdeckt den ersten, und der
    laeuft ab da nie wieder - ohne dass irgendwo etwas rot wird."""
    import ast
    from collections import Counter
    from pathlib import Path

    baum = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    namen = Counter(k.name for k in baum.body
                    if isinstance(k, ast.FunctionDef) and k.name.startswith("test_"))
    doppelt = sorted(name for name, anzahl in namen.items() if anzahl > 1)
    assert not doppelt, f"doppelt vergeben: {doppelt}"


def test_nur_die_brennstoffzeilen_werden_berechnet():
    """„Heizungswartung" faengt mit „Heizung" an, ist aber eine eigene Rechnung
    des Heizungsbauers. Wird sie als berechnet eingestuft, verschwindet sie aus
    der Kostentabelle und bekommt obendrein den Betrag der Gasrechnung - die
    Heizkosten stuenden dann zweimal in der Abrechnung."""
    from nebenkosten.modell import brennstoffzeile

    assert brennstoffzeile("Heizung (Gas)") == "heizung"
    assert brennstoffzeile("Heizung (Öl)") == "heizung"
    assert brennstoffzeile("Fernwärme") == "heizung"
    assert brennstoffzeile("Verbundene Heizungs- und Warmwasseranlage") == "heizung"
    assert brennstoffzeile("Warmwasser (Gas)") == "warmwasser"
    assert brennstoffzeile("Warmwasser (Strom, Boiler)") == "warmwasser"

    for eigene_rechnung in ("Heizungswartung", "Wartung der Etagenheizung",
                            "Wartung der verbundenen Anlage", "Schornsteinfeger",
                            "Betriebsstrom der Heizung", "Miete und Eichung der Wärmezähler",
                            "Reinigung der Heizanlage und des Heizraums",
                            "Kosten der Heizkostenabrechnung"):
        assert brennstoffzeile(eigene_rechnung) == "", eigene_rechnung


def test_heizungswartung_bleibt_in_der_kostentabelle():
    """Auch nach dem Laden gespeicherter Daten."""
    from nebenkosten.modell import Stammdaten, as_dict, from_dict, standard_positionen

    _, positionen = from_dict(as_dict(Stammdaten(), standard_positionen()))
    nach_name = {p.bezeichnung: p for p in positionen}
    assert nach_name["Heizungswartung"].berechnet is False
    assert nach_name["Schornsteinfeger"].berechnet is False
    assert nach_name["Heizung (Gas)"].berechnet is True
    assert nach_name["Warmwasser (Gas)"].berechnet is True


def test_falsch_gekennzeichnete_zeile_wird_beim_laden_repariert():
    """Wer die App zwischendurch benutzt hat, hat den Fehler gespeichert."""
    from nebenkosten.modell import from_dict

    daten = {
        "stammdaten": {},
        "positionen": [
            {"bezeichnung": "Heizungswartung", "kategorie": "gas", "betrag": 180.0,
             "berechnet": True},
            {"bezeichnung": "Heizung (Gas)", "kategorie": "gas", "berechnet": True},
        ],
    }
    _, positionen = from_dict(daten)
    nach_name = {p.bezeichnung: p for p in positionen}
    assert nach_name["Heizungswartung"].berechnet is False
    assert nach_name["Heizungswartung"].betrag == 180.0
    assert nach_name["Heizung (Gas)"].berechnet is True


def test_faelschlich_abgeschaltete_zeile_kommt_zurueck():
    """Die App hatte solchen Zeilen den Betrag der Brennstoffrechnung zugewiesen
    und sie abgeschaltet, wenn der 0 war. Sonst bliebe die Wartung unsichtbar."""
    from nebenkosten.modell import from_dict

    daten = {"stammdaten": {}, "positionen": [
        {"bezeichnung": "Heizungswartung", "kategorie": "gas", "betrag": 0.0,
         "aktiv": False, "berechnet": True},
        {"bezeichnung": "Gartenpflege", "kategorie": "sonstiges", "betrag": 0.0,
         "aktiv": False, "berechnet": False},
    ]}
    _, positionen = from_dict(daten)
    nach_name = {p.bezeichnung: p for p in positionen}
    assert nach_name["Heizungswartung"].aktiv is True
    # Von Hand abgewaehlte Zeilen bleiben aus.
    assert nach_name["Gartenpflege"].aktiv is False


def test_etappe_wird_erst_gruen_wenn_sie_fertig_ist():
    """Ein einziger eingetragener Betrag darf nicht die ganze Sparte gruen
    faerben - sonst haelt man eine halb ausgefuellte Abrechnung fuer fertig."""
    from nebenkosten import pruefung
    from nebenkosten.modell import standard_positionen

    s = basis_stammdaten(vermieter_name="Andreas", vermieter_strasse="",
                         vermieter_plz_ort="", vermieter_iban="")
    positionen = standard_positionen()
    positionen[0].betrag = 10.0
    nach_name = {name: (a, b) for name, a, b, _ in pruefung.etappen(s, positionen)}

    erledigt, gesamt = nach_name["Kosten"]
    assert 0 < erledigt < gesamt, "eine von vielen Zeilen ist nicht fertig"
    erledigt, gesamt = nach_name["Vermieter"]
    assert 0 < erledigt < gesamt, "ohne Anschrift und IBAN ist es nicht fertig"
    assert nach_name["Zählerstände"][0] == 0, "kein Zaehler eingetragen"


def test_etappe_ist_gruen_wenn_wirklich_alles_steht():
    from nebenkosten import pruefung
    from nebenkosten.modell import standard_positionen

    s = basis_stammdaten(
        vermieter_name="A", vermieter_strasse="Weg 1", vermieter_plz_ort="12345 Ort",
        vermieter_iban="DE02 1203 0000 0000 2020 51", objekt_strasse="Weg 1",
        flaeche_gesamt=245.0, personen_gesamt=4.0, mieter_name="B",
        mieter_wohnung="Obergeschoss", flaeche_mieter=91.0, personen_mieter=2.0,
        vorauszahlung_monatlich=200.0, vorauszahlung_monate=12)
    positionen = [p for p in standard_positionen() if not p.berechnet]
    for p in positionen:
        p.betrag = 100.0
        for z in p.zaehler:
            z.alt, z.neu = 100.0, 200.0
    nach_name = {name: (a, b) for name, a, b, _ in pruefung.etappen(s, positionen)}
    for name, (erledigt, gesamt) in nach_name.items():
        assert erledigt >= gesamt, f"{name} sollte fertig sein: {erledigt}/{gesamt}"


def test_fremdes_manifest_wird_verdraengt():
    """Der Betreiber haengt ein eigenes Manifest in die Seite. Frueher gab das
    Skript an der Stelle auf - der Browser nahm dann dessen Symbol und Namen
    fuer den Startbildschirm, also das rote Streamlit-Zeichen."""
    import inspect

    from nebenkosten import design

    quelle = inspect.getsource(design._startbildschirm)
    assert "link#nk-manifest" in quelle, "ohne eigene Kennung wird doppelt eingehaengt"
    assert "querySelectorAll('link[rel=\"manifest\"]')" in quelle
    assert "fremd.remove()" in quelle
    assert "id: 'nk-manifest'" in quelle
    # Der alte Abbruch darf nicht zurueckkommen.
    assert "kopf.querySelector('link[rel=\"manifest\"]')) return" not in quelle


if __name__ == "__main__":
    fehlgeschlagen = 0
    for name, funktion in sorted(globals().items()):
        if name.startswith("test_") and callable(funktion):
            try:
                funktion()
                print(f"  ok   {name}")
            except AssertionError as fehler:
                fehlgeschlagen += 1
                print(f"  FAIL {name}: {fehler}")
    print("Alle Tests bestanden." if not fehlgeschlagen else f"{fehlgeschlagen} Test(s) fehlgeschlagen.")
    sys.exit(1 if fehlgeschlagen else 0)

def test_nur_der_kopf_baustein_wird_flach_gezogen():
    """Die Regel, die den unsichtbaren Kopf-Baustein auf Höhe null zieht, galt
    einmal für jeden eingebetteten Rahmen. Alles andere in einem Rahmen wäre
    damit unsichtbar - das hat schon einen Anlauf gekostet."""
    import inspect

    from nebenkosten import design

    stil = design._stil()
    for zeile in stil.splitlines():
        if '[data-testid="stIFrame"]' in zeile and "height: 0" in zeile:
            assert zeile.lstrip().startswith(".st-key-nk-startbildschirm"), (
                "die Regel gilt wieder für alle Rahmen - eingebettete "
                f"Inhalte wären unsichtbar: {zeile}")
    assert '.st-key-nk-startbildschirm [data-testid="stIFrame"]' in stil
    quelle = inspect.getsource(design._startbildschirm)
    assert 'st.container(key="nk-startbildschirm")' in quelle


def test_stand_wird_angezeigt():
    """Ohne sichtbaren Stand lässt sich vom Handy aus nicht sagen, ob der
    Betreiber die neue Fassung schon ausliefert."""
    from nebenkosten import design

    assert design.STAND
    quelle = Path(__file__).resolve().parents[1] / "nebenkosten_app.py"
    if not quelle.exists():
        quelle = Path(__file__).resolve().parents[1] / "streamlit_app.py"
    assert "design.STAND" in quelle.read_text(encoding="utf-8")

def test_eintrag_geht_bis_zur_obersten_seite():
    """Der Betreiber steckt die App in einen weiteren Rahmen (bei Streamlit
    Cloud unter /~/+/). Der Browser holt Symbol und Namen von der obersten
    Seite. Wer nur eine Ebene hochgeht, schreibt in einen Rahmen, den für die
    Verknüpfung niemand ansieht - genau das war der Fehler."""
    import inspect

    from nebenkosten import design

    quelle = inspect.getsource(design)
    assert "window.parent.document" not in quelle, (
        "eine Ebene hoch reicht nicht - der Eintrag landet im falschen Rahmen")
    fuer_kopf = inspect.getsource(design._startbildschirm)
    assert "function obersteSeite()" in fuer_kopf
    assert "fenster !== window.top" in fuer_kopf
    assert "seite.document.head" in fuer_kopf
    assert "seite.location" in fuer_kopf


def test_name_der_obersten_seite_wird_gesetzt():
    """Der Name unter dem Symbol kommt vom Titel der obersten Seite; beim
    Betreiber heißt die 'Streamlit'. set_page_config erreicht nur den Rahmen
    darin."""
    import inspect

    from nebenkosten import design

    quelle = inspect.getsource(design._startbildschirm)
    assert "seite.document.title = 'Nebenkosten'" in quelle
    assert "setInterval(namen" in quelle
