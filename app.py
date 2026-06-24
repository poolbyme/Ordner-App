import streamlit as st
import json
import os
from datetime import datetime, timedelta
from streamlit_calendar import calendar

# App-Setup
st.set_page_config(page_title="FECG App", layout="wide")

# Dateien
DB_MITGLIEDER = "mitglieder_data.json"
DB_NOTIZEN = "kalender_notizen.json"
DB_CHAT = "chat.json"
DB_ABFRAGEN = "abfragen.json"

# Standard-Mitglieder (wird geladen, wenn Datei fehlt)
STANDARD_MITGLIEDER = [
    {'name': 'Komjagin Andreas', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Chef', 'passwort': 'Ordner'},
    {'name': 'Hauf Valintin', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
    {'name': 'Volkov Slawik', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Teamleiter', 'passwort': 'Ordner'},
    {'name': 'Geier Enriko', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
    {'name': 'Peter S.', 'gruppe': 'Gruppe 3 (Peter S.)', 'rolle': 'Teamleiter', 'passwort': 'Ordner'}
]

# Speicher-Funktionen
def load(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f: return json.load(f)
    return default

def save(file, data):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

# Session State
if "m" not in st.session_state: st.session_state.m = load(DB_MITGLIEDER, STANDARD_MITGLIEDER)
if "n" not in st.session_state: st.session_state.n = load(DB_NOTIZEN, [])
if "c" not in st.session_state: st.session_state.c = load(DB_CHAT, [])
if "a" not in st.session_state: st.session_state.a = load(DB_ABFRAGEN, {})
if "user" not in st.session_state: st.session_state.user = None
if "pw_modus" not in st.session_state: st.session_state.pw_modus = None

# Dienstplan-Logik
def get_dienst(datum):
    basis = datetime(2026, 6, 21).date()
    return ["Gruppe 1 (Andreas K.)", "Gruppe 2 (Slawik V.)", "Gruppe 3 (Peter S.)"][((datum - basis).days // 7) % 3]

# Login
if st.session_state.user is None:
    st.title("⛪ Login")
    if st.session_state.pw_modus:
        u = st.session_state.pw_modus
        npw = st.text_input("Neues Passwort wählen:", type="password")
        if st.button("Speichern"):
            for m in st.session_state.m:
                if m['name'] == u: m['passwort'] = npw
            save(DB_MITGLIEDER, st.session_state.m)
            st.session_state.user = u
            st.session_state.pw_modus = None
            st.rerun()
    else:
        name = st.selectbox("Name:", [m['name'] for m in st.session_state.m])
        pw = st.text_input("Passwort:", type="password")
        if st.button("Login"):
            u = next((m for m in st.session_state.m if m['name'] == name), None)
            if u and pw == u['passwort']:
                if pw == "Ordner": st.session_state.pw_modus = name
                else: st.session_state.user = name
                st.rerun()
    st.stop()

# Hauptteil
user = next(m for m in st.session_state.m if m['name'] == st.session_state.user)
st.sidebar.write(f"### {user['name']}")
if st.sidebar.button("Abmelden"): st.session_state.user = None; st.rerun()

st.title("FECG Ordner-Zentrale")

# Kalender
events = [{"title": f"🛠️ {get_dienst(datetime(2026, 6, 21).date() + timedelta(weeks=i))}", "start": (datetime(2026, 6, 21).date() + timedelta(weeks=i)).isoformat(), "allDay": True} for i in range(-4, 20)]
for n in st.session_state.n: events.append({"title": f"{n['icon']} {n['name']}: {n['text']}", "start": n['datum'], "allDay": True})

cal = calendar(events=events, options={"selectable": True})

if cal and "dateClick" in cal:
    datum = cal["dateClick"]["date"].split("T")[0]
    typ = st.radio("Was eintragen?", ["🔴 Abwesenheit", "📝 Info/Geburtstag/Kuchen"])
    text = st.text_input("Details:")
    if st.button("Speichern"):
        st.session_state.n.append({'datum': datum, 'name': user['name'], 'icon': '🔴' if 'Abw' in typ else '📝', 'text': text or "Abwesend"})
        save(DB_NOTIZEN, st.session_state.n)
        st.rerun()

# Gruppenleiter Funktionen
if user['rolle'] in ["Chef", "Teamleiter"]:
    st.write("---")
    st.write("### 💬 Gruppenleiter-Chat")
    for msg in st.session_state.c: st.write(f"*{msg['von']}*: {msg['text']}")
    if n_msg := st.chat_input("Nachricht..."):
        st.session_state.c.append({'von': user['name'], 'text': n_msg})
        save(DB_CHAT, st.session_state.c)
        st.rerun()
    
    st.write("### 📊 Abfragen")
    datum_abfrage = st.date_input("Datum für Abfrage:")
    if st.button("Abfrage erstellen"):
        st.session_state.a[str(datum_abfrage)] = "Offen"
        save(DB_ABFRAGEN, st.session_state.a)
        st.rerun()
