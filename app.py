import streamlit as st
import json
import os
from datetime import datetime, timedelta
from streamlit_calendar import calendar

# App-Konfiguration
st.set_page_config(page_title="FECG Bruchmühlbach - Ordner Team", page_icon="⛪", layout="wide")

# CSS Design für die Optik
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    .main-title { color: #1e3a8a; font-weight: bold; text-align: center; }
    .card-box { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); border-left: 5px solid #1e3a8a; }
</style>
""", unsafe_allow_html=True)

# --- DATEN-KONFIGURATION ---
MITGLIEDER_LISTE = [
    {'name': 'Komjagin Andreas', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Chef', 'passwort': 'Ordner'},
    {'name': 'Hauf Valintin', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
    {'name': 'Volkov Slawik', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Teamleiter', 'passwort': 'Ordner'},
    {'name': 'Geier Enriko', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
    {'name': 'Peter S.', 'gruppe': 'Gruppe 3 (Peter S.)', 'rolle': 'Teamleiter', 'passwort': 'Ordner'}
]

# --- HILFSFUNKTIONEN ---
def lade_json(datei, default):
    if os.path.exists(datei):
        with open(datei, "r", encoding="utf-8") as f: return json.load(f)
    return default

def speichere_json(datei, daten):
    with open(datei, "w", encoding="utf-8") as f: json.dump(daten, f, ensure_ascii=False, indent=4)

def get_dienst_gruppe(datum):
    basis = datetime(2026, 6, 21).date()
    gruppen = ["Gruppe 1 (Andreas K.)", "Gruppe 2 (Slawik V.)", "Gruppe 3 (Peter S.)"]
    return gruppen[((datum - basis).days // 7) % 3]

# --- INITIALISIERUNG ---
if "mitglieder" not in st.session_state: st.session_state.mitglieder = MITGLIEDER_LISTE
if "notizen" not in st.session_state: st.session_state.notizen = lade_json("notizen.json", [])
if "urlaub" not in st.session_state: st.session_state.urlaub = lade_json("urlaub.json", [])
if "eingeloggt" not in st.session_state: st.session_state.eingeloggt = None

# --- LOGIN ---
if st.session_state.eingeloggt is None:
    st.markdown("<h1 class='main-title'>⛪ FECG Login</h1>", unsafe_allow_html=True)
    name = st.selectbox("Wer bist du?", [m['name'] for m in st.session_state.mitglieder])
    pw = st.text_input("Passwort:", type="password")
    if st.button("Einloggen"):
        user = next((m for m in st.session_state.mitglieder if m['name'] == name), None)
        if user and pw == user['passwort']:
            st.session_state.eingeloggt = name
            st.rerun()
        else: st.error("Falsches Passwort!")
    st.stop()

# --- HAUPTTEIL ---
user = next(m for m in st.session_state.mitglieder if m['name'] == st.session_state.eingeloggt)
st.sidebar.write(f"### Angemeldet: {user['name']}")
if st.sidebar.button("Abmelden"): st.session_state.eingeloggt = None; st.rerun()

st.markdown("<h1 class='main-title'>FECG Ordner-Zentrale</h1>", unsafe_allow_html=True)

# Dienstplan-Logik im Kalender
events = []
for i in range(-4, 20):
    datum = datetime(2026, 6, 21).date() + timedelta(weeks=i)
    events.append({"title": f"🛠️ {get_dienst_gruppe(datum)}", "start": datum.isoformat(), "allDay": True})

# Eigene Notizen/Urlaub hinzufügen
for n in st.session_state.notizen:
    events.append({"title": f"{n['icon']} {n['name']}: {n['text']}", "start": n['datum'], "allDay": True})

cal = calendar(events=events, options={"selectable": True})

if cal and "dateClick" in cal:
    datum = cal["dateClick"]["date"].split("T")[0]
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    typ = st.radio("Grund:", ["🔴 Abwesenheit", "📝 Info / Urlaub"])
    text = st.text_input("Details:")
    if st.button("Speichern"):
        st.session_state.notizen.append({'datum': datum, 'name': user['name'], 'icon': '🔴' if 'Abw' in typ else '📝', 'text': text or "Abwesend"})
        speichere_json("notizen.json", st.session_state.notizen)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
