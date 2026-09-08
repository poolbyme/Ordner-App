"""Anmeldung mit Benutzername und Passwort.

Ohne hinterlegte Zugangsdaten ist die App frei zugänglich – richtig, solange sie
nur auf dem eigenen Rechner läuft. Sobald sie im Internet steht, gehören die
Benutzer in die Secrets:

    [benutzer]
    andreas = "einGutesWort"
    claudia = "einAnderes"

Die alte Schreibweise mit einer einzigen Zeile funktioniert weiter:

    passwort = "einGutesWort"

Dann heißt der Benutzer „vermieter“.

**Angemeldet bleiben.** Wer das Häkchen setzt, bekommt einen Ausweis als Cookie,
der 60 Tage gilt. Er trägt nur den Benutzernamen, das Ablaufdatum und eine
Unterschrift – kein Passwort. Die Unterschrift entsteht aus den hinterlegten
Passwörtern: Wird eines geändert, sind alle alten Ausweise sofort wertlos.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time

import streamlit as st

COOKIE = "nk_ausweis"
GUELTIG_TAGE = 60
STANDARDBENUTZER = "vermieter"


# --- hinterlegte Zugangsdaten ---------------------------------------------

def benutzerliste() -> dict[str, str]:
    """Alle hinterlegten Benutzer mit ihrem Passwort."""
    try:
        tabelle = st.secrets.get("benutzer")
        if tabelle:
            return {str(name).strip().lower(): str(wort)
                    for name, wort in dict(tabelle).items() if str(wort)}
        einzeln = str(st.secrets.get("passwort") or "")
        return {STANDARDBENUTZER: einzeln} if einzeln else {}
    except Exception:  # noqa: BLE001 – ohne secrets.toml wirft st.secrets
        return {}


def _unterschriftsgeheimnis(benutzer: dict[str, str]) -> bytes:
    """Schlüssel für die Unterschrift auf dem Ausweis.

    Er hängt an den Passwörtern: Ändert sich eines, passt keine alte
    Unterschrift mehr und alle Geräte müssen sich neu anmelden.
    """
    zusatz = ""
    try:
        zusatz = str(st.secrets.get("cookie_geheimnis") or "")
    except Exception:  # noqa: BLE001
        pass
    roh = zusatz + "|" + "|".join(f"{n}:{w}" for n, w in sorted(benutzer.items()))
    return hashlib.sha256(roh.encode("utf-8")).digest()


# --- Ausweis (Cookie) ------------------------------------------------------

def _ausweis_bauen(name: str, benutzer: dict[str, str]) -> str:
    ablauf = int(time.time()) + GUELTIG_TAGE * 24 * 3600
    nutzlast = f"{name}|{ablauf}"
    unterschrift = hmac.new(_unterschriftsgeheimnis(benutzer),
                            nutzlast.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    roh = f"{nutzlast}|{unterschrift}".encode("utf-8")
    return base64.urlsafe_b64encode(roh).decode("ascii")


def _ausweis_pruefen(wert: str, benutzer: dict[str, str]) -> str:
    """Benutzername, wenn der Ausweis gültig ist – sonst leer."""
    try:
        name, ablauf, unterschrift = base64.urlsafe_b64decode(
            wert.encode("ascii")).decode("utf-8").split("|")
    except Exception:  # noqa: BLE001 – alles Unlesbare gilt als ungültig
        return ""
    if name not in benutzer or int(ablauf) < time.time():
        return ""
    erwartet = hmac.new(_unterschriftsgeheimnis(benutzer),
                        f"{name}|{ablauf}".encode("utf-8"),
                        hashlib.sha256).hexdigest()[:32]
    return name if hmac.compare_digest(unterschrift, erwartet) else ""


def _cookie_lesen() -> str:
    try:
        return str(st.context.cookies.get(COOKIE) or "")
    except Exception:  # noqa: BLE001 – ältere Streamlit-Fassungen
        return ""


def _cookie_schreiben(wert: str, tage: int) -> None:
    """Cookie im Browser setzen. Leerer Wert plus 0 Tage löscht ihn.

    Streamlit kann Cookies nur lesen, nicht setzen. Deshalb erledigt das ein
    kurzes Skript in einem Rahmen, das in die umgebende Seite schreibt.
    """
    baustein = getattr(st, "iframe", None)
    hoehe = 1
    if baustein is None:  # pragma: no cover – ältere Streamlit-Fassungen
        hoehe = 0
        try:
            from streamlit.components.v1 import html as baustein
        except ImportError:
            return
    sicher = "".join(c for c in wert if c.isalnum() or c in "-_=")
    baustein(
        f"""
<script>
(function () {{
  const alter = {tage * 24 * 3600};
  window.parent.document.cookie =
    "{COOKIE}=" + "{sicher}" + "; path=/; max-age=" + alter + "; SameSite=Lax";
}})();
</script>
""",
        height=hoehe,
    )


# --- Anmeldung -------------------------------------------------------------

def angemeldet_als() -> str:
    return str(st.session_state.get("_benutzer") or "")


def abmelden() -> None:
    """Abmelden und alles vergessen, was zu diesem Benutzer gehoert.

    Ohne das Leeren saehe der naechste Benutzer auf demselben Geraet noch die
    Daten des vorigen - in derselben Sitzung wird nichts neu geladen.
    """
    for schluessel in ("_benutzer", "_ablage_geprueft", "_ablagegrund",
                       "stamm", "positionen"):
        st.session_state.pop(schluessel, None)
    st.session_state["_abmelden"] = True


def _maske(benutzer: dict[str, str]) -> None:
    from . import design

    design.kopfzeile("Nebenkostenabrechnung", "Bitte anmelden")
    mehrere = len(benutzer) > 1
    with st.form("anmeldung"):
        if mehrere:
            name = st.text_input("Benutzername", key="anm_name").strip().lower()
        else:
            name = next(iter(benutzer))
            st.caption(f"Angemeldet wird als **{name}**.")
        wort = st.text_input("Passwort", type="password", key="anm_wort")
        merken = st.checkbox("Auf diesem Gerät angemeldet bleiben", value=True,
                             help=f"Gilt {GUELTIG_TAGE} Tage. Gespeichert wird nur ein "
                                  "Ausweis für dieses Gerät, nicht dein Passwort.")
        abgeschickt = st.form_submit_button("Anmelden", type="primary", width="stretch")

    if abgeschickt:
        hinterlegt = benutzer.get(name, "")
        if hinterlegt and hmac.compare_digest(wort, hinterlegt):
            st.session_state["_benutzer"] = name
            if merken:
                st.session_state["_ausweis_setzen"] = _ausweis_bauen(name, benutzer)
            st.rerun()
        else:
            st.error("Benutzername oder Passwort stimmt nicht."
                     if mehrere else "Das Passwort stimmt nicht.")
    st.stop()


def pruefen() -> None:
    """Hält die App an, bis jemand angemeldet ist."""
    benutzer = benutzerliste()
    if not benutzer:
        st.session_state.setdefault("_benutzer", STANDARDBENUTZER)
        return

    # Aufträge aus dem letzten Durchlauf zuerst ausführen: Ein Cookie lässt sich
    # nur setzen, während die Seite gezeichnet wird.
    ausweis = st.session_state.pop("_ausweis_setzen", "")
    if ausweis:
        _cookie_schreiben(ausweis, GUELTIG_TAGE)
    if st.session_state.pop("_abmelden", False):
        _cookie_schreiben("", 0)

    if angemeldet_als():
        return

    aus_cookie = _ausweis_pruefen(_cookie_lesen(), benutzer)
    if aus_cookie:
        st.session_state["_benutzer"] = aus_cookie
        return

    _maske(benutzer)
