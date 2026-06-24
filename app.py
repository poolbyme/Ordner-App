[18:51, 24.6.2026] A.K: import streamlit as st
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
</style>
""", unsafe_allow_html=True)

# DATENBANK FUNKTIONEN
DB_MITGLIEDER = "mitglieder_data.json"
DB_NOTIZEN = "kalender_notizen.json"

def lade_mitglieder():
    if os.path.exists(DB_MITGLIEDER):
        with open(DB_MITGLIEDER, "r", encoding="utf-8") as f: return json.load(f)
    return [{'name': 'Komjagin Andreas', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Chef', 'passwort': 'Ordner'}]

def speichere_mitglieder(daten):
    with open(DB_MITGLIEDER, "w", encoding="utf-8") as f: json.dump(daten, f, ensure_ascii=False, indent=4)

if "mitglieder" not in st.session_state: st.session_state.mitglieder = lade_mitglieder()
if "eingeloggt_als" not in st.session_state: st.session_state.eingeloggt_als = None
if "passwort_aendern_modus" not in st.session_state: st.session_state.passwort_aendern_modus = None

# LOGIN LOGIK
if st.session_state.eingeloggt_als is None:
    st.markdown("<h1 class='main-title'>⛪ FECG Login</h1>", unsafe_allow_html=True)
    if st.session_state.passwort_aendern_modus:
        u_name = st.session_state.passwort_aendern_modus
        npw = st.text_input("Neues Passwort wählen:", type="password")
        if st.button("Speichern"):
            for m in st.session_state.mitglieder:
                if m['name'] == u_name: m['passwort'] = npw
            speichere_mitglieder(st.session_state.mitglieder)
            st.session_state.eingeloggt_als = u_name
            st.session_state.passwort_aendern_modus = None
            st.rerun()
    else:
        name = st.selectbox("Name:", [m['name'] for m in st.session_state.mitglieder])
        pw = st.text_input("Passwort:", type="password")
        if st.button("Einloggen"):
            user = next((m for m in st.session_state.mitglieder if m['name'] == name), None)
            if user and pw == user['passwort']:
                if pw == "Ordner": st.session_state.passwort_aendern_modus = name
                else: st.session_state.eingeloggt_als = name
                st.rerun()
    st.stop()

st.success(f"Eingeloggt als {st.session_state.eingeloggt_als}")
[18:52, 24.6.2026] A.K: import streamlit as st
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
    .main-title { color: #1e3a8a; font-family: 'Arial', sans-serif; font-weight: bold; text-align: center; margin-bottom: 20px; }
    .card-box { background-color: #ffffff; padding: 22px; border-radius: 12px; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05); border-top: 5px solid #1e3a8a; margin-bottom: 20px; }
    .chat-bubble-other { background-color: #ffffff; padding: 12px; border-radius: 12px; margin-bottom: 10px; border-left: 4px solid #3b82f6; }
    .chat-system { background-color: #e5e7eb; padding: 6px; border-radius: 20px; text-align: center; font-size: 0.85em; color: #4b5563; }
</style>
""", unsafe_allow_html=True)

# DATENBANK FUNKTIONEN
DB_MITGLIEDER = "mitglieder_data.json"
DB_NOTIZEN = "kalender_notizen.json"
DB_CHAT = "chat_data.json"

def lade_json(datei, default):
    if os.path.exists(datei):
        with open(datei, "r", encoding="utf-8") as f: return json.load(f)
    return default

def speichere_json(datei, daten):
    with open(datei, "w", encoding="utf-8") as f: json.dump(daten, f, ensure_ascii=False, indent=4)

# INITIALISIERUNG
if "mitglieder" not in st.session_state: st.session_state.mitglieder = lade_json(DB_MITGLIEDER, [
    {'name': 'Komjagin Andreas', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Chef', 'passwort': 'Ordner'},
    {'name': 'Hauf Valintin', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'}
])
if "notizen" not in st.session_state: st.session_state.notizen = lade_json(DB_NOTIZEN, [])
if "chat" not in st.session_state: st.session_state.chat = lade_json(DB_CHAT, [{'von': 'System', 'text': 'Willkommen!', 'zeit': 'Info'}])
if "eingeloggt" not in st.session_state: st.session_state.eingeloggt = None
if "pw_modus" not in st.session_state: st.session_state.pw_modus = None

# HILFSFUNKTIONEN
def get_dienst_gruppe(datum):
    basis = datetime(2026, 6, 21).date()
    return ["Gruppe 1 (Andreas K.)", "Gruppe 2 (Slawik V.)", "Gruppe 3 (Peter S.)"][((datum - basis).days // 7) % 3]

# LOGIN LOGIK
if st.session_state.eingeloggt is None:
    st.markdown("<h1 class='main-title'>⛪ FECG Login</h1>", unsafe_allow_html=True)
    if st.session_state.pw_modus:
        u_name = st.session_state.pw_modus
        npw = st.text_input("Neues Passwort wählen:", type="password")
        if st.button("Speichern"):
            for m in st.session_state.mitglieder:
                if m['name'] == u_name: m['passwort'] = npw
            speichere_json(DB_MITGLIEDER, st.session_state.mitglieder)
            st.session_state.eingeloggt = u_name
            st.session_state.pw_modus = None
            st.rerun()
    else:
        name = st.selectbox("Name:", [m['name'] for m in st.session_state.mitglieder])
        pw = st.text_input("Passwort:", type="password")
        if st.button("Einloggen"):
            user = next((m for m in st.session_state.mitglieder if m['name'] == name), None)
            if user and pw == user['passwort']:
                if pw == "Ordner": st.session_state.pw_modus = name
                else: st.session_state.eingeloggt = name
                st.rerun()
    st.stop()

# HAUPTTEIL
user = next(m for m in st.session_state.mitglieder if m['name'] == st.session_state.eingeloggt)
st.sidebar.write(f"### 👤 {user['name']}")
if st.sidebar.button("🚪 Abmelden"): st.session_state.eingeloggt = None; st.rerun()

st.markdown("<h1 class='main-title'>⛪ FECG Ordner-Zentrale</h1>", unsafe_allow_html=True)

# KALENDER
st.write("### 📅 Dienstplan & Pinnwand")
events = [{"title": f"🛠️ {get_dienst_gruppe(datetime(2026, 6, 21).date() + timedelta(weeks=i))}", "start": (datetime(2026, 6, 21).date() + timedelta(weeks=i)).isoformat(), "allDay": True} for i in range(-4, 20)]
for n in st.session_state.notizen:
    events.append({"title": f"{n['icon']} {n['name']}: {n['text']}", "start": n['datum'], "allDay": True})

cal = calendar(events=events, options={"initialView": "dayGridMonth", "locale": "de", "selectable": True})

if cal and "dateClick" in cal:
    datum = cal["dateClick"]["date"].split("T")[0]
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    typ = st.radio("Eintragstyp:", ["🔴 Abwesenheit", "📝 Info / Notiz"])
    text = st.text_input("Details:") if "Info" in typ else ""
    if st.button("Speichern"):
        st.session_state.notizen.append({'datum': datum, 'name': user['name'], 'icon': '🔴' if 'Abw' in typ else '📝', 'text': text if text else "Abwesend"})
        speichere_json(DB_NOTIZEN, st.session_state.notizen)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# CHAT
if user['rolle'] in ["Chef", "Teamleiter"]:
    st.write("---")
    st.write("### 💬 Gruppenleiter-Chat")
    for msg in st.session_state.chat:
        st.markdown(f"<div class='chat-bubble-other'><b>{msg['von']}</b>: {msg['text']}</div>", unsafe_allow_html=True)
    if n_msg := st.chat_input("Schreiben..."):
        st.session_state.chat.append({'von': user['name'], 'text': n_msg})
        speichere_json(DB_CHAT, st.session_state.chat)
        st.rerun()
