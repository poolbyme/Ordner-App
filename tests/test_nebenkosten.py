"""Tests für die Nebenkostenabrechnung: python -m pytest tests/ (oder direkt ausführen)."""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nebenkosten.berechnung import berechne, eur, tage  # noqa: E402
from nebenkosten.modell import (  # noqa: E402
    Position, Stammdaten, as_dict, from_dict, standard_positionen,
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
    pos = Position("Wasser", betrag=600.0, schluessel="verbrauch",
                   verbrauch_gesamt=200.0, verbrauch_mieter=50.0, einheit="m³")
    e = berechne(basis_stammdaten(), [pos])
    assert e.summe_anteil == 150.0


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
