import streamlit as st
from datetime import datetime, timedelta
from streamlit_calendar import calendar
import os
import json

# App-Konfiguration
st.set_page_config(page_title="FECG Bruchmühlbach - Ordner Team", page_icon="⛪", layout="wide")

# CSS DESIGN
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    .main-title { color: #1e3a8a; font-family: 'Arial', sans-serif; font-weight: bold; text-align: center; margin-bottom: 20px; }
    .card-box { background-color: #ffffff; padding: 22px; border-radius: 12px; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05); border-top: 5px solid #1e3a8a; margin-bottom: 20px; }
    .chat-bubble-user { background-color: #dcf8c6; padding: 12px; border-radius: 12px; margin-bottom: 10px; border-right: 4px solid #25d366; max-width: 80%; margin-left: auto; }
    .chat-bubble-other { background-color: #ffffff; padding: 12px; border-radius: 12px; margin-bottom: 10px; border-left: 4px solid #3b82f6; max-width: 80%; margin-right: auto; }
    .chat-system { background-color: #e5e7eb; padding: 6px; border-radius: 20px; text-align: center; font-size: 0.85em; color: #4b5563; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# DATENBANK-LOGIK
# ----------------------------------------------------
DB_MITGLIEDER = "mitglieder_data.json"
DB_NOTIZEN = "kalender_notizen.json"

def lade_json(datei, default):
    if os.path.exists(datei):
        with open(datei, "r", encoding="utf-8") as f: return json.load(f)
    return default

def speichere_json(datei, daten):
    with open(datei, "w", encoding="utf-8") as f: json.dump(daten, f, ensure_ascii=False, indent=4)

if "mitglieder" not in st.session_state: 
    st.session_state.mitglieder = lade_json(DB_MITGLIEDER, [
        {'name': 'Komjagin Andreas', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Chef', 'passwort': 'Ordner'},
        {'name': 'Hauf Valintin', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'}
    ])
if "kalender_notizen" not in st.session_state: st.session_state.kalender_notizen = lade_json(DB_NOTIZEN, [])
if "leiter_chat" not in st.session_state: st.session_state.leiter_chat = [{'von': 'System', 'text': 'Willkommen im Chat!', 'zeit': 'Info'}]
if "eingeloggt_als" not in st.session_state: st.session_state.eingeloggt_als = None
if "passwort_aendern_fuer" not in st.session_state: st.session_state.passwort_aendern_fuer = None

def get_dienst_gruppe(datum):
    basis = datetime(2026, 6, 21).date()
    return ["Gruppe 1 (Andreas K.)", "Gruppe 2 (Slawik V.)", "Gruppe 3 (Peter S.)"][((datum - basis).days // 7) % 3]

# ----------------------------------------------------
# LOGIN-SYSTEM
# ----------------------------------------------------
if st.session_state.eingeloggt_als is None:
    st.markdown("<h1 class='main-title'>⛪ FECG Login</h1>", unsafe_allow_html=True)
    if st.session_state.passwort_aendern_fuer:
        u_name = st.session_state.passwort_aendern_fuer
        st.warning(f"⚠️ Hallo {u_name}, bitte wähle dein neues Passwort.")
        npw = st.text_input("Neues Passwort:", type="password")
        if st.button("Speichern"):
            for m in st.session_state.mitglieder:
                if m['name'] == u_name: m['passwort'] = npw
            speichere_json(DB_MITGLIEDER, st.session_state.mitglieder)
            st.session_state.eingeloggt_als = u_name
            st.session_state.passwort_aendern_fuer = None
            st.rerun()
    else:
        name = st.selectbox("Name:", [m['name'] for m in st.session_state.mitglieder])
        pw = st.text_input("Passwort (Standard: Ordner):", type="password")
        if st.button("Einloggen"):
            user = next((m for m in st.session_state.mitglieder if m['name'] == name), None)
            if user and pw == user['passwort']:
                if pw == "Ordner": st.session_state.passwort_aendern_fuer = name
                else: st.session_state.eingeloggt_als = name
                st.rerun()
    st.stop()

user = next(m for m in st.session_state.mitglieder if m['name'] == st.session_state.eingeloggt_als)
