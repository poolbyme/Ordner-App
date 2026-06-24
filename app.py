import streamlit as st
from datetime import datetime, timedelta
from streamlit_calendar import calendar
from streamlit_cookies_controller import CookieController
import os
import json
import time

# App-Konfiguration
st.set_page_config(page_title="FECG Bruchmühlbach - Ordner Team", page_icon="⛪", layout="wide")
controller = CookieController()

# CSS
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    .main-title { color: #1e3a8a; font-family: 'Arial', sans-serif; font-weight: bold; text-align: center; }
    .chat-bubble-user { background-color: #dcf8c6; padding: 12px; border-radius: 12px; margin-bottom: 10px; border-right: 4px solid #25d366; max-width: 85%; margin-left: auto; }
    .chat-bubble-other { background-color: #ffffff; padding: 12px; border-radius: 12px; margin-bottom: 10px; border-left: 4px solid #3b82f6; max-width: 85%; }
    .popup-box { background-color: #ffe4e6; padding: 15px; border-left: 6px solid #f43f5e; border-radius: 8px; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# Datenbanken laden
DB_FILE = "mitglieder_data.json"
CHAT_FILE = "chat_data.json"

def lade_daten():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return [{'name': 'Komjagin Andreas', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Chef', 'passwort': 'Ordner', 'telefon': '', 'anschrift': '', 'infos': '', 'geburtstag': ''}]

def speichere_daten(liste):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=4)

if "mitglieder" not in st.session_state: st.session_state.mitglieder = lade_daten()
if "leiter_chat" not in st.session_state: 
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r", encoding="utf-8") as f: st.session_state.leiter_chat = json.load(f)
    else: st.session_state.leiter_chat = []

# --- LOGIN LOGIK ---
if "eingeloggt_als" not in st.session_state:
    saved_user = controller.get('eingeloggt_als')
    if saved_user:
        st.session_state.eingeloggt_als = saved_user
        st.rerun()

if "eingeloggt_als" not in st.session_state:
    st.markdown("<h1 class='main-title'>⛪ Login</h1>", unsafe_allow_html=True)
    with st.form("login_form"):
        name = st.selectbox("Name:", [m['name'] for m in st.session_state.mitglieder])
        pw = st.text_input("Passwort:", type="password")
        if st.form_submit_button("Einloggen"):
            user = next((m for m in st.session_state.mitglieder if m['name'] == name), None)
            if user and user['passwort'] == pw:
                st.session_state.eingeloggt_als = name
                controller.set('eingeloggt_als', name, max_age=365*24*60*60)
                st.rerun()
            else: st.error("Fehler!")
    st.stop()

# --- HAUPTTEIL ---
user = next((m for m in st.session_state.mitglieder if m['name'] == st.session_state.eingeloggt_als), None)

st.sidebar.success(f"Eingeloggt als: {user['name']}")
if st.sidebar.button("Abmelden"):
    controller.remove('eingeloggt_als')
    st.session_state.clear()
    st.rerun()

st.title(f"Willkommen, {user['name']}")

# Chat System
with st.sidebar.expander("Chat"):
    for msg in st.session_state.leiter_chat:
        st.write(f"**{msg['von']}**: {msg['text']}")
    text = st.text_input("Nachricht")
    if st.button("Senden"):
        st.session_state.leiter_chat.append({'von': user['name'], 'text': text})
        with open(CHAT_FILE, "w", encoding="utf-8") as f: json.dump(st.session_state.leiter_chat, f)
        st.rerun()

# Kalender (simpel)
st.write("Dienstplan Übersicht...")
# Hier würde dein restlicher Code folgen...
