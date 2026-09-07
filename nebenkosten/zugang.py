"""Passwortschutz für den Betrieb im Internet.

Ohne hinterlegtes Passwort ist die App frei zugänglich – das ist richtig, solange
sie nur auf dem eigenen Rechner läuft. Sobald sie im Netz steht, gehört ein
Passwort in die Secrets:

    passwort = "einGutesWort"

Dann fragt die App danach, bevor irgendetwas angezeigt wird.
"""

from __future__ import annotations

import hmac

import streamlit as st


def _hinterlegtes_passwort() -> str:
    try:
        return str(st.secrets.get("passwort") or "")
    except Exception:  # noqa: BLE001 – ohne secrets.toml wirft st.secrets
        return ""


def pruefen() -> None:
    """Fragt nach dem Passwort und hält die App an, solange es fehlt."""
    erwartet = _hinterlegtes_passwort()
    if not erwartet or st.session_state.get("_zugang_frei"):
        return

    st.markdown("### 🔒 Nebenkostenabrechnung")
    st.caption("Diese App enthält persönliche Daten. Bitte das Passwort eingeben.")
    with st.form("anmeldung"):
        eingabe = st.text_input("Passwort", type="password")
        abgeschickt = st.form_submit_button("Anmelden", type="primary")
    if abgeschickt:
        # hmac.compare_digest vergleicht ohne Rückschlüsse über die Antwortzeit
        if hmac.compare_digest(eingabe, erwartet):
            st.session_state["_zugang_frei"] = True
            st.rerun()
        else:
            st.error("Das Passwort stimmt nicht.")
    st.stop()
