"""Dauerhaftes Speichern der Abrechnungsdaten in einer Datei.

Die Daten liegen als JSON im Ordner `daten/` neben der App – lesbar, kopierbar,
sicherbar. Der Ordner lässt sich über die Umgebungsvariable NEBENKOSTEN_DATEN
verlegen (z. B. in einen Cloud-Ordner, der automatisch synchronisiert wird).
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from .modell import Position, Stammdaten, as_dict, from_dict

ORDNER = Path(os.environ.get("NEBENKOSTEN_DATEN")
              or Path(__file__).resolve().parents[1] / "daten")
AKTUELL = ORDNER / "abrechnung.json"
ARCHIV = ORDNER / "archiv"

# Optionale Ablage außerhalb des Dateisystems (z. B. Google-Tabelle).
_ablage = None


def konfiguriere(ablage) -> None:
    """Eine andere Ablage benutzen. None schaltet zurück auf Dateien."""
    global _ablage
    _ablage = ablage


def beschreibung() -> str:
    """Wo die Daten liegen – für die Anzeige in der App."""
    if _ablage is not None:
        return getattr(_ablage, "beschreibung", "externe Ablage")
    return "Datei auf diesem Gerät"


def adresse() -> str:
    if _ablage is not None:
        return getattr(_ablage, "adresse", "")
    return str(AKTUELL)


def _schreiben(ziel: Path, daten: dict) -> Path:
    ziel.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(daten, ensure_ascii=False, indent=2)
    # Erst in eine Nebendatei schreiben, dann umbenennen: so bleibt bei einem
    # Absturz mitten im Schreiben die alte Fassung erhalten.
    vorlaeufig = ziel.with_suffix(ziel.suffix + ".tmp")
    vorlaeufig.write_text(text, encoding="utf-8")
    vorlaeufig.replace(ziel)
    return ziel


def speichern(stammdaten: Stammdaten, positionen: list[Position]):
    """Aktuellen Stand sichern (wird von der App nach jeder Eingabe aufgerufen)."""
    daten = as_dict(stammdaten, positionen)
    if _ablage is not None:
        _ablage.schreiben("aktuell", daten)
        return adresse()
    return _schreiben(AKTUELL, daten)


def laden() -> tuple[Stammdaten, list[Position]] | None:
    """Gespeicherten Stand lesen; None, wenn es noch keinen gibt."""
    if _ablage is not None:
        daten = _ablage.lesen("aktuell")
        return from_dict(daten) if daten else None
    if not AKTUELL.exists():
        return None
    try:
        return from_dict(json.loads(AKTUELL.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return None


def gespeichert_am() -> datetime | None:
    if _ablage is not None:
        return _ablage.zeitpunkt("aktuell")
    if not AKTUELL.exists():
        return None
    return datetime.fromtimestamp(AKTUELL.stat().st_mtime)


def _dateiname(stammdaten: Stammdaten) -> str:
    from .berechnung import parse_datum  # lokal, um Ringimporte zu vermeiden

    jahr = (parse_datum(stammdaten.zeitraum_bis) or datetime.today().date()).year
    name = "".join(c for c in stammdaten.mieter_name if c.isalnum() or c in " -_").strip()
    name = name.replace(" ", "_") or "Mieter"
    art = stammdaten.bezeichnung_abrechnung.replace(" ", "-")
    return f"{jahr}_{name}_{art}.json"


def archivieren(stammdaten: Stammdaten, positionen: list[Position]):
    """Fertige Abrechnung zusätzlich unter Jahr und Mietername ablegen."""
    name = _dateiname(stammdaten)
    daten = as_dict(stammdaten, positionen)
    if _ablage is not None:
        _ablage.schreiben(name, daten)
        return name
    return _schreiben(ARCHIV / name, daten)


def archiv() -> list:
    """Abgelegte Abrechnungen, neueste zuerst."""
    if _ablage is not None:
        return list(reversed(_ablage.schluessel()))
    if not ARCHIV.exists():
        return []
    return sorted(ARCHIV.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def archivname(eintrag) -> str:
    """Anzeigename eines Archiveintrags – egal ob Datei oder Tabellenzeile."""
    name = eintrag.stem if isinstance(eintrag, Path) else str(eintrag)
    return name.removesuffix(".json").replace("_", " ")


def vorjahr(stammdaten: Stammdaten):
    """Die abgelegte Abrechnung des Vorjahres, falls es eine gibt."""
    from .berechnung import parse_datum

    bis = parse_datum(stammdaten.zeitraum_bis)
    if not bis:
        return None
    gesucht = bis.year - 1
    for eintrag in archiv():
        geladen = aus_archiv(eintrag)
        if not geladen:
            continue
        alt_bis = parse_datum(geladen[0].zeitraum_bis)
        if alt_bis and alt_bis.year == gesucht:
            return geladen
    return None


def aus_archiv(eintrag) -> tuple[Stammdaten, list[Position]] | None:
    if _ablage is not None:
        daten = _ablage.lesen(str(eintrag))
        return from_dict(daten) if daten else None
    try:
        return from_dict(json.loads(Path(eintrag).read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return None
