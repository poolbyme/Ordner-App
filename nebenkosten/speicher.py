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


def _schreiben(ziel: Path, daten: dict) -> Path:
    ziel.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(daten, ensure_ascii=False, indent=2)
    # Erst in eine Nebendatei schreiben, dann umbenennen: so bleibt bei einem
    # Absturz mitten im Schreiben die alte Fassung erhalten.
    vorlaeufig = ziel.with_suffix(ziel.suffix + ".tmp")
    vorlaeufig.write_text(text, encoding="utf-8")
    vorlaeufig.replace(ziel)
    return ziel


def speichern(stammdaten: Stammdaten, positionen: list[Position]) -> Path:
    """Aktuellen Stand sichern (wird von der App nach jeder Eingabe aufgerufen)."""
    return _schreiben(AKTUELL, as_dict(stammdaten, positionen))


def laden() -> tuple[Stammdaten, list[Position]] | None:
    """Gespeicherten Stand lesen; None, wenn es noch keinen gibt."""
    if not AKTUELL.exists():
        return None
    try:
        return from_dict(json.loads(AKTUELL.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return None


def gespeichert_am() -> datetime | None:
    if not AKTUELL.exists():
        return None
    return datetime.fromtimestamp(AKTUELL.stat().st_mtime)


def _dateiname(stammdaten: Stammdaten) -> str:
    from .berechnung import parse_datum  # lokal, um Ringimporte zu vermeiden

    jahr = (parse_datum(stammdaten.zeitraum_bis) or datetime.today().date()).year
    name = "".join(c for c in stammdaten.mieter_name if c.isalnum() or c in " -_").strip()
    name = name.replace(" ", "_") or "Mieter"
    art = "Mietende" if stammdaten.ist_endabrechnung else "Jahresabrechnung"
    return f"{jahr}_{name}_{art}.json"


def archivieren(stammdaten: Stammdaten, positionen: list[Position]) -> Path:
    """Fertige Abrechnung zusätzlich unter Jahr und Mietername ablegen."""
    return _schreiben(ARCHIV / _dateiname(stammdaten), as_dict(stammdaten, positionen))


def archiv() -> list[Path]:
    """Abgelegte Abrechnungen, neueste zuerst."""
    if not ARCHIV.exists():
        return []
    return sorted(ARCHIV.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def aus_archiv(datei: Path) -> tuple[Stammdaten, list[Position]] | None:
    try:
        return from_dict(json.loads(Path(datei).read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return None
