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

**Angemeldet bleiben.** Wer das Häkchen setzt, bekommt einen Ausweis. Er trägt
nur den Benutzernamen, ein Ablaufdatum und eine Unterschrift – kein Passwort.
Die Unterschrift entsteht aus den hinterlegten Passwörtern: Wird eines
geändert, sind alle alten Ausweise sofort wertlos.

Der Ausweis liegt an **zwei** Stellen: als Cookie und im Speicher des Browsers.
Ein Cookie allein hat sich als unzuverlässig erwiesen – Browser räumen sie auf,
und der Server sieht sie nur beim ersten Verbindungsaufbau. Findet sich kein
Cookie, holt ein kurzes Skript den Ausweis aus dem Browserspeicher und hängt
ihn einmalig an die Adresse; die App liest ihn, meldet an und räumt die Adresse
wieder auf.

Bei jedem Besuch wird der Ausweis erneuert. Wer die App benutzt, bleibt also
angemeldet, bis er auf „Abmelden" drückt.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time

import streamlit as st

COOKIE = "nk_ausweis"
SPEICHER = "nk_ausweis"          # derselbe Name im Speicher des Browsers
GUELTIG_TAGE = 365
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
    except Exception:  # noqa: BLE001 - aeltere Streamlit-Fassungen
        return ""


def _skript(inhalt: str) -> None:
    """Ein kurzes Skript in der umgebenden Seite ausfuehren."""
    baustein = getattr(st, "iframe", None)
    hoehe = 1
    if baustein is None:  # pragma: no cover - aeltere Streamlit-Fassungen
        hoehe = 0
        try:
            from streamlit.components.v1 import html as baustein
        except ImportError:
            return
    baustein("<script>\n(function () {\n" + inhalt + "\n})();\n</script>",
             height=hoehe)


def _sauber(wert: str) -> str:
    """Nur das Alphabet des Ausweises durchlassen - nichts Ausfuehrbares."""
    return "".join(c for c in wert if c.isalnum() or c in "-_=")


def _ausweis_ablegen(wert: str, tage: int) -> None:
    """Ausweis an beiden Stellen ablegen: Cookie und Browserspeicher.

    Leerer Wert plus 0 Tage loescht ihn. Streamlit kann weder Cookies setzen
    noch den Browserspeicher lesen, deshalb erledigt das ein Skript in der
    umgebenden Seite.
    """
    _skript("\n".join([
        '  const alter = %d;',
        '  const w = "%s";',
        '  try {',
        '    window.parent.document.cookie =',
        '      "%s=" + w + "; path=/; max-age=" + alter + "; SameSite=Lax";',
        '  } catch (e) {}',
        '  try {',
        '    if (w) window.parent.localStorage.setItem("%s", w);',
        '    else window.parent.localStorage.removeItem("%s");',
        '  } catch (e) {}',
    ]) % (tage * 24 * 3600, _sauber(wert), COOKIE, SPEICHER, SPEICHER))


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
                             help="Bleibt gesetzt, bis du auf ‚Abmelden‘ drückst. "
                                  "Gespeichert wird nur ein Ausweis, nicht dein Passwort. "
                                  "Er hängt danach auch in der Adresszeile – wer diesen "
                                  "Link bekommt, ist angemeldet.")
        abgeschickt = st.form_submit_button("Anmelden", type="primary", width="stretch")

    if abgeschickt:
        hinterlegt = benutzer.get(name, "")
        if hinterlegt and hmac.compare_digest(wort, hinterlegt):
            _anmelden(name, benutzer, merken)
            st.rerun()
        else:
            st.error("Benutzername oder Passwort stimmt nicht."
                     if mehrere else "Das Passwort stimmt nicht.")
    st.stop()


def _adresse_aufraeumen() -> None:
    """Den Ausweis wieder aus der Adresszeile nehmen."""
    try:
        if "ausweis" in st.query_params:
            del st.query_params["ausweis"]
    except Exception:  # noqa: BLE001 - aeltere Streamlit-Fassungen
        pass


def _anmelden(name: str, benutzer: dict) -> None:
    """Anmelden und den Ausweis erneuern.

    Bei jedem Besuch neu ausgestellt: Wer die App benutzt, bleibt angemeldet,
    bis er auf „Abmelden" drueckt.
    """
    st.session_state["_benutzer"] = name
    st.session_state["_ausweis_setzen"] = _ausweis_bauen(name, benutzer)


def _adresse_setzen(wert: str) -> None:
    """Den Ausweis in die Adresszeile schreiben - oder ihn dort loeschen.

    Das ist der zuverlaessigste Weg: Wer die App danach auf den Startbildschirm
    legt, dessen Verknuepfung traegt den Ausweis fuer immer mit sich. Der Preis
    steht in der Anmeldemaske: Wer diesen Link bekommt, ist angemeldet.
    """
    try:
        if wert:
            st.query_params["ausweis"] = wert
        elif "ausweis" in st.query_params:
            del st.query_params["ausweis"]
    except Exception:  # noqa: BLE001 - aeltere Streamlit-Fassungen
        pass


def _anmelden(name: str, benutzer: dict, merken: bool = True) -> None:
    """Anmelden und den Ausweis erneuern.

    Bei jedem Besuch neu ausgestellt: Wer die App benutzt, bleibt angemeldet,
    bis er auf „Abmelden" drueckt.
    """
    st.session_state["_benutzer"] = name
    if merken:
        ausweis = _ausweis_bauen(name, benutzer)
        st.session_state["_ausweis_setzen"] = ausweis
        _adresse_setzen(ausweis)


def pruefen() -> None:
    """Haelt die App an, bis jemand angemeldet ist."""
    benutzer = benutzerliste()
    if not benutzer:
        st.session_state.setdefault("_benutzer", STANDARDBENUTZER)
        return

    # Auftraege aus dem letzten Durchlauf: Ablegen und Loeschen geht nur,
    # waehrend die Seite gezeichnet wird.
    ausweis = st.session_state.pop("_ausweis_setzen", "")
    if ausweis:
        _ausweis_ablegen(ausweis, GUELTIG_TAGE)
    if st.session_state.pop("_abmelden", False):
        _ausweis_ablegen("", 0)
        _adresse_setzen("")

    if angemeldet_als():
        return

    # 1. Ausweis in der Adresszeile - so traegt ihn auch die Verknuepfung auf
    #    dem Startbildschirm mit sich.
    try:
        aus_adresse = str(st.query_params.get("ausweis") or "")
    except Exception:  # noqa: BLE001 - aeltere Streamlit-Fassungen
        aus_adresse = ""
    name = _ausweis_pruefen(aus_adresse, benutzer) if aus_adresse else ""
    if name:
        _anmelden(name, benutzer)
        return

    # 2. Cookie. Streamlit sieht ihn nur beim Verbindungsaufbau, und nicht jeder
    #    Browser haelt ihn - deshalb ist er nur die zweite Reihe.
    name = _ausweis_pruefen(_cookie_lesen(), benutzer)
    if name:
        _anmelden(name, benutzer)
        return

    if aus_adresse:      # abgelaufen oder verstuemmelt
        _adresse_setzen("")
    _maske(benutzer)
