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
    .stApp { background-color: #f4f6f9; }
    .main-title { color: #1e3a8a; font-family: 'Arial', sans-serif; font-weight: bold; text-align: center; margin-bottom: 20px; }
    .chat-bubble-user { background-color: #dcf8c6; padding: 12px; border-radius: 12px; margin-bottom: 10px; border-right: 4px solid #25d366; max-width: 80%; margin-left: auto; box-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
    .chat-bubble-other { background-color: #ffffff; padding: 12px; border-radius: 12px; margin-bottom: 10px; border-left: 4px solid #3b82f6; max-width: 80%; margin-right: auto; box-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
    .chat-system { background-color: #e5e7eb; padding: 6px; border-radius: 20px; text-align: center; font-size: 0.85em; color: #4b5563; margin-bottom: 15px; }
    .card-box { background-color: #ffffff; padding: 22px; border-radius: 12px; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05); border-top: 5px solid #1e3a8a; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# DATENBANK FUNKTIONEN
DB_FILE = "mitglieder_data.json"
def lade_mitglieder():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
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
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(liste, f, ensure_ascii=False, indent=4)

if "mitglieder" not in st.session_state: st.session_state.mitglieder = lade_mitglieder()
if "notizen" not in st.session_state: st.session_state.notizen = [] # Initialisiere Notizen

def get_dienst_gruppe(datum):
    basis_datum = datetime(2026, 6, 21).date()
    wochen = (datum - basis_datum).days // 7
    return ["Gruppe 1 (Andreas K.)", "Gruppe 2 (Slawik V.)", "Gruppe 3 (Peter S.)"][wochen % 3]

# LOGIN-LOGIK
if "eingeloggt_als" not in st.session_state: st.session_state.eingeloggt_als = None
if st.session_state.eingeloggt_als is None:
    st.title("Login")
    name = st.selectbox("Name:", [m['name'] for m in st.session_state.mitglieder])
    pw = st.text_input("Passwort:", type="password")
    if st.button("Einloggen"):
        user_check = next((m for m in st.session_state.mitglieder if m['name'] == name), None)
        if user_check and pw == user_check['passwort']:
            st.session_state.eingeloggt_als = name
            st.rerun()
    st.stop()

user = next((m for m in st.session_state.mitglieder if m['name'] == st.session_state.eingeloggt_als), None)

# HAUPTTEIL
st.title("FECG Ordner-Zentrale")
if st.sidebar.button("Abmelden"): st.session_state.eingeloggt_als = None; st.rerun()

# KALENDER
cal = calendar(events=[], options={"initialView": "dayGridMonth", "locale": "de", "selectable": True})

# --- HIER IST DIE GEWÜNSCHTE EINSCHRÄNKUNG ---
if cal and "dateClick" in cal:
    datum_str = cal["dateClick"]["date"].split("T")[0]
    datum_obj = datetime.strptime(datum_str, "%Y-%m-%d").date()
    
    # NUR WENN DIENSTWOCHE PASST
    if user['gruppe'] == get_dienst_gruppe(datum_obj):
        st.write(f"### Eintrag für den {datum_str}")
        typ = st.radio("Art:", ["🔴 Abwesenheit", "📝 Sonstiges"])
        text = st.text_input("Details:")
        if st.button("Speichern"):
            st.session_state.notizen.append({'datum': datum_str, 'name': user['name'], 'typ': typ, 'text': text})
            st.rerun()
    else:
        st.warning(f"🚫 Du kannst nur für deine eigene Dienstwoche ({user['gruppe']}) Einträge machen.")
