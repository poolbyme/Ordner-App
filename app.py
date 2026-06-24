import streamlit as st
from datetime import datetime, timedelta
from streamlit_calendar import calendar

st.set_page_config(page_title="Ordner Team App", page_icon="⛪", layout="wide")

# LIVE-SPEICHER INITIALISIEREN
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
    st.session_state.urlaube = [
        {'name': 'Hauf Valintin', 'email': 'valintin@kirche.de', 'von': '2026-06-22', 'bis': '2026-06-25'},
        {'name': 'Geier Enriko', 'email': 'enriko@kirche.de', 'von': '2026-06-23', 'bis': '2026-06-26'}
    ]

if "anfragen" not in st.session_state:
    st.session_state.anfragen = []

def get_dienst_gruppe(datum):
    basis_datum = datetime(2026, 6, 21).date()
    wochen = (datum - basis_datum).days // 7
    return ["Gruppe 1", "Gruppe 2", "Gruppe 3"][wochen % 3]

st.title("⛪ Ordner-Team Kalender & Einsatzplan")

st.sidebar.header("🔐 Login")
user_email = st.sidebar.text_input("Deine E-Mail:", value="andreas@kirche.de").strip()
user = next((m for m in st.session_state.mitglieder if m['email'] == user_email), None)

if user:
    st.sidebar.success(f"Hallo {user['name']}!\n{user['rolle']} ({user['gruppe']})")
    
    st.write("### 📅 Dein Team-Kalender")
    st.info("Grün = Alles super | Gelb = 1 Person fehlt | Rot = Mindestens 2 Personen fehlen | Blau = Eingetragene Urlaube")
    
    kalender_events = []
    start_sonntag = datetime(2026, 6, 21).date()
    
    for i in range(12):
        woche_start = start_sonntag + timedelta(weeks=i)
        woche_ende = woche_start + timedelta(days=6)
        aktive_gruppe = get_dienst_gruppe(woche_start)
        
        g_mitglieder = [m['email'] for m in st.session_state.mitglieder if m['gruppe'] == aktive_gruppe]
        abwesende = 0
        for url in st.session_state.urlaube:
            if url['email'] in g_mitglieder:
                u_von = datetime.strptime(url['von'], '%Y-%m-%d').date() if isinstance(url['von'], str) else url['von']
                u_bis = datetime.strptime(url['bis'], '%Y-%m-%d').date() if isinstance(url['bis'], str) else url['bis']
                if not (u_von > woche_ende or u_bis < woche_start):
                    abwesende += 1
        
        if abwesende == 0:
            farbe = "#28a745"
            titel = f"🟢 {aktive_gruppe} Dienst"
        elif abwesende == 1:
            farbe = "#ffc107"
            titel = f"🟡 {aktive_gruppe} (1 fehlt!)"
        else:
            farbe = "#dc3545"
            titel = f"🔴 {aktive_gruppe} ({abwesende} fehlen!)"
            
        kalender_events.append({
            "title": titel,
            "start": woche_start.isoformat(),
            "end": (woche_ende + timedelta(days=1)).isoformat(),
            "backgroundColor": farbe,
            "borderColor": farbe,
            "allDay": True
        })

    for url in st.session_state.urlaube:
        u_von = datetime.strptime(url['von'], '%Y-%m-%d').date() if isinstance(url['von'], str) else url['von']
        u_bis = datetime.strptime(url['bis'], '%Y-%m-%d').date() if isinstance(url['bis'], str) else url['bis']
        kalender_events.append({
            "title": f"🌴 Urlaub: {url['name']}",
            "start": u_von.isoformat(),
            "end": (u_bis + timedelta(days=1)).isoformat(),
            "backgroundColor": "#17a2b8",
            "borderColor": "#17a2b8",
            "allDay": True
        })

    kalender_optionen = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"},
        "initialView": "dayGridMonth",
        "locale": "de"
    }
    calendar(events=kalender_events, options=kalender_optionen, key="team_kalender")

    st.write("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌴 Abwesenheit / Urlaub melden")
        heute = datetime.now().date()
        von_tag = st.date_input("Urlaub von:", value=heute, key="u_von")
        bis_tag = st.date_input("Urlaub bis:", value=heute + timedelta(days=7), key="u_bis")
        
        if st.button("Urlaub verbindlich speichern"):
            st.session_state.urlaube.append({'name': user['name'], 'email': user_email, 'von': von_tag, 'bis': bis_tag})
            st.success("Dein Urlaub wurde eingetragen!")
            st.rerun()

    with col2:
        st.subheader("📢 Offene Hilferufe / Vertretungen")
        aktive_anfragen = [a for a in st.session_state.anfragen if a['gesucht'] > 0]
        if not aktive_anfragen:
            st.write("Aktuell wird keine Hilfe gesucht. Alles stabil!")
        else:
            for idx, anfrage in enumerate(st.session_state.anfragen):
                if anfrage['gesucht'] > 0:
                    st.warning(f"*Ersatz gesucht für: {anfrage['datum'].strftime('%d.%m.%Y')}* ({anfrage['typ']})")
                    st.write(f"Noch benötigt: {anfrage['gesucht']} Ordner")
                    if st.button(f"🤝 Verbindlich zusagen", key=f"help_{idx}"):
                        anfrage['gesucht'] -= 1
                        anfrage['helfer'].append(user['name'])
                        st.rerun()

    if user['rolle'] in ["Chef", "Teamleiter"]:
        st.write("---")
        st.subheader("🛠️ Leiter-Menü")
        c1, c2 = st.columns(2)
        with c1:
            st.write("*🆘 Neue Suche starten*")
            anfrage_typ = st.radio("Typ:", ["Ausfall im Team", "Sondereinsatz / Feiertag"])
            such_datum = st.date_input("Datum:", value=heute + timedelta(days=1))
            anzahl_helfer = st.number_input("Anzahl Helfer:", min_value=1, max_value=5, value=1)
            if st.button("Anfrage losschicken"):
                st.session_state.anfragen.append({'typ': anfrage_typ, 'datum': such_datum, 'gesucht': anzahl_helfer, 'helfer': []})
                st.success("Anfrage aktiv!")
                st.rerun()
        with c2:
            if user['rolle'] == "Chef":
                st.write("*➕ Neuen Mitarbeiter anlegen*")
                n_name = st.text_input("Name:")
                n_email = st.text_input("E-Mail:")
                n_grp = st.selectbox("Gruppe:", ["Gruppe 1", "Gruppe 2", "Gruppe 3"])
                if st.button("Mitarbeiter speichern"):
                    st.session_state.mitglieder.append({'name': n_name, 'email': n_email, 'gruppe': n_grp, 'rolle': 'Mitarbeiter'})
                    st.success("Gespeichert!")
                    st.rerun()
else:
    st.sidebar.error("E-Mail nicht im System.")
