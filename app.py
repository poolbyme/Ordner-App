import streamlit as st
from datetime import datetime, timedelta
from streamlit_calendar import calendar
import os
import json

# App-Konfiguration
st.set_page_config(page_title="FECG Bruchmühlbach - Ordner Team", page_icon="⛪", layout="wide")

# CSS Design
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    .main-title { color: #1e3a8a; font-weight: bold; text-align: center; }
    .card-box { background-color: #ffffff; padding: 22px; border-radius: 12px; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05); border-top: 5px solid #1e3a8a; margin-bottom: 20px; }
    .chat-bubble-user { background-color: #dcf8c6; padding: 12px; border-radius: 12px; margin-bottom: 10px; border-right: 4px solid #25d366; max-width: 80%; margin-left: auto; }
    .chat-bubble-other { background-color: #ffffff; padding: 12px; border-radius: 12px; margin-bottom: 10px; border-left: 4px solid #3b82f6; max-width: 80%; margin-right: auto; }
    .chat-system { background-color: #e5e7eb; padding: 6px; border-radius: 20px; text-align: center; font-size: 0.85em; color: #4b5563; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# DATENBANK FUNKTIONEN
# ----------------------------------------------------
DB_FILE = "mitglieder_data.json"
NOTIZEN_FILE = "kalender_notizen.json"

def lade_daten(datei, standard_inhalt):
    if os.path.exists(datei):
        with open(datei, "r", encoding="utf-8") as f: return json.load(f)
    return standard_inhalt

def speichere_daten(datei, inhalt):
    with open(datei, "w", encoding="utf-8") as f: json.dump(inhalt, f, ensure_ascii=False, indent=4)

if "mitglieder" not in st.session_state:
    st.session_state.mitglieder = lade_daten(DB_FILE, [
        {'name': 'Komjagin Andreas', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Chef', 'passwort': 'Ordner'},
        {'name': 'Hauf Valintin', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
        {'name': 'Volkov Slawik', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Teamleiter', 'passwort': 'Ordner'}
    ])

if "kalender_notizen" not in st.session_state: st.session_state.kalender_notizen = lade_daten(NOTIZEN_FILE, [])

# Session States
defaults = {"urlaube": [], "gruppen_abfragen": {}, "leiter_chat": [{'von': 'System', 'text': 'Willkommen!', 'zeit': 'Info'}], 
            "eingeloggt_als": None, "passwort_aendern_fuer": None, "show_abfrage_form": False}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

def get_dienst_gruppe(datum):
    basis = datetime(2026, 6, 21).date()
    return ["Gruppe 1 (Andreas K.)", "Gruppe 2 (Slawik V.)", "Gruppe 3 (Peter S.)"][((datum - basis).days // 7) % 3]

# ----------------------------------------------------
# LOGIN-LOGIK
# ----------------------------------------------------
if st.session_state.eingeloggt_als is None:
    st.markdown("<h1 class='main-title'>⛪ FECG Login</h1>", unsafe_allow_html=True)
    if st.session_state.passwort_aendern_fuer:
        u_name = st.session_state.passwort_aendern_fuer
        st.warning(f"Hallo {u_name}, bitte wähle ein neues Passwort.")
        npw = st.text_input("Neues Passwort:", type="password")
        if st.button("Sichern"):
            for m in st.session_state.mitglieder:
                if m['name'] == u_name: m['passwort'] = npw
            speichere_daten(DB_FILE, st.session_state.mitglieder)
            st.session_state.eingeloggt_als = u_name
            st.session_state.passwort_aendern_fuer = None
            st.rerun()
    else:
        name = st.selectbox("Name:", [m['name'] for m in st.session_state.mitglieder])
        pw = st.text_input("Passwort:", type="password")
        if st.button("Einloggen"):
            user = next((m for m in st.session_state.mitglieder if m['name'] == name), None)
            if user and pw == user['passwort']:
                if pw == "Ordner": st.session_state.passwort_aendern_fuer = name
                else: st.session_state.eingeloggt_als = name
                st.rerun()
    st.stop()

user = next(m for m in st.session_state.mitglieder if m['name'] == st.session_state.eingeloggt_als)

# ----------------------------------------------------
# HAUPTTEIL
# ----------------------------------------------------
st.markdown("<h1 class='main-title'>FECG Ordner-Zentrale</h1>", unsafe_allow_html=True)

# Kalender
st.write("### 📅 Dienstplan & Pinnwand")
kalender_events = []
# (Dienstplan-Logik hier eingefügt wie vorher)
for i in range(-4, 20):
    w_start = datetime(2026, 6, 21).date() + timedelta(weeks=i)
    grp = get_dienst_gruppe(w_start)
    kalender_events.append({"title": f"🛠️ {grp}", "start": w_start.isoformat(), "allDay": True})

for n in st.session_state.kalender_notizen:
    kalender_events.append({"title": f"{n['icon']} {n['name']}: {n['text']}", "start": n['datum'], "allDay": True})

cal_render = calendar(events=kalender_events, options={"initialView": "dayGridMonth", "locale": "de", "selectable": True})

# Kalender Klick-Interaktion
if cal_render and "dateClick" in cal_render:
    datum_str = cal_render["dateClick"]["date"].split("T")[0]
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    typ = st.radio("Was eintragen?", ["🔴 Abwesenheit", "📝 Info / Notiz"])
    text = st.text_input("Details:") if "Info" in typ else ""
    if st.button("Speichern"):
        st.session_state.kalender_notizen.append({'datum': datum_str, 'name': user['name'], 'typ': typ, 'icon': '🔴' if 'Abw' in typ else '📝', 'text': text if text else "Abwesend"})
        speichere_daten(NOTIZEN_FILE, st.session_state.kalender_notizen)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

if st.sidebar.button("🚪 Abmelden"):
    st.session_state.eingeloggt_als = None
    st.rerun()
