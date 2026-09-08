"""Benutzerkonten: eigener Name, eigenes Passwort, eigene oder geteilte Daten.

Früher standen Benutzer und Passwörter in den Streamlit-Einstellungen. Das
heißt: Nur wer an die Einstellungsseite herankommt, kann ein Passwort ändern –
und dort steht es im Klartext. Beides taugt nicht, sobald sich jemand seinen
Zugang selbst vergeben soll.

Hier liegen die Konten deshalb in der Ablage (Google-Tabelle oder Datei) und
das Passwort **nie im Klartext**, sondern nur als Prüfsumme aus `hashlib.scrypt`
– mit Zufallssalz, absichtlich langsam zu berechnen. Aus der Prüfsumme lässt
sich das Passwort nicht zurückrechnen.

Jedes Konto merkt sich, **welches Arbeitsblatt** ihm gehört. Damit hängen Daten
und Name nicht mehr aneinander: Ein Konto lässt sich umbenennen, ohne dass die
Abrechnung verschwindet, und zwei Personen (etwa Eheleute) können dasselbe
Blatt teilen und trotzdem jeder ein eigenes Passwort haben.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from .cloud import BLATT

# Absichtlich teuer: So bringt eine gestohlene Prüfsumme dem Dieb wenig.
# n=2**14 braucht rund 16 MB Speicher und einen Sekundenbruchteil.
_N, _R, _P = 2**14, 8, 1
_LAENGE = 32

NAME_MUSTER = re.compile(r"^[a-z0-9][a-z0-9._-]{1,30}$")
MINDESTLAENGE = 8

ORDNER = Path(os.environ.get("NEBENKOSTEN_DATEN")
              or Path(__file__).resolve().parents[1] / "daten")
DATEI = ORDNER / "benutzer.json"


@dataclass
class Konto:
    """Ein Zugang. `blatt` ist die Ablage, die zu ihm gehört."""

    name: str
    passwort: str = ""          # Prüfsumme, nie das Passwort selbst
    blatt: str = BLATT
    wechseln: str = ""          # "ja" = beim nächsten Anmelden neues vergeben
    geaendert: str = field(default_factory=
                           lambda: datetime.now().isoformat(timespec="seconds"))

    @property
    def muss_wechseln(self) -> bool:
        return str(self.wechseln).strip().lower() in ("ja", "true", "1")


# --- Passwörter ------------------------------------------------------------

def verschluesseln(passwort: str) -> str:
    """Prüfsumme mit frischem Zufallssalz."""
    salz = os.urandom(16)
    roh = hashlib.scrypt(passwort.encode("utf-8"), salt=salz,
                         n=_N, r=_R, p=_P, dklen=_LAENGE)
    return "scrypt${}${}${}${}${}".format(
        _N, _R, _P,
        base64.b64encode(salz).decode("ascii"),
        base64.b64encode(roh).decode("ascii"))


def stimmt(passwort: str, pruefsumme: str) -> bool:
    """Passt das Passwort zur Prüfsumme? Vergleich ohne Zeitverrat."""
    try:
        art, n, r, p, salz, erwartet = pruefsumme.split("$")
        if art != "scrypt":
            return False
        roh = hashlib.scrypt(passwort.encode("utf-8"),
                             salt=base64.b64decode(salz),
                             n=int(n), r=int(r), p=int(p),
                             dklen=len(base64.b64decode(erwartet)))
    except Exception:  # noqa: BLE001 – alles Unlesbare gilt als falsch
        return False
    return hmac.compare_digest(base64.b64encode(roh).decode("ascii"), erwartet)


def passwort_pruefen(passwort: str) -> str:
    """Leerer Text, wenn das Passwort taugt – sonst der Grund im Klartext."""
    if len(passwort) < MINDESTLAENGE:
        return f"Das Passwort braucht mindestens {MINDESTLAENGE} Zeichen."
    if passwort.strip() != passwort:
        return "Am Anfang oder Ende darf kein Leerzeichen stehen."
    return ""


def name_pruefen(name: str) -> str:
    """Leerer Text, wenn der Name taugt – sonst der Grund im Klartext."""
    if not NAME_MUSTER.match(name or ""):
        return ("Der Benutzername braucht 2 bis 31 Zeichen: Kleinbuchstaben, "
                "Ziffern, Punkt, Strich oder Unterstrich – ohne Leerzeichen "
                "und ohne Umlaute.")
    return ""


def blattname(name: str) -> str:
    """Eigenes Arbeitsblatt für einen neuen Zugang."""
    sauber = "".join(c for c in name.strip().lower() if c.isalnum() or c in "-_")
    return f"{BLATT}-{sauber}" if sauber else BLATT


# --- Ablage ----------------------------------------------------------------

_ablage = None


def konfiguriere(ablage) -> None:
    """Eine andere Ablage benutzen. None schaltet zurück auf die Datei."""
    global _ablage
    _ablage = ablage


def beschreibung() -> str:
    if _ablage is not None:
        return getattr(_ablage, "beschreibung", "externe Ablage")
    return "Datei auf diesem Gerät"


def _lesen_roh() -> list[dict]:
    if _ablage is not None:
        return list(_ablage.lesen())
    if not DATEI.exists():
        return []
    try:
        inhalt = json.loads(DATEI.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return list(inhalt) if isinstance(inhalt, list) else []


def _schreiben_roh(konten: list[dict]) -> None:
    if _ablage is not None:
        _ablage.schreiben(konten)
        return
    DATEI.parent.mkdir(parents=True, exist_ok=True)
    vorlaeufig = DATEI.with_suffix(".tmp")
    vorlaeufig.write_text(json.dumps(konten, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    vorlaeufig.replace(DATEI)


# --- Schnittstelle ---------------------------------------------------------

def alle() -> list[Konto]:
    gefunden = []
    for eintrag in _lesen_roh():
        name = str(eintrag.get("name", "")).strip().lower()
        if not name:
            continue
        gefunden.append(Konto(
            name=name,
            passwort=str(eintrag.get("passwort", "")),
            blatt=str(eintrag.get("blatt") or BLATT),
            wechseln=str(eintrag.get("wechseln", "")),
            geaendert=str(eintrag.get("geaendert", "")),
        ))
    return gefunden


def _sichern(konten: list[Konto]) -> None:
    _schreiben_roh([asdict(k) for k in konten])


def finden(name: str) -> Konto | None:
    gesucht = (name or "").strip().lower()
    for konto in alle():
        if konto.name == gesucht:
            return konto
    return None


def leer() -> bool:
    """Noch gar kein Konto angelegt – dann steht die Erstanmeldung an."""
    return not alle()


def pruefen(name: str, passwort: str) -> Konto | None:
    konto = finden(name)
    if konto and konto.passwort and stimmt(passwort, konto.passwort):
        return konto
    return None


def anlegen(name: str, passwort: str, blatt: str = "",
            wechseln: bool = False) -> Konto:
    name = (name or "").strip().lower()
    if finden(name):
        raise ValueError("Diesen Benutzernamen gibt es schon.")
    konto = Konto(name=name, passwort=verschluesseln(passwort),
                  blatt=blatt or blattname(name),
                  wechseln="ja" if wechseln else "")
    bestand = alle()
    bestand.append(konto)
    _sichern(bestand)
    return konto


def passwort_setzen(name: str, passwort: str) -> None:
    bestand = alle()
    gesucht = (name or "").strip().lower()
    for konto in bestand:
        if konto.name == gesucht:
            konto.passwort = verschluesseln(passwort)
            konto.wechseln = ""
            konto.geaendert = datetime.now().isoformat(timespec="seconds")
            _sichern(bestand)
            return
    raise ValueError("Diesen Benutzer gibt es nicht.")


def umbenennen(alt: str, neu: str) -> None:
    """Nur den Namen ändern – das Arbeitsblatt bleibt.

    Genau darum steht das Blatt im Konto: Früher hing es am Namen, und ein
    neuer Name führte in eine leere Abrechnung.
    """
    alt = (alt or "").strip().lower()
    neu = (neu or "").strip().lower()
    if alt == neu:
        return
    if finden(neu):
        raise ValueError("Diesen Benutzernamen gibt es schon.")
    bestand = alle()
    for konto in bestand:
        if konto.name == alt:
            konto.name = neu
            konto.geaendert = datetime.now().isoformat(timespec="seconds")
            _sichern(bestand)
            return
    raise ValueError("Diesen Benutzer gibt es nicht.")


def loeschen(name: str) -> None:
    gesucht = (name or "").strip().lower()
    vorher = alle()
    bestand = [k for k in vorher if k.name != gesucht]
    if len(bestand) == len(vorher):
        raise ValueError("Diesen Benutzer gibt es nicht.")
    if not bestand:
        raise ValueError("Der letzte Zugang lässt sich nicht löschen.")
    _sichern(bestand)
