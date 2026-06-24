import streamlit as st
from datetime import datetime, timedelta
from streamlit_calendar import calendar

st.set_page_config(page_title="Ordner Team App", page_icon="⛪", layout="wide")

# 1. LIVE-SPEICHER INITIALISIEREN
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

# NEU: Gemeinsamer Chat-Verlauf für alle Gruppenleiter & Chef
if "leiter_chat" not in st.session_state:
    st.session_state.leiter_chat = [
        {'von': 'System', 'text': 'Willkommen im internen Chat der Gruppenleiter!', 'zeit': 'Info'}
    ]

def get_dienst_gruppe(datum):
    basis_datum = datetime(2026, 6, 21).date()
    wochen = (datum - basis_datum).days // 7
    return ["Gruppe 1", "Gruppe 2", "Gruppe 3"][wochen % 3]

st.title("⛪ Ordner-Team Planer & Leiter-Zentrale")

# TEST-LOGIN IN DER SEITENLEISTE
st.sidebar.header("🔐 Ansicht wechseln")
mitarbeiter_namen = [m['name'] for m in st.session_state.mitglieder]
ausgewaehlter_name = st.sidebar.selectbox("Du agierst gerade als:", mitarbeiter_namen, index=0)
user = next((m for m in st.session_state.mitglieder if m['name'] == ausgewaehlter_name), None)

st.sidebar.info(f"Rolle: {user['rolle']}\nTeam: {user['gruppe']}")

# ----------------------------------------------------
# NEU: DER INTERNE LEITER-CHAT (NUR FÜR CHEF & TEAMLEITER)
# ----------------------------------------------------
if user['rolle'] in ["Chef", "Teamleiter"]:
    st.write("### 💬 Interner Chat (Nur für Gruppenleiter sichtbar)")
    
    # Chat-Box mit Scrollfunktion simulieren
    chat_box = ""
    for msg in st.session_state.leiter_chat:
        if msg['zeit'] == 'Info':
            chat_box += f"ℹ️ {msg['text']}\n\n"
        else:
            chat_box += f"👤 {msg['von']} ({msg['zeit']}):\n➔ {msg['text']}\n\n"
    
    st.text_area("Nachrichtenverlauf:", value=chat_box, height=200, disabled=True)
    
    # Eingabe für neue Nachrichten
    col_msg, col_btn = st.columns([4, 1])
    with col_msg:
        neue_nachricht = st.text_input("Nachricht schreiben...", placeholder="Schreib etwas wie in WhatsApp...", key="chat_input")
    with col_btn:
        st.write("##") # Abstandshalter für den Button
        if st.button("Senden", use_container_width=True):
            if neue_nachricht.strip():
                jetzt_zeit = datetime.now().strftime("%H:%M")
                st.session_state.leiter_chat.append({
                    'von': user['name'],
                    'text': neue_nachricht,
                    'zeit': jetzt_zeit
                })
                st.rerun()
    st.write("---")

# ----------------------------------------------------
# 1. HAUPT-ÜBERSICHT & KALENDER
# ----------------------------------------------------
st.write("### 📅 Dienstplan-Übersicht")
heute = datetime.now().date()
aktueller_sonntag = heute - timedelta(days=(heute.weekday() + 1) % 7)
dienst_gruppe = get_dienst_gruppe(aktueller_sonntag)

st.success(f"📢 *Aktuelle Woche:* {dienst_gruppe} hat regulären Dienst.")

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
        "backgroundColor": "#28a745" if grp == "Gruppe 1" else ("#17a2b8" if grp == "Gruppe 2" else "#ffc107"),
        "allDay": True
    })

for u in st.session_state.urlaube:
    kalender_events.append({
        "title": f"🌴 Urlaub: {u['name']}",
        "start": u['von'].isoformat() if not isinstance(u['von'], str) else u['von'],
        "end": (u['bis'] + timedelta(days=1)).isoformat() if not isinstance(u['bis'], str) else u['bis'],
        "backgroundColor": "#dc3545",
        "allDay": True
    })

calendar(events=kalender_events, options={"initialView": "dayGridMonth", "locale": "de"}, key="calendar")

st.write("---")

# ----------------------------------------------------
# 2. DAS AKTIVE RÜCKMELDE-SYSTEM (Für den Sonntag)
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
# 3. INTERNES GRUPPENLEITER-WERKZEUG
# ----------------------------------------------------
if user['rolle'] in ["Chef", "Teamleiter"]:
    st.subheader(f"🛠️ Leiter-Werkzeuge ({user['gruppe']})")
    
    if st.button(f"🚀 Abfrage starten für Sonntag, {aktueller_sonntag.strftime('%d.%m.%Y')}"):
        st.session_state.gruppen_abfragen[abfrage_key] = {'status': 'offen', 'rueckmeldungen': {}}
        st.success("Abfrage wurde für deine Gruppenmitglieder freigeschaltet!")
        st.rerun()
        
    if abfrage_key in st.session_state.gruppen_abfragen:
        st.write("#### 📊 Aktuelle Rückmeldungen deines Teams:")
        team = [m for m in st.session_state.mitglieder if m['gruppe'] == user['gruppe']]
        
        fehlende_leute = 0
        for t_mitglied in team:
            status = st.session_state.gruppen_abfragen[abfrage_key]['rueckmeldungen'].get(t_mitglied['name'], "⏳ Keine Rückmeldung")
            st.text(f"• {t_mitglied['name']}: {status}")
            if "Nicht da" in status:
                fehlende_leute += 1
                
        if fehlende_leute > 0:
            st.error(f"Achtung: Es fehlen {fehlende_leute} Person(en)!")
            if st.button("🚨 Hilfe anfordern: Ersatz in anderen Gruppen suchen"):
                st.session_state.ersatz_suchen.append({
                    'von_gruppe': user['gruppe'],
                    'datum': aktueller_sonntag,
                    'anzahl': fehlende_leute,
                    'helfer': []
                })
                st.success("Hilferuf wurde gestartet!")
                st.rerun()
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

# ----------------------------------------------------
# 5. LANGFRISTIGER URLAUB
# ----------------------------------------------------
st.write("---")
st.subheader("🌴 Sommerurlaub / Langfristige Abwesenheit eintragen")
u_von = st.date_input("Urlaub von:", value=heute, key="u_von")
u_bis = st.date_input("Urlaub bis:", value=heute + timedelta(days=7), key="u_bis")
if st.button("Urlaub im Kalender eintragen"):
    st.session_state.urlaube.append({'name': user['name'], 'email': user['email'], 'von': u_von, 'bis': u_bis})
    st.success("Urlaub erfolgreich eingetragen!")
    st.rerun()
