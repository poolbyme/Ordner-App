import streamlit as st
from datetime import datetime, timedelta
from streamlit_calendar import calendar
import os
import json

# App-Konfiguration mit Kreuz-Symbol
st.set_page_config(page_title="FECG Bruchmühlbach - Ordner Team", page_icon="⛪", layout="wide")

# CSS FÜR INDIVIDUELLES DESIGN UND FARBEN (FECG THEME)
st.markdown("""
<style>
    .stApp {
        background-color: #f4f6f9;
    }
    .main-title {
        color: #1e3a8a;
        font-family: 'Arial', sans-serif;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
    }
    .chat-bubble-user {
        background-color: #dcf8c6;
        padding: 12px;
        border-radius: 12px;
        margin-bottom: 10px;
        border-right: 4px solid #25d366;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .chat-bubble-other {
        background-color: #ffffff;
        padding: 12px;
        border-radius: 12px;
        margin-bottom: 10px;
        border-left: 4px solid #3b82f6;
        max-width: 80%;
        margin-right: auto;
        box-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .chat-system {
        background-color: #e5e7eb;
        padding: 6px;
        border-radius: 20px;
        text-align: center;
        font-size: 0.85em;
        color: #4b5563;
        margin-bottom: 15px;
    }
    .card-box {
        background-color: #ffffff;
        padding: 22px;
        border-radius: 12px;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05);
        border-top: 5px solid #1e3a8a;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# MITGLIEDER DAUERHAFT SPEICHERN (DATEI-DATENBANK)
# ----------------------------------------------------
DB_FILE = "mitglieder_data.json"

def lade_mitglieder():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return [
            {'name': 'Komjagin Andreas', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Chef', 'passwort': 'Ordner'},
            {'name': 'Hauf Valintin', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
            {'name': 'Geier Enriko', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
            {'name': 'Ilchuk Vasyl', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
            {'name': 'Volkov Slawik', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Teamleiter', 'passwort': 'Ordner'},
            {'name': 'Tissen Eduard', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
            {'name': 'Eberhart Wili', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
            {'name': 'Paul Steffen', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
            {'name': 'Schäfer Peter', 'gruppe': 'Gruppe 3 (Peter S.)', 'rolle': 'Teamleiter', 'passwort': 'Ordner'},
            {'name': 'Akulenko Wili', 'gruppe': 'Gruppe 3 (Peter S.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
            {'name': 'Hermann Bogdan', 'gruppe': 'Gruppe 3 (Peter S.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'}
        ]

def speichere_mitglieder(liste):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=4)

if "mitglieder" not in st.session_state:
    st.session_state.mitglieder = lade_mitglieder()

# Initialisierung aller anderen Variablen
if "urlaube" not in st.session_state: st.session_state.urlaube = []
if "gruppen_abfragen" not in st.session_state: st.session_state.gruppen_abfragen = {}
if "leiter_chat" not in st.session_state: st.session_state.leiter_chat = [{'von': 'System', 'text': 'Willkommen!', 'zeit': 'Info'}]
if "eingeloggt_als" not in st.session_state: st.session_state.eingeloggt_als = None
if "passwort_aendern_fuer" not in st.session_state: st.session_state.passwort_aendern_fuer = None
if "show_abfrage_form" not in st.session_state: st.session_state.show_abfrage_form = False
if "show_urlaub_form" not in st.session_state: st.session_state.show_urlaub_form = False

def get_dienst_gruppe(datum):
    basis_datum = datetime(2026, 6, 21).date()
    wochen = (datum - basis_datum).days // 7
    return ["Gruppe 1 (Andreas K.)", "Gruppe 2 (Slawik V.)", "Gruppe 3 (Peter S.)"][wochen % 3]

# LOGIN-LOGIK
if st.session_state.eingeloggt_als is None:
    st.markdown("<h1 class='main-title'>⛪ FECG Bruchmühlbach — Login</h1>", unsafe_allow_html=True)
    if st.session_state.passwort_aendern_fuer is not None:
        u_name = st.session_state.passwort_aendern_fuer
        st.warning(f"Hallo {u_name}, bitte Passwort ändern.")
        neues_pw = st.text_input("Neues Passwort:", type="password")
        if st.button("Speichern"):
            for m in st.session_state.mitglieder:
                if m['name'] == u_name: m['passwort'] = neues_pw
            speichere_mitglieder(st.session_state.mitglieder)
            st.session_state.eingeloggt_als = u_name
            st.session_state.passwort_aendern_fuer = None
            st.rerun()
    else:
        alle_namen = sorted([m['name'] for m in st.session_state.mitglieder])
        login_name = st.selectbox("Name:", options=alle_namen)
        passwort_eingabe = st.text_input("Passwort:", type="password")
        if st.button("Einloggen"):
            user_check = next((m for m in st.session_state.mitglieder if m['name'] == login_name), None)
            if user_check and passwort_eingabe == user_check['passwort']:
                if passwort_eingabe == "Ordner":
                    st.session_state.passwort_aendern_fuer = login_name
                else:
                    st.session_state.eingeloggt_als = login_name
                st.rerun()
    st.stop()

user = next((m for m in st.session_state.mitglieder if m['name'] == st.session_state.eingeloggt_als), None)

# HAUPTTEIL
st.markdown("<h1 class='main-title'>FECG Ordner-Zentrale</h1>", unsafe_allow_html=True)
if st.sidebar.button("🚪 Abmelden"): st.session_state.eingeloggt_als = None; st.rerun()

# KALENDER
kalender_events = []
# (Hier fügst du deine bestehende Kalender-Logik ein...)
cal = calendar(events=kalender_events, options={"initialView": "dayGridMonth", "locale": "de", "selectable": True}, key="fecg_calendar")

# --- HIER IST DIE EINGESCHRÄNKTE EINGABE-LOGIK ---
if cal and "dateClick" in cal:
    datum_str = cal["dateClick"]["date"].split("T")[0]
    datum_obj = datetime.strptime(datum_str, "%Y-%m-%d").date()
    
    if user['gruppe'] == get_dienst_gruppe(datum_obj):
        st.write(f"### Eintrag für den {datum_str}")
        typ = st.radio("Art:", ["🔴 Abwesenheit", "📝 Sonstiges"])
        text = st.text_input("Details:")
        if st.button("Speichern"):
            # Speichere in eine Liste oder Datei...
            st.success("Gespeichert!")
    else:
        st.warning(f"🚫 Du kannst nur für deine eigene Dienstwoche ({user['gruppe']}) Einträge machen.")

# (Hier folgen alle weiteren Funktionen aus deinem Originalcode: Mitgliederverwaltung, Chat, Abfragen, etc.)
