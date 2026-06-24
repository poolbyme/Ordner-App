import streamlit as st
from datetime import datetime, timedelta
from streamlit_calendar import calendar

# App-Konfiguration mit Kreuz-Symbol
st.set_page_config(page_title="FECG Bruchmühlbach - Ordner Team", page_icon="⛪", layout="wide")

# CSS FÜR INDIVIDUELLES DESIGN UND FARBEN (FECG THEME)
st.markdown("""
<style>
    /* Hintergrundfarbe der App */
    .stApp {
        background-color: #f4f6f9;
    }
    /* Titel-Styling */
    .main-title {
        color: #1e3a8a;
        font-family: 'Arial', sans-serif;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
    }
    /* WhatsApp-Style für den Gruppenleiter-Chat */
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
    /* Stilvolle Kartenboxen für die Funktionen */
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

# 1. LIVE-SPEICHER INITIALISIEREN (DATEN BLEIBEN ERHALTEN)
if "mitglieder" not in st.session_state:
    st.session_state.mitglieder = [
        {'name': 'Komjagin Andreas', 'email': 'andreas@kirche.de', 'gruppe': 'Gruppe 1', 'rolle': 'Chef'},
        {'name': 'Hauf Valintin', 'email': 'valintin@kirche.de', 'gruppe': 'Gruppe 1', 'rolle': 'Mitarbeiter'},
        {'name': 'Geier Enriko', 'email': 'enriko@kirche.de', 'gruppe': 'Gruppe 1', 'rolle': 'Mitarbeiter'},
        {'name': 'Ilchuk Vasyl', 'email': 'vasyl@kirche.de', 'gruppe': 'Gruppe 1', 'rolle': 'Mitarbeiter'},
        {'name': 'Volkov Slawik', 'email': 'slawik@kirche.de', 'gruppe': 'Gruppe 2', 'rolle': 'Teamleiter'},
        {'name': 'Tissen Eduard', 'email': 'eduard@kirche.de', 'gruppe': 'Gruppe 2', 'rolle': 'Mitarbeiter'},
        {'name': 'Eberhart Wili', 'email': 'wili@kirche.de', 'gruppe': 'Gruppe 2', 'rolle': 'Mitarbeiter'},
        {'name': 'Paul Steffen', 'email': 'steffen@kirche.de', 'gruppe': 'Gruppe 2', 'rolle': 'Mitarbeiter'},
        {'name': 'Schäfer Peter', 'email': 'peter@kirche.de', 'gruppe': 'Gruppe 3', 'rolle': 'Teamleiter'},
        {'name': 'Akulenko Wili', 'email': 'wili.a@kirche.de', 'gruppe': 'Gruppe 3', 'rolle': 'Mitarbeiter'},
        {'name': 'Hermann Bogdan', 'email': 'bogdan@kirche.de', 'gruppe': 'Gruppe 3', 'rolle': 'Mitarbeiter'}
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

def get_dienst_gruppe(datum):
    basis_datum = datetime(2026, 6, 21).date()
    wochen = (datum - basis_datum).days // 7
    return ["Gruppe 1", "Gruppe 2", "Gruppe 3"][wochen % 3]

# APP OBERFLÄCHE
st.markdown("<h1 class='main-title'>⛪ FECG Bruchmühlbach — Ordner-Zentrale</h1>", unsafe_allow_html=True)

# TEST-LOGIN IN DER SEITENLEISTE
st.sidebar.header("🔐 Ansicht wechseln")
mitarbeiter_namen = [m['name'] for m in st.session_state.mitglieder]
ausgewaehlter_name = st.sidebar.selectbox("Du agierst gerade als:", mitarbeiter_namen, index=0)
user = next((m for m in st.session_state.mitglieder if m['name'] == ausgewaehlter_name), None)

st.sidebar.info(f"Rolle: {user['rolle']}\nTeam: {user['gruppe']}")

# ----------------------------------------------------
# INTERNER LEITER-CHAT (NUR FÜR CHEF & TEAMLEITER)
# ----------------------------------------------------
if user['rolle'] in ["Chef", "Teamleiter"]:
    st.write("### 💬 Interner Chat (Nur für Gruppenleiter sichtbar)")
    
    # Nachrichten rendern
    for msg in st.session_state.leiter_chat:
        if msg['zeit'] == 'Info':
            st.markdown(f"<div class='chat-system'>ℹ️ {msg['text']}</div>", unsafe_allow_html=True)
        elif msg['von'] == user['name']:
            st.markdown(f"<div class='chat-bubble-user'><b>Du</b> ({msg['zeit']})<br>{msg['text']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-bubble-other'><b>{msg['von']}</b> ({msg['zeit']})<br>{msg['text']}</div>", unsafe_allow_html=True)
            
    # Eingabe-Formular (leert sich automatisch)
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
dienst_gruppe = get_dienst_gruppe(aktueller_sonntag)

st.success(f"📢 *Aktuelle Woche:* {dienst_gruppe} hat diesen Sonntag regulären Dienst.")

kalender_events = []
start_sonntag = datetime(2026, 6, 21).date()
for i in range(8):
    w_start = start_sonntag + timedelta(weeks=i)
    w_ende = w_start + timedelta(days=6)
    grp = get_dienst_gruppe(w_start)
    kalender_events.append({
        "title": f"🛠️ Dienst: {grp}",
        "start": w_start.isoformat(),
        "end": (w_ende + timedelta(days=1)).isoformat(),
        "backgroundColor": "#1e3a8a" if grp == "Gruppe 1" else ("#3b82f6" if grp == "Gruppe 2" else "#93c5fd"),
        "allDay": True
    })

for u in st.session_state.urlaube:
    kalender_events.append({
        "title": f"🌴 Urlaub: {u['name']}",
        "start": u['von'].isoformat() if not isinstance(u['von'], str) else u['von'],
        "end": (u['bis'] + timedelta(days=1)).isoformat() if not isinstance(u['bis'], str) else u['bis'],
        "backgroundColor": "#ef4444",
        "allDay": True
    })

calendar(events=kalender_events, options={"initialView": "dayGridMonth", "locale": "de"}, key="calendar")

st.write("---")

# ----------------------------------------------------
# 2. DAS AKTIVE RÜCKMELDE-SYSTEM (Für Mitarbeiter)
# ----------------------------------------------------
st.write("### 📋 Aktuelle Anwesenheits-Abfragen deiner Gruppe")
abfrage_key = f"{user['gruppe']}_{aktueller_sonntag.strftime('%Y-%m-%d')}"

if abfrage_key in st.session_state.gruppen_abfragen:
    abfrage = st.session_state.gruppen_abfragen[abfrage_key]
    st.info(f"➔ Dein Gruppenleiter fragt ab: *Wer ist am Sonntag, den {aktueller_sonntag.strftime('%d.%m.%Y')} da?*")
    
    aktueller_status = abfrage['rueckmeldungen'].get(user['name'], "Noch keine Antwort")
    st.write(f"Dein aktueller Status: *{aktueller_status}*")
    
    col_da, col_weg = st.columns(2)
    with col_da:
        if st.button("🟢 Ich bin verbindlich DA", key="btn_da"):
            abfrage['rueckmeldungen'][user['name']] = "🟢 Bin da"
            st.rerun()
    with col_weg:
        if st.button("🔴 Ich bin NICHT da", key="btn_weg"):
            abfrage['rueckmeldungen'][user['name']] = "🔴 Nicht da"
            st.rerun()
else:
    st.write("Für diesen Sonntag steht aktuell keine aktive Abfrage von deinem Gruppenleiter an.")

st.write("---")

# ----------------------------------------------------
# 3. KARTEN-LAYOUT FÜR LEITER-WERKZEUGE & URLAUB
# ----------------------------------------------------
col_box1, col_box2 = st.columns(2)

with col_box1:
    if user['rolle'] in ["Chef", "Teamleiter"]:
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        st.subheader(f"🛠️ Leiter-Werkzeuge ({user['gruppe']})")
        
        if st.button(f"🚀 Abfrage starten für Sonntag, {aktueller_sonntag.strftime('%d.%m.%Y')}"):
            st.session_state.gruppen_abfragen[abfrage_key] = {'status': 'offen', 'rueckmeldungen': {}}
            st.success("Abfrage freigeschaltet!")
            st.rerun()
            
        if abfrage_key in st.session_state.gruppen_abfragen:
            st.write("#### 📊 Rückmeldungen deines Teams:")
            team = [m for m in st.session_state.mitglieder if m['gruppe'] == user['gruppe']]
            
            fehlende_leute = 0
            for t_mitglied in team:
                status = st.session_state.gruppen_abfragen[abfrage_key]['rueckmeldungen'].get(t_mitglied['name'], "⏳ Keine Rückmeldung")
                st.text(f"• {t_mitglied['name']}: {status}")
                if "Nicht da" in status:
                    fehlende_leute += 1
                    
            if fehlende_leute > 0:
                st.error(f"Es fehlen {fehlende_leute} Person(en)!")
                if st.button("🚨 Hilfe anfordern: Ersatz suchen"):
                    st.session_state.ersatz_suchen.append({
                        'von_gruppe': user['gruppe'],
                        'datum': aktueller_sonntag,
                        'anzahl': fehlende_leute,
                        'helfer': []
                    })
                    st.success("Hilferuf gestartet!")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Hier haben nur Gruppenleiter Zugriff auf die Auswertung.")

with col_box2:
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.subheader("🌴 Abwesenheit eintragen")
    u_von = st.date_input("Urlaub von:", value=heute, key="u_von")
    u_bis = st.date_input("Urlaub bis:", value=heute + timedelta(days=7), key="u_bis")
    if st.button("Urlaub im Kalender eintragen"):
        st.session_state.urlaube.append({'name': user['name'], 'email': user['email'], 'von': u_von, 'bis': u_bis})
        st.success("Urlaub erfolgreich eingetragen!")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.write("---")

# ----------------------------------------------------
# 4. GRUPPENÜBERGREIFENDE ERSATZSUCHE
# ----------------------------------------------------
st.write("### 📢 Gruppenübergreifende Notfall-Suchen")
aktive_ersatz_suchen = [s for s in st.session_state.ersatz_suchen if user['gruppe'] != s['von_gruppe']]

if not aktive_ersatz_suchen:
    st.write("Keine offenen Ersatzsuchen aus anderen Gruppen vorhanden.")
else:
    for idx, suche in enumerate(st.session_state.ersatz_suchen):
        if user['gruppe'] != suche['von_gruppe']:
            st.warning(f"⚠️ *{suche['von_gruppe']}* sucht dringend {suche['anzahl']} Ersatz-Ordner für Sonntag, {suche['datum'].strftime('%d.%m.%Y')}!")
            st.write(f"Bereits zugesagt: {', '.join(suche['helfer']) if suche['helfer'] else 'Niemand'}")
            
            if user['name'] in suche['helfer']:
                st.success("✅ Du hast hier bereits verbindlich zugesagt!")
            else:
                if st.button(f"🤝 Als {user['name']} verbindlich einspringen", key=f"ersatz_{idx}"):
                    suche['helfer'].append(user['name'])
                    st.rerun()
