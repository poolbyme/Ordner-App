"""Anmeldung mit Benutzername und selbst vergebenem Passwort.

Die Konten liegen in der Ablage (siehe `konten.py`), nicht mehr in den
Streamlit-Einstellungen. Dort steht nur noch **ein** Wert:

    passwort = "einStartwort"

Der ist zweierlei:

* **Erstanmeldung.** Solange kein einziges Konto angelegt ist, kommt man damit
  hinein – und muss sofort Benutzername und eigenes Passwort festlegen. Das
  erste Konto übernimmt das bisherige Arbeitsblatt, damit die vorhandene
  Abrechnung nicht verschwindet.
* **Notfallschlüssel.** Wer sein Passwort vergisst, setzt sich damit ein neues.
  Ohne diesen Weg könnte man sich dauerhaft aussperren – die App läuft im
  Internet, es gibt keinen Hausmeister mit Zweitschlüssel.

Ist gar kein Startwort hinterlegt und noch kein Konto angelegt, ist die App
frei zugänglich. Das ist richtig, solange sie nur auf dem eigenen Rechner läuft.

**Angemeldet bleiben.** Wer das Häkchen setzt, bekommt einen Ausweis. Er trägt
nur den Benutzernamen, ein Ablaufdatum und eine Unterschrift – kein Passwort.
Die Unterschrift entsteht aus der Prüfsumme des Passworts: Wird das Passwort
geändert, sind alle alten Ausweise **dieses** Benutzers sofort wertlos, die der
anderen bleiben gültig.

Der Ausweis liegt an **zwei** Stellen: als Cookie und im Speicher des Browsers.
Ein Cookie allein hat sich als unzuverlässig erwiesen – Browser räumen sie auf,
und der Server sieht sie nur beim ersten Verbindungsaufbau. Bei jedem Besuch
wird der Ausweis erneuert: Wer die App benutzt, bleibt angemeldet, bis er auf
„Abmelden" drückt.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time

import streamlit as st

from . import konten

COOKIE = "nk_ausweis"
SPEICHER = "nk_ausweis"          # derselbe Name im Speicher des Browsers
GUELTIG_TAGE = 365
STANDARDBENUTZER = "vermieter"


# --- Startwort aus den Einstellungen ---------------------------------------

def startwort() -> str:
    """Das Wort für Erstanmeldung und Notfall – oder leer, wenn keines da ist."""
    try:
        einzeln = str(st.secrets.get("passwort") or "")
        if einzeln:
            return einzeln
        # Alte Schreibweise mit mehreren Benutzern: das erste Wort zählt.
        tabelle = st.secrets.get("benutzer")
        if tabelle:
            for wort in dict(tabelle).values():
                if str(wort):
                    return str(wort)
    except Exception:  # noqa: BLE001 – ohne secrets.toml wirft st.secrets
        return ""
    return ""


def aktiv() -> bool:
    """Ist überhaupt eine Anmeldung eingerichtet?"""
    return bool(startwort()) or not konten.leer()


def _startwort_stimmt(eingabe: str) -> bool:
    hinterlegt = startwort()
    return bool(hinterlegt) and hmac.compare_digest(eingabe, hinterlegt)


# --- Ausweis ---------------------------------------------------------------

def _unterschriftsgeheimnis(konto: konten.Konto) -> bytes:
    """Schlüssel für die Unterschrift – hängt an der Prüfsumme des Passworts.

    Damit macht ein Passwortwechsel genau die Ausweise dieses einen Benutzers
    ungültig. Früher hing der Schlüssel an *allen* Passwörtern; dann hätte das
    Anlegen einer weiteren Person alle anderen abgemeldet.
    """
    return hashlib.sha256(f"nk-ausweis|{konto.passwort}".encode("utf-8")).digest()


def _ausweis_bauen(konto: konten.Konto) -> str:
    ablauf = int(time.time()) + GUELTIG_TAGE * 24 * 3600
    nutzlast = f"{konto.name}|{ablauf}"
    unterschrift = hmac.new(_unterschriftsgeheimnis(konto),
                            nutzlast.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    roh = f"{nutzlast}|{unterschrift}".encode("utf-8")
    return base64.urlsafe_b64encode(roh).decode("ascii")


def _ausweis_pruefen(wert: str) -> konten.Konto | None:
    """Das Konto, wenn der Ausweis gültig ist – sonst None."""
    try:
        name, ablauf, unterschrift = base64.urlsafe_b64decode(
            wert.encode("ascii")).decode("utf-8").split("|")
    except Exception:  # noqa: BLE001 – alles Unlesbare gilt als ungültig
        return None
    konto = konten.finden(name)
    if konto is None or int(ablauf) < time.time():
        return None
    erwartet = hmac.new(_unterschriftsgeheimnis(konto),
                        f"{name}|{ablauf}".encode("utf-8"),
                        hashlib.sha256).hexdigest()[:32]
    return konto if hmac.compare_digest(unterschrift, erwartet) else None


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


def _adresse_setzen(wert: str) -> None:
    """Den Ausweis in die Adresszeile schreiben - oder ihn dort loeschen."""
    try:
        if wert:
            st.query_params["ausweis"] = wert
        elif "ausweis" in st.query_params:
            del st.query_params["ausweis"]
    except Exception:  # noqa: BLE001 - aeltere Streamlit-Fassungen
        pass


# --- angemeldeter Zustand --------------------------------------------------

def angemeldet_als() -> str:
    return str(st.session_state.get("_benutzer") or "")


def blatt() -> str:
    """Arbeitsblatt des angemeldeten Zugangs.

    Es steht im Konto, nicht im Namen. Deshalb behalten zwei Personen mit
    eigenem Passwort dieselbe Abrechnung, und ein neuer Name führt nicht in
    eine leere App.
    """
    return str(st.session_state.get("_blatt") or konten.BLATT)


def abmelden() -> None:
    """Abmelden und alles vergessen, was zu diesem Benutzer gehoert."""
    for schluessel in ("_benutzer", "_blatt", "_ablage_geprueft", "_ablagegrund",
                       "stamm", "positionen"):
        st.session_state.pop(schluessel, None)
    st.session_state["_abmelden"] = True


def _anmelden(konto: konten.Konto, merken: bool = True) -> None:
    """Anmelden und den Ausweis erneuern."""
    st.session_state["_benutzer"] = konto.name
    st.session_state["_blatt"] = konto.blatt
    if merken:
        ausweis = _ausweis_bauen(konto)
        st.session_state["_ausweis_setzen"] = ausweis
        _adresse_setzen(ausweis)


# --- Masken ----------------------------------------------------------------

def _kopf(unterzeile: str) -> None:
    from . import design

    design.kopfzeile("Nebenkostenabrechnung", unterzeile)


def _haekchen() -> bool:
    return st.checkbox(
        "Auf diesem Gerät angemeldet bleiben", value=True, key="anm_merken",
        help="Bleibt gesetzt, bis du auf ‚Abmelden' drückst. Gespeichert wird nur "
             "ein Ausweis, nicht dein Passwort. Er hängt danach auch in der "
             "Adresszeile – wer diesen Link bekommt, ist angemeldet.")


def _neues_passwort(schluessel: str) -> tuple[str, str]:
    eins = st.text_input("Neues Passwort", type="password", key=schluessel,
                         help=f"Mindestens {konten.MINDESTLAENGE} Zeichen.")
    zwei = st.text_input("Neues Passwort wiederholen", type="password",
                         key=schluessel + "_2")
    return eins, zwei


def _passwort_beanstanden(eins: str, zwei: str) -> str:
    if eins != zwei:
        return "Die beiden Passwörter sind nicht gleich."
    return konten.passwort_pruefen(eins)


def _erstanmeldung() -> None:
    """Erstes Konto anlegen: Startwort hinein, eigener Zugang heraus."""
    _kopf("Erste Anmeldung")
    if not st.session_state.get("_erst_frei"):
        st.info("Melde dich einmalig mit dem Startpasswort aus den Einstellungen an. "
                "Danach legst du deinen eigenen Benutzernamen und dein eigenes "
                "Passwort fest.")
        with st.form("erst_start"):
            wort = st.text_input("Startpasswort", type="password", key="erst_wort")
            los = st.form_submit_button("Weiter", type="primary", width="stretch")
        if los:
            if _startwort_stimmt(wort):
                st.session_state["_erst_frei"] = True
                st.rerun()
            else:
                st.error("Das Startpasswort stimmt nicht.")
        st.stop()

    st.success("Startpasswort stimmt. Jetzt dein eigener Zugang.")
    with st.form("erst_konto"):
        name = st.text_input("Benutzername", key="erst_name",
                             help="Frei wählbar, klein geschrieben, ohne "
                                  "Leerzeichen.").strip().lower()
        eins, zwei = _neues_passwort("erst_neu")
        merken = _haekchen()
        los = st.form_submit_button("Zugang anlegen", type="primary", width="stretch")

    if los:
        fehler = konten.name_pruefen(name) or _passwort_beanstanden(eins, zwei)
        if fehler:
            st.error(fehler)
        else:
            # Das erste Konto erbt das bisherige Arbeitsblatt: Was schon
            # eingetragen ist, soll nach dem Umstellen noch da sein.
            konto = konten.anlegen(name, eins, blatt=konten.BLATT)
            st.session_state.pop("_erst_frei", None)
            _anmelden(konto, merken)
            st.rerun()
    st.stop()


def _wechselmaske() -> None:
    """Erzwungener Wechsel: Der Zugang wurde mit einem Startpasswort angelegt."""
    _kopf("Bitte eigenes Passwort vergeben")
    st.info("Dieser Zugang wurde mit einem Startpasswort angelegt. Vergib jetzt "
            "dein eigenes – danach kennt es niemand sonst.")
    with st.form("wechsel"):
        eins, zwei = _neues_passwort("wechsel_neu")
        los = st.form_submit_button("Passwort übernehmen", type="primary",
                                    width="stretch")
    if los:
        fehler = _passwort_beanstanden(eins, zwei)
        if fehler:
            st.error(fehler)
        else:
            konten.passwort_setzen(angemeldet_als(), eins)
            konto = konten.finden(angemeldet_als())
            st.session_state.pop("_wechsel_noetig", None)
            if konto:
                _anmelden(konto)
            st.rerun()
    st.stop()


def _notfall() -> None:
    """Passwort vergessen: mit dem Startwort ein neues setzen."""
    with st.expander("Passwort vergessen?"):
        if not startwort():
            st.caption("Dafür muss in den Einstellungen ein Startpasswort "
                       "hinterlegt sein.")
            return
        st.caption("Mit dem Startpasswort aus den Einstellungen lässt sich für "
                   "einen Zugang ein neues Passwort setzen.")
        with st.form("notfall"):
            name = st.text_input("Benutzername", key="not_name").strip().lower()
            wort = st.text_input("Startpasswort", type="password", key="not_wort")
            eins, zwei = _neues_passwort("not_neu")
            los = st.form_submit_button("Passwort neu setzen", width="stretch")
        if los:
            if not _startwort_stimmt(wort):
                st.error("Das Startpasswort stimmt nicht.")
            elif konten.finden(name) is None:
                st.error("Diesen Benutzernamen gibt es nicht.")
            else:
                fehler = _passwort_beanstanden(eins, zwei)
                if fehler:
                    st.error(fehler)
                else:
                    konten.passwort_setzen(name, eins)
                    st.success("Passwort gesetzt. Du kannst dich jetzt anmelden.")


def _maske() -> None:
    _kopf("Bitte anmelden")
    with st.form("anmeldung"):
        name = st.text_input("Benutzername", key="anm_name").strip().lower()
        wort = st.text_input("Passwort", type="password", key="anm_wort")
        merken = _haekchen()
        abgeschickt = st.form_submit_button("Anmelden", type="primary",
                                            width="stretch")

    if abgeschickt:
        konto = konten.pruefen(name, wort)
        if konto:
            _anmelden(konto, merken)
            if konto.muss_wechseln:
                st.session_state["_wechsel_noetig"] = True
            st.rerun()
        else:
            st.error("Benutzername oder Passwort stimmt nicht.")
    _notfall()
    st.stop()


# --- Einstieg --------------------------------------------------------------

def pruefen() -> None:
    """Haelt die App an, bis jemand angemeldet ist."""
    # Auftraege aus dem letzten Durchlauf: Ablegen und Loeschen geht nur,
    # waehrend die Seite gezeichnet wird.
    ausweis = st.session_state.pop("_ausweis_setzen", "")
    if ausweis:
        _ausweis_ablegen(ausweis, GUELTIG_TAGE)
    if st.session_state.pop("_abmelden", False):
        _ausweis_ablegen("", 0)
        _adresse_setzen("")

    if not aktiv():
        # Weder Startwort noch Konto: freier Zugang, wie auf dem eigenen Rechner.
        st.session_state.setdefault("_benutzer", STANDARDBENUTZER)
        st.session_state.setdefault("_blatt", konten.BLATT)
        return

    if angemeldet_als():
        if st.session_state.get("_wechsel_noetig"):
            _wechselmaske()
        return

    # 1. Ausweis in der Adresszeile - so traegt ihn auch die Verknuepfung auf
    #    dem Startbildschirm mit sich.
    try:
        aus_adresse = str(st.query_params.get("ausweis") or "")
    except Exception:  # noqa: BLE001 - aeltere Streamlit-Fassungen
        aus_adresse = ""
    konto = _ausweis_pruefen(aus_adresse) if aus_adresse else None

    # 2. Cookie. Streamlit sieht ihn nur beim Verbindungsaufbau, und nicht jeder
    #    Browser haelt ihn - deshalb ist er nur die zweite Reihe.
    if konto is None:
        keks = _cookie_lesen()
        konto = _ausweis_pruefen(keks) if keks else None

    if konto is not None:
        _anmelden(konto)
        if konto.muss_wechseln:
            _wechselmaske()
        return

    if aus_adresse:      # abgelaufen oder verstuemmelt
        _adresse_setzen("")

    if konten.leer():
        _erstanmeldung()
    _maske()
