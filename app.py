import streamlit as st
import json
import os
from datetime import datetime, timedelta
from streamlit_calendar import calendar

# App-Konfiguration
st.set_page_config(page_title="FECG Bruchmühlbach", layout="wide")

# CSS Design
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    .card-box { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# Funktionen für dauerhafte Speicherung
def lade_daten(datei):
    if os.path.exists(datei):
        with open(datei, "r", encoding="utf-8") as f: return json.load(f)
    return None

def speichere_daten(datei, daten):
    with open(datei, "w", encoding="utf-8") as f: json.dump(daten, f, ensure_ascii=False, indent=4)

# Initialisierung
if "mitglieder" not in st.session_state:
    st.session_state.mitglieder = lade_daten("mitglieder_data.json") or [
        {'name': 'Komjagin Andreas', 'rolle': 'Chef', 'passwort': 'Ordner'},
        {'name': 'Hauf Valintin', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'}
    ]
if "notizen" not in st.session_state: st.session_state.notizen = lade_daten("notizen.json") or []
if "user" not in st.session_state: st.session_state.user = None
if "pw_aendern" not in st.session_state: st.session_state.pw_aendern = None

# Login Logik
if st.session_state.user is None:
    st.title("Login")
    if st.session_state.pw_aendern:
        neues_pw = st.text_input("Neues Passwort:", type="password")
        if st.button("Speichern"):
            for m in st.session_state.mitglieder:
                if m['name'] == st.session_state.pw_aendern: m['passwort'] = neues_pw
            speichere_daten("mitglieder_data.json", st.session_state.mitglieder)
            st.session_state.user = st.session_state.pw_aendern
            st.session_state.pw_aendern = None
            st.rerun()
    else:
        name = st.selectbox("Name:", [m['name'] for m in st.session_state.mitglieder])
        pw = st.text_input("Passwort:", type="password")
        if st.button("Einloggen"):
            user = next((m for m in st.session_state.mitglieder if m['name'] == name), None)
            if user and pw == user['passwort']:
                if pw == "Ordner": st.session_state.pw_aendern = name
                else: st.session_state.user = name
                st.rerun()
    st.stop()

# Hauptteil
user = next(m for m in st.session_state.mitglieder if m['name'] == st.session_state.user)
st.sidebar.write(f"Eingeloggt als: {user['name']}")
if st.sidebar.button("Abmelden"): st.session_state.user = None; st.rerun()

st.title("FECG Ordner-Zentrale")
events = [{"title": f"{n['name']}: {n['text']}", "start": n['datum']} for n in st.session_state.notizen]
cal = calendar(events=events, options={"selectable": True})

if cal and "dateClick" in cal:
    datum = cal["dateClick"]["date"].split("T")[0]
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    typ = st.radio("Grund:", ["Abwesenheit", "Sonstiges"])
    text = st.text_input("Details:")
    if st.button("Speichern"):
        st.session_state.notizen.append({'datum': datum, 'name': user['name'], 'text': text or typ})
        speichere_daten("notizen.json", st.session_state.notizen)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
