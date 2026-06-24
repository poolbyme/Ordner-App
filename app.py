[18:47, 24.6.2026] A.K: import streamlit as st
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

# ----------------------------------------------------
# SIDEBAR
# ----------------------------------------------------
st.sidebar.success(f"👤 {user['name']}")
if st.sidebar.button("🚪 Abmelden"): st.session_state.eingeloggt_als = None; st.rerun()

# ----------------------------------------------------
# HAUPTTEIL: KALENDER & PINNWAND
# ----------------------------------------------------
st.markdown("<h1 class='main-title'>⛪ FECG Ordner-Zentrale</h1>", unsafe_allow_html=True)
st.write("### 📅 Dienstplan & Pinnwand")
events = []
for i in range(-4, 20):
    w_start = datetime(2026, 6, 21).date() + timedelta(weeks=i)
    grp = get_dienst_gruppe(w_start)
    events.append({"title": f"🛠️ {grp}", "start": w_start.isoformat(), "allDay": True, "backgroundColor": "#1e3a8a"})

for n in st.session_state.kalender_notizen:
    events.append({"title": f"{n['icon']} {n['name']}: {n['text']}", "start": n['datum'], "allDay": True, "backgroundColor": "#ef4444" if n['typ'] == "🔴 Abwesenheit" else "#10b981"})

cal = calendar(events=events, options={"initialView": "dayGridMonth", "locale": "de", "selectable": True})

if cal and "dateClick" in cal:
    datum = cal["dateClick"]["date"].split("T")[0]
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.subheader(f"📌 Eintrag für {datum}")
    typ = st.radio("Eintragstyp:", ["🔴 Abwesenheit", "📝 Info / Notiz"])
    text = st.text_input("Details:") if "Info" in typ else ""
    if st.button("Speichern"):
        st.session_state.kalender_notizen.append({'datum': datum, 'name': user['name'], 'typ': typ, 'icon': '🔴' if 'Abw' in typ else '📝', 'text': text if text else "Abwesend"})
        speichere_json(DB_NOTIZEN, st.session_state.kalender_notizen)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------
# CHAT
# ----------------------------------------------------
if user['rolle'] in ["Chef", "Teamleiter"]:
    st.write("### 💬 Interner Gruppenleiter-Chat")
    for msg in st.session_state.leiter_chat:
        if msg['zeit'] == 'Info': st.markdown(f"<div class='chat-system'>{msg['text']}</div>", unsafe_allow_html=True)
        else: st.markdown(f"<div class='chat-bubble-other'><b>{msg['von']}</b>: {msg['text']}</div>", unsafe_allow_html=True)
    
    if n_msg := st.chat_input("Nachricht schreiben..."):
        st.session_state.leiter_chat.append({'von': user['name'], 'text': n_msg, 'zeit': datetime.now().strftime("%H:%M")})
        st.rerun()
[18:50, 24.6.2026] A.K: import streamlit as st
from datetime import datetime, timedelta
from streamlit_calendar import calendar
import os
import json

# --- KONFIGURATION ---
st.set_page_config(page_title="FECG Bruchmühlbach - Ordner Team", page_icon="⛪", layout="wide")

# --- CSS DESIGN ---
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

# --- DATENBANK FUNKTIONEN ---
DB_MITGLIEDER = "mitglieder_data.json"
DB_NOTIZEN = "kalender_notizen.json"

def lade_mitglieder():
    if os.path.exists(DB_MITGLIEDER):
        with open(DB_MITGLIEDER, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {'name': 'Komjagin Andreas', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Chef', 'passwort': 'Ordner'},
        {'name': 'Hauf Valintin', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
        {'name': 'Geier Enriko', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'}
    ]

def speichere_mitglieder(daten):
    with open(DB_MITGLIEDER, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=4)

def lade_notizen():
    if os.path.exists(DB_NOTIZEN):
        with open(DB_NOTIZEN, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def speichere_notizen(daten):
    with open(DB_NOTIZEN, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=4)

# --- SESSION INITIALISIERUNG ---
if "mitglieder" not in st.session_state: st.session_state.mitglieder = lade_mitglieder()
if "kalender_notizen" not in st.session_state: st.session_state.kalender_notizen = lade_notizen()
if "leiter_chat" not in st.session_state: st.session_state.leiter_chat = [{'von': 'System', 'text': 'Willkommen im Team-Chat!', 'zeit': 'Info'}]
if "eingeloggt_als" not in st.session_state: st.session_state.eingeloggt_als = None
if "passwort_aendern_modus" not in st.session_state: st.session_state.passwort_aendern_modus = None

# --- HILFSFUNKTIONEN ---
def get_dienst_gruppe(datum):
    basis = datetime(2026, 6, 21).date()
    gruppen = ["Gruppe 1 (Andreas K.)", "Gruppe 2 (Slawik V.)", "Gruppe 3 (Peter S.)"]
    return gruppen[((datum - basis).days // 7) % 3]

# --- LOGIN & REGISTRIERUNGSLOGIK ---
if st.session_state.eingeloggt_als is None:
    st.markdown("<h1 class='main-title'>⛪ FECG Login</h1>", unsafe_allow_html=True)
    
    # MODUS 1: Passwort ändern erzwingen
    if st.session_state.passwort_aendern_modus is not None:
        u_name = st.session_state.passwort_aendern_modus
        st.warning(f"⚠️ Willkommen {u_name}. Da du das Standardpasswort verwendest, musst du es jetzt ändern.")
        
        neues_pw = st.text_input("Neues persönliches Passwort:", type="password")
        if st.button("Passwort dauerhaft speichern und einloggen"):
            if neues_pw == "Ordner" or not neues_pw:
                st.error("Das neue Passwort darf nicht 'Ordner' sein!")
            else:
                # In der Liste suchen und speichern
                for m in st.session_state.mitglieder:
                    if m['name'] == u_name:
                        m['passwort'] = neues_pw
                speichere_mitglieder(st.session_state.mitglieder)
                st.session_state.eingeloggt_als = u_name
                st.session_state.passwort_aendern_modus = None
                st.rerun()
    
    # MODUS 2: Normales Login
    else:
        st.write("Bitte wähle deinen Namen aus:")
        namen = sorted([m['name'] for m in st.session_state.mitglieder])
        auswahl_name = st.selectbox("Name:", namen)
        eingabe_pw = st.text_input("Dein Passwort:", type="password")
        
        if st.button("Einloggen"):
            user = next((m for m in st.session_state.mitglieder if m['name'] == auswahl_name), None)
            if user and eingabe_pw == user['passwort']:
                if eingabe_pw == "Ordner":
                    st.session_state.passwort_aendern_modus = auswahl_name
                    st.rerun()
                else:
                    st.session_state.eingeloggt_als = auswahl_name
                    st.rerun()
            else:
                st.error("Login fehlgeschlagen. Überprüfe Passwort.")
    st.stop()

# --- HAUPTTEIL (Eingeloggt) ---
user = next(m for m in st.session_state.mitglieder if m['name'] == st.session_state.eingeloggt_als)

# Sidebar
st.sidebar.write(f"### 👤 {user['name']}")
st.sidebar.write(f"*Rolle:* {user['rolle']}")
if st.sidebar.button("🚪 Abmelden"):
    st.session_state.eingeloggt_als = None
    st.rerun()

st.markdown("<h1 class='main-title'>⛪ FECG Ordner-Zentrale</h1>", unsafe_allow_html=True)

# Kalender Sektion
st.write("### 📅 Dienstplan & Pinnwand")
kalender_events = []

# Dienstplan-Events generieren
for i in range(-4, 20):
    w_start = datetime(2026, 6, 21).date() + timedelta(weeks=i)
    grp = get_dienst_gruppe(w_start)
    kalender_events.append({
        "title": f"🛠️ {grp}",
        "start": w_start.isoformat(),
        "allDay": True,
        "backgroundColor": "#1e3a8a"
    })

# Notizen laden
for n in st.session_state.kalender_notizen:
    farbe = "#ef4444" if n['typ'] == "🔴 Abwesenheit" else "#10b981"
    kalender_events.append({
        "title": f"{n['icon']} {n['name']}: {n['text']}",
        "start": n['datum'],
        "allDay": True,
        "backgroundColor": farbe
    })

# Kalender Rendering
cal_resp = calendar(events=kalender_events, options={"initialView": "dayGridMonth", "locale": "de", "selectable": True})

# Interaktion
if cal_resp and "dateClick" in cal_resp:
    datum = cal_resp["dateClick"]["date"].split("T")[0]
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.subheader(f"Eintrag für den {datum}")
    typ = st.radio("Was willst du eintragen?", ["🔴 Abwesenheit", "📝 Info / Notiz"])
    text_info = st.text_input("Details (optional):") if "Info" in typ else ""
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Speichern"):
            neue_notiz = {
                'datum': datum, 
                'name': user['name'], 
                'typ': typ, 
                'icon': '🔴' if 'Abw' in typ else '📝', 
                'text': text_info if text_info else "Abwesend"
            }
            st.session_state.kalender_notizen.append(neue_notiz)
            speichere_notizen(st.session_state.kalender_notizen)
            st.rerun()
    with col2:
        if st.button("Fenster schließen"):
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Chat Sektion
if user['rolle'] in ["Chef", "Teamleiter"]:
    st.write("---")
    st.write("### 💬 Interner Gruppenleiter-Chat")
    for msg in st.session_state.leiter_chat:
        if msg['zeit'] == 'Info': st.markdown(f"<div class='chat-system'>{msg['text']}</div>", unsafe_allow_html=True)
        else: st.markdown(f"<div class='chat-bubble-other'><b>{msg['von']}</b>: {msg['text']}</div>", unsafe_allow_html=True)
    
    if n_msg := st.chat_input("Schreibe eine Nachricht..."):
        st.session_state.leiter_chat.append({'von': user['name'], 'text': n_msg, 'zeit': datetime.now().strftime("%H:%M")})
        st.rerun()

# --- WEITERE HUNDERTZEILEN AN LOGIK KÖNNTEN HIER FOLGEN ---
# Hier ist noch Platz für Erweiterungen, ohne dass die Grundlogik instabil wird
