import streamlit as st
from datetime import datetime, timedelta
from streamlit_calendar import calendar

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
# AUTOMATISCHE WHATSAPP-FUNKTION
# ----------------------------------------------------
def sende_whatsapp_benachrichtigung(nachrichtstext):
    # Hier wird später eure Gruppen-API verknüpft!
    try:
        pass
    except Exception as e:
        print(f"WhatsApp-Fehler: {e}")

# 1. LIVE-SPEICHER INITIALISIEREN
if "mitglieder" not in st.session_state:
    st.session_state.mitglieder = [
        {'name': 'Komjagin Andreas', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Chef'},
        {'name': 'Hauf Valintin', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter'},
        {'name': 'Geier Enriko', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter'},
        {'name': 'Ilchuk Vasyl', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter'},
        {'name': 'Volkov Slawik', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Teamleiter'},
        {'name': 'Tissen Eduard', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Mitarbeiter'},
        {'name': 'Eberhart Wili', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Mitarbeiter'},
        {'name': 'Paul Steffen', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Mitarbeiter'},
        {'name': 'Schäfer Peter', 'gruppe': 'Gruppe 3 (Peter S.)', 'rolle': 'Teamleiter'},
        {'name': 'Akulenko Wili', 'gruppe': 'Gruppe 3 (Peter S.)', 'rolle': 'Mitarbeiter'},
        {'name': 'Hermann Bogdan', 'gruppe': 'Gruppe 3 (Peter S.)', 'rolle': 'Mitarbeiter'}
    ]

if "urlaube" not in st.session_state:
    st.session_state.urlaube = []

if "gruppen_abfragen" not in st.session_state:
    st.session_state.gruppen_abfragen = {}

if "ersatz_suchen" not in st.session_state:
    st.session_state.ersatz_suchen = []

if "leiter_chat" not in st.session_state:
    st.session_state.leiter_chat = [
        {'von': 'System', 'text': 'Willkommen im internen Chat der Gruppenleiter der FECG Bruchmühlbach!', 'zeit': 'Info'}
    ]

if "eingeloggt_als" not in st.session_state:
    st.session_state.eingeloggt_als = None

def get_dienst_gruppe(datum):
    basis_datum = datetime(2026, 6, 21).date()
    wochen = (datum - basis_datum).days // 7
    return ["Gruppe 1 (Andreas K.)", "Gruppe 2 (Slawik V.)", "Gruppe 3 (Peter S.)"][wochen % 3]


# ----------------------------------------------------
# LOGIN-PRÜFUNG
# ----------------------------------------------------
if st.session_state.eingeloggt_als is None:
    st.markdown("<h1 class='main-title'>⛪ FECG Bruchmühlbach — Ordner App Login</h1>", unsafe_allow_html=True)
    
    col_login, _ = st.columns([1, 1])
    with col_login:
        st.write("Bitte wähle deinen Namen aus und gib das gemeinsame Passwort ein.")
        alle_namen = [m['name'] for m in st.session_state.mitglieder]
        login_name = st.selectbox("Dein Name:", options=alle_namen)
        passwort_eingabe = st.text_input("Passwort (Zentrale):", type="password")
        
        if st.button("Einloggen", use_container_width=True):
            if passwort_eingabe == "Ordner":
                st.session_state.eingeloggt_als = login_name
                st.success(f"Erfolgreich eingeloggt!")
                st.rerun()
            else:
                st.error("Falsches Passwort!")
    st.stop()

user = next((m for m in st.session_state.mitglieder if m['name'] == st.session_state.eingeloggt_als), None)


# ----------------------------------------------------
# APP OBERFLÄCHE (NACH LOGIN)
# ----------------------------------------------------
st.markdown("<h1 class='main-title'>⛪ FECG Bruchmühlbach — Ordner-Zentrale</h1>", unsafe_allow_html=True)

st.sidebar.header("👤 Dein Profil")
st.sidebar.success(f"Eingeloggt: *{user['name']}*")
st.sidebar.info(f"Rolle: {user['rolle']}\nTeam: {user['gruppe']}")

if st.sidebar.button("🚪 Abmelden", use_container_width=True):
    st.session_state.eingeloggt_als = None
    st.rerun()

# ----------------------------------------------------
# INTERNER LEITER-CHAT
# ----------------------------------------------------
if user['rolle'] in ["Chef", "Teamleiter"]:
    st.write("### 💬 Interner Chat (Nur für Gruppenleiter sichtbar)")
    
    for msg in st.session_state.leiter_chat:
        if msg['zeit'] == 'Info':
            st.markdown(f"<div class='chat-system'>ℹ️ {msg['text']}</div>", unsafe_allow_html=True)
        elif msg['von'] == user['name']:
            st.markdown(f"<div class='chat-bubble-user'><b>Du</b> ({msg['zeit']})<br>{msg['text']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-bubble-other'><b>{msg['von']}</b> ({msg['zeit']})<br>{msg['text']}</div>", unsafe_allow_html=True)
            
    with st.form(key="chat_form", clear_on_submit=True):
        col_msg, col_btn = st.columns([4, 1])
        with col_msg:
            neue_nachricht = st.text_input("Nachricht schreiben...", placeholder="Schreiben und Enter drücken...")
        with col_btn:
            submit_button = st.form_submit_button("Senden", use_container_width=True)
            
        if submit_button and neue_nachricht.strip():
            jetzt_zeit = datetime.now().strftime("%H:%M")
            st.session_state.leiter_chat.append({
                'von': user['name'],
                'text': neue_nachricht,
                'zeit': jetzt_zeit
            })
            st.rerun()
    st.write("---")

# ----------------------------------------------------
# 1. HAUPT-ÜBERSICHT & DIENSTPLAN-KALENDER
# ----------------------------------------------------
st.write("### 📅 Dienstplan-Übersicht")
heute = datetime.now().date()
aktueller_sonntag = heute - timedelta(days=(heute.weekday() + 1) % 7)
if heute.weekday() == 6:
    aktueller_sonntag = heute
    
dienst_gruppe = get_dienst_gruppe(aktueller_sonntag)
st.success(f"📢 *Aktuelle Woche:* {dienst_gruppe} hat Dienst (von vergangenem Sonntag bis Samstag).")

kalender_events = []

start_basis = datetime(2026, 6, 21).date()
for i in range(-4, 150):
    w_sonntag = start_basis + timedelta(weeks=i)
    w_samstag = w_sonntag + timedelta(days=6)
    grp = get_dienst_gruppe(w_sonntag)
    
    if "Andreas K." in grp:
        farbe = "#1e3a8a"  # Dunkelblau
    elif "Slawik V." in grp:
        farbe = "#8b5cf6"  # Hellviolett
    else:
        farbe = "#f97316"  # Orange
        
    kalender_events.append({
        "title": f"🛠️ {grp}",
        "start": w_sonntag.isoformat(),
        "end": (w_samstag + timedelta(days=1)).isoformat(),
        "backgroundColor": farbe,
        "borderColor": farbe,
        "allDay": True
    })

# INTELLIGENTE URLAUBS-LOGIK
urlaubs_tage_zaehler = {}
for u in st.session_state.urlaube:
    u_mitglied = next((m for m in st.session_state.mitglieder if m['name'] == u['name']), None)
    if u_mitglied:
        akt_tag = u['von']
        while akt_tag <= u['bis']:
            dienst_gruppe_an_dem_tag = get_dienst_gruppe(akt_tag)
            if u_mitglied['gruppe'] == dienst_gruppe_an_dem_tag:
                if akt_tag not in urlaubs_tage_zaehler:
                    urlaubs_tage_zaehler[akt_tag] = []
                if u['name'] not in urlaubs_tage_zaehler[akt_tag]:
                    urlaubs_tage_zaehler[akt_tag].append(u['name'])
            akt_tag += timedelta(days=1)

for tag, namen_liste in urlaubs_tage_zaehler.items():
    anzahl_fehlende = len(namen_liste)
    namen_text = ", ".join(namen_liste)
    
    if anzahl_fehlende == 1:
        u_farbe = "#eab308"  # Gelb
        u_titel = f"⚠️ Urlaub (1/4 fehlt): {namen_text}"
    else:
        u_farbe = "#ef4444"  # Rot
        u_titel = f"🚨 ENG (Urlaub {anzahl_fehlende}/4): {namen_text}"
        
    kalender_events.append({
        "title": u_titel,
        "start": tag.isoformat(),
        "end": (tag + timedelta(days=1)).isoformat(),
        "backgroundColor": u_farbe,
        "borderColor": u_farbe,
        "allDay": True
    })

calendar(events=kalender_events, options={"initialView": "dayGridMonth", "locale": "de"}, key="fecg_calendar")
st.write("---")

# ----------------------------------------------------
# 2. CRITICAL UPDATE: EINMALIGES ANWESENHEITS-RÜCKMELDE-SYSTEM
# ----------------------------------------------------
st.write("### 📋 Aktuelle Anwesenheits-Abfragen deiner Gruppe")

# Wir suchen nach JEDER aktiven Abfrage, um zu sehen, ob der Nutzer antworten muss
abfragen_gefunden = False
for k_abfrage, v_abfrage in list(st.session_state.gruppen_abfragen.items()):
    # Betrifft diese Abfrage die Gruppe des angemeldeten Nutzers?
    if k_abfrage.startswith(user['gruppe']):
        # Hat dieser Nutzer bereits geantwortet?
        if user['name'] in v_abfrage['rueckmeldungen']:
            # WICHTIG: Wenn er schon geantwortet hat, verschwindet die Abfrage für ihn komplett!
            continue
        
        abfragen_gefunden = True
        datum_str = k_abfrage.split("_")[1]
        ziel_datum = datetime.strptime(datum_str, "%Y-%m-%d").date()
        
        st.info(f"➔ *Offene Abfrage:* Wer ist am Sonntag, den {ziel_datum.strftime('%d.%m.%Y')} einsatzbereit?")
        
        col_da, col_weg = st.columns(2)
        with col_da:
            if st.button("🟢 Ich bin verbindlich DA", key=f"da_{k_abfrage}"):
                v_ab
