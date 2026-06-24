import streamlit as st
from datetime import datetime, timedelta
from streamlit_calendar import calendar
import os
import json

# App-Konfiguration
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
    .section-divider {
        margin-top: 40px;
        margin-bottom: 20px;
        border-bottom: 2px dashed #cbd5e1;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# MITGLIEDER SPEICHERN MIT GEBURTSTAGS-SUPPORT
# ----------------------------------------------------
DB_FILE = "mitglieder_data.json"

def hole_standard_liste():
    # Neues Feld: 'geburtstag' (Format: YYYY-MM-DD oder leerer String)
    return [
        {'name': 'Komjagin Andreas', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Chef', 'passwort': 'Ordner', 'telefon': '', 'anschrift': '', 'infos': '', 'geburtstag': ''},
        {'name': 'Hauf Valintin', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner', 'telefon': '', 'anschrift': '', 'infos': '', 'geburtstag': ''},
        {'name': 'Geier Enriko', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner', 'telefon': '', 'anschrift': '', 'infos': '', 'geburtstag': ''},
        {'name': 'Ilchuk Vasyl', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner', 'telefon': '', 'anschrift': '', 'infos': '', 'geburtstag': ''},
        {'name': 'Volkov Slawik', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Teamleiter', 'passwort': 'Ordner', 'telefon': '', 'anschrift': '', 'infos': '', 'geburtstag': ''},
        {'name': 'Tissen Eduard', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner', 'telefon': '', 'anschrift': '', 'infos': '', 'geburtstag': ''},
        {'name': 'Eberhart Wili', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner', 'telefon': '', 'anschrift': '', 'infos': '', 'geburtstag': ''},
        {'name': 'Paul Steffen', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner', 'telefon': '', 'anschrift': '', 'infos': '', 'geburtstag': ''},
        {'name': 'Schäfer Peter', 'gruppe': 'Gruppe 3 (Peter S.)', 'rolle': 'Teamleiter', 'passwort': 'Ordner', 'telefon': '', 'anschrift': '', 'infos': '', 'geburtstag': ''},
        {'name': 'Akulenko Wili', 'gruppe': 'Gruppe 3 (Peter S.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner', 'telefon': '', 'anschrift': '', 'infos': '', 'geburtstag': ''},
        {'name': 'Hermann Bogdan', 'gruppe': 'Gruppe 3 (Peter S.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner', 'telefon': '', 'anschrift': '', 'infos': '', 'geburtstag': ''}
    ]

def speichere_mitglieder(liste):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=4)

if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        st.session_state.mitglieder = json.load(f)
        for m in st.session_state.mitglieder:
            if 'telefon' not in m: m['telefon'] = ''
            if 'anschrift' not in m: m['anschrift'] = ''
            if 'infos' not in m: m['infos'] = ''
            if 'geburtstag' not in m: m['geburtstag'] = ''
else:
    st.session_state.mitglieder = hole_standard_liste()
    speichere_mitglieder(st.session_state.mitglieder)

# Weitere Speicher initialisieren
if "urlaube" not in st.session_state: st.session_state.urlaube = []
if "gruppen_abfragen" not in st.session_state: st.session_state.gruppen_abfragen = {}
if "ersatz_suchen" not in st.session_state: st.session_state.ersatz_suchen = []
if "leiter_chat" not in st.session_state: st.session_state.leiter_chat = [{'von': 'System', 'text': 'Willkommen im internen Chat!', 'zeit': 'Info'}]
if "eingeloggt_als" not in st.session_state: st.session_state.eingeloggt_als = None
if "passwort_aendern_fuer" not in st.session_state: st.session_state.passwort_aendern_fuer = None
if "show_abfrage_form" not in st.session_state: st.session_state.show_abfrage_form = False
if "abfrage_typ" not in st.session_state: st.session_state.abfrage_typ = None
if "show_urlaub_form" not in st.session_state: st.session_state.show_urlaub_form = False

def get_dienst_gruppe(datum):
    basis_datum = datetime(2026, 6, 21).date()
    wochen = (datum - basis_datum).days // 7
    return ["Gruppe 1 (Andreas K.)", "Gruppe 2 (Slawik V.)", "Gruppe 3 (Peter S.)"][wochen % 3]

# ----------------------------------------------------
# LOGIN-SYSTEM
# ----------------------------------------------------
if st.session_state.eingeloggt_als is None:
    st.markdown("<h1 class='main-title'>⛪ FECG Bruchmühlbach — Ordner App Login</h1>", unsafe_allow_html=True)
    
    if st.session_state.passwort_aendern_fuer is not None:
        u_name = st.session_state.passwort_aendern_fuer
        st.warning(f"⚠️ Hallo **{u_name}**! Bitte vergebe jetzt dein persönliches Passwort.")
        neues_pw = st.text_input("Neues Passwort:", type="password", key="new_pw_input")
        neues_pw_wdhl = st.text_input("Passwort wiederholen:", type="password", key="new_pw_confirm")
        
        if st.button("Sichern & Einloggen", use_container_width=True):
            if neues_pw == "Ordner" or neues_pw.strip() == "":
                st.error("Ungültiges Passwort!")
            elif neues_pw != neues_pw_wdhl:
                st.error("Die Passwörter stimmen nicht überein!")
            else:
                for m in st.session_state.mitglieder:
                    if m['name'] == u_name: m['passwort'] = neues_pw
                speichere_mitglieder(st.session_state.mitglieder)
                st.session_state.eingeloggt_als = u_name
                st.session_state.passwort_aendern_fuer = None
                st.rerun()
        st.stop()

    else:
        col_login, _ = st.columns([1, 1])
        with col_login:
            alle_namen = sorted([m['name'] for m in st.session_state.mitglieder])
            login_name = st.selectbox("Dein Name:", options=alle_namen)
            passwort_eingabe = st.text_input("Dein Passwort:", type="password")
            
            if st.button("Einloggen", use_container_width=True):
                user_check = next((m for m in st.session_state.mitglieder if m['name'] == login_name), None)
                if user_check and passwort_eingabe == user_check['passwort']:
                    if passwort_eingabe == "Ordner":
                        st.session_state.passwort_aendern_fuer = login_name
                        st.rerun()
                    else:
                        st.session_state.eingeloggt_als = login_name
                        st.rerun()
                else:
                    st.error("Falsches Passwort!")
        st.stop()

user = next((m for m in st.session_state.mitglieder if m['name'] == st.session_state.eingeloggt_als), None)

# ----------------------------------------------------
# ERSTMALIGE DATENERFASSUNG (Inklusive Geburtstag)
# ----------------------------------------------------
if user['telefon'].strip() == "" and user['anschrift'].strip() == "" and user['geburtstag'].strip() == "":
    st.markdown("<h1 class='main-title'>📝 Kontaktdaten & Geburtstag vervollständigen</h1>", unsafe_allow_html=True)
    st.info(f"Hallo **{user['name']}**, trage bitte deine Daten ein. Dein Geburtstag wird danach für dein gesamtes Team im Kalender angezeigt!")
    
    with st.form("erst_erfassung_form"):
        init_tel = st.text_input("📱 Deine Telefonnummer:", placeholder="z.B. 0176 / 12345678")
        init_adr = st.text_input("🏠 Deine Anschrift:", placeholder="Straße, Hausnummer, PLZ, Ort")
        init_geb = st.date_input("📅 Dein Geburtsdatum:", value=datetime(1995, 1, 1).date(), min_value=datetime(1940, 1, 1).date(), max_value=datetime.now().date())
        
        if st.form_submit_button("Daten speichern & zur App", use_container_width=True):
            if init_tel.strip() == "" or init_adr.strip() == "":
                st.error("Bitte fülle alle Textfelder aus!")
            else:
                user['telefon'] = init_tel.strip()
                user['anschrift'] = init_adr.strip()
                user['geburtstag'] = init_geb.strftime("%Y-%m-%d")
                speichere_mitglieder(st.session_state.mitglieder)
                st.success("Erfolgreich eingetragen!")
                st.rerun()
    st.stop()

# ----------------------------------------------------
# APP OBERFLÄCHE & SIDEBAR
# ----------------------------------------------------
st.markdown("<h1 class='main-title'>⛪ FECG Bruchmühlbach — Ordner-Zentrale</h1>", unsafe_allow_html=True)

st.sidebar.header("👤 Dein Profil")
st.sidebar.success(f"**{user['name']}**")
# Geburtstag im Profil anzeigen
geb_formatiert = "Nicht eingetragen"
if user.get('geburtstag'):
    geb_formatiert = datetime.strptime(user['geburtstag'], "%Y-%m-%d").strftime("%d.%m.%Y")
st.sidebar.info(f"Rolle: {user['rolle']}\nTeam: {user['gruppe']}\nGeburtstag: {geb_formatiert}")

# SELBSTSTÄNDIGE PROFILÄNDERUNG IN SIDEBAR
with st.sidebar.expander("⚙️ Meine Profildaten ändern"):
    mein_neues_tel = st.text_input("📱 Telefonnummer:", value=user.get('telefon', ''), key="my_own_tel")
    mein_neues_adr = st.text_input("🏠 Anschrift:", value=user.get('anschrift', ''), key="my_own_adr")
    
    aktueller_geb_date = datetime.strptime(user['geburtstag'], "%Y-%m-%d").date() if user.get('geburtstag') else datetime(1995, 1, 1).date()
    mein_neuer_geb = st.date_input("📅 Geburtstag:", value=aktueller_geb_date, key="my_own_geb", min_value=datetime(1940, 1, 1).date())
    
    if st.button("💾 Profil aktualisieren", use_container_width=True, key="save_my_profile"):
        user['telefon'] = mein_neues_tel
        user['anschrift'] = mein_neues_adr
        user['geburtstag'] = mein_neuer_geb.strftime("%Y-%m-%d")
        speichere_mitglieder(st.session_state.mitglieder)
        st.sidebar.success("Daten aktualisiert!")
        st.rerun()

# ----------------------------------------------------
# FEATURE: "MEIN TEAM" UND GESAMTMITGLIEDER
# ----------------------------------------------------
st.sidebar.write("---")
show_team_section = st.sidebar.checkbox("👥 Mein Team & Mitglieder-Infos", value=False)

if show_team_section:
    st.write("## 👥 Teamverwaltung & Stammdaten")
    person_ausgewaehlt = None
    
    st.write(f"### 🛡️ Mein Team ({user['gruppe']})")
    eigenes_team = [m for m in st.session_state.mitglieder if m['gruppe'] == user['gruppe']]
    namen_eigenes_team = sorted([m['name'] for m in erstes_team_mitglied] if (erstes_team_mitglied := eigenes_team) else [])
    
    wahl_eigenes_team = st.selectbox("Mitglied aus deinem Team wählen:", options=["-- Bitte wählen --"] + namen_eigenes_team, key="sel_my_team")
    if wahl_eigenes_team != "-- Bitte wählen --":
        person_ausgewaehlt = wahl_eigenes_team

    if user['rolle'] == "Chef":
        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        st.write("### 🌍 Alle anderen Ordner-Mitglieder (Gesamtübersicht)")
        andere_mitglieder = [m for m in st.session_state.mitglieder if m['gruppe'] != user['gruppe']]
        namen_andere = sorted([m['name'] for m in andere_mitglieder])
        
        wahl_andere = st.selectbox("Anderes Gemeindemitglied wählen:", options=["-- Bitte wählen --"] + namen_andere, key="sel_all_members")
        if wahl_andere != "-- Bitte wählen --":
            person_ausgewaehlt = wahl_andere

    if person_ausgewaehlt:
        person_daten = next((m for m in st.session_state.mitglieder if m['name'] == person_ausgewaehlt), None)
        if person_daten:
            st.markdown(f"<div class='card-box'>", unsafe_allow_html=True)
            st.markdown(f"<h4>📝 Details für {person_daten['name']} ({person_daten['gruppe']})</h4>", unsafe_allow_html=True)
            
            p_telefon = st.text_input("📱 Telefonnummer:", value=person_daten.get('telefon', ''), key="edit_tel")
            p_anschrift = st.text_input("🏠 Anschrift (Straße, PLZ, Ort):", value=person_daten.get('anschrift', ''), key="edit_adr")
            
            p_geb_date = datetime.strptime(person_daten['geburtstag'], "%Y-%m-%d").date() if person_daten.get('geburtstag') else datetime(1995, 1, 1).date()
            p_geb = st.date_input("📅 Geburtstag:", value=p_geb_date, key="edit_geb", min_value=datetime(1940, 1, 1).date())
            
            p_infos = st.text_area("ℹ️ Weitere Infos / Notizen:", value=person_daten.get('infos', ''), key="edit_inf")
            
            if st.button("💾 Änderungen für diese Person speichern", use_container_width=True, key="save_person_btn"):
                person_daten['telefon'] = p_telefon
                person_daten['anschrift'] = p_anschrift
                person_daten['geburtstag'] = p_geb.strftime("%Y-%m-%d")
                person_daten['infos'] = p_infos
                speichere_mitglieder(st.session_state.mitglieder)
                st.success(f"Die Daten für {person_daten['name']} wurden erfolgreich aktualisiert!")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    st.write("---")

# Allgemeine Admin-Verwaltung in Sidebar
if user['rolle'] in ["Chef", "Teamleiter"]:
    st.sidebar.subheader("⚙️ System-Verwaltung")
    with st.sidebar.expander("➕ Neues Mitglied anlegen"):
        neu_name = st.text_input("Vollständiger Name:", placeholder="z.B. Müller Johann")
        neu_gruppe_chef = user['gruppe']
        if user['rolle'] == "Chef":
            neu_gruppe_chef = st.selectbox("Gruppe zuweisen:", options=["Gruppe 1 (Andreas K.)", "Gruppe 2 (Slawik V.)", "Gruppe 3 (Peter S.)"])
        neu_rolle = st.selectbox("Rolle:", options=["Mitarbeiter", "Teamleiter"])
        if st.button("Hinzufügen", use_container_width=True):
            if neu_name.strip() and not any(m['name'].lower() == neu_name.strip().lower() for m in st.session_state.mitglieder):
                st.session_state.mitglieder.append({
                    'name': neu_name.strip(), 'gruppe': neu_gruppe_chef, 'rolle': neu_rolle, 'passwort': 'Ordner',
                    'telefon': '', 'anschrift': '', 'infos': '', 'geburtstag': ''
                })
                speichere_mitglieder(st.session_state.mitglieder)
                st.sidebar.success(f"Erstellt!")
                st.rerun()
                
    with st.sidebar.expander("🗑️ Mitglied entfernen"):
        if user['rolle'] == "Chef":
            sichtbare_leute = sorted([m['name'] for m in st.session_state.mitglieder if m['name'] != user['name']])
        else:
            sichtbare_leute = sorted([m['name'] for m in st.session_state.mitglieder if m['gruppe'] == user['gruppe'] and m['name'] != user['name']])
        if sichtbare_leute:
            loesch_name = st.selectbox("Wer soll gelöscht werden?", options=sichtbare_leute)
            if st.button("Verbindlich Löschen", use_container_width=True):
                st.session_state.mitglieder = [m for m in st.session_state.mitglieder if m['name'] != loesch_name]
                speichere_mitglieder(st.session_state.mitglieder)
                st.sidebar.warning(f"{loesch_name} wurde entfernt.")
                st.rerun()

st.sidebar.write("---")
if st.sidebar.button("🚪 Abmelden", use_container_width=True):
    st.session_state.eingeloggt_als = None
    st.rerun()

# ----------------------------------------------------
# RESTLICHE APP (CHAT)
# ----------------------------------------------------
if user['rolle'] in ["Chef", "Teamleiter"]:
    st.write("### 💬 Interner Chat (Nur für Gruppenleiter sichtbar)")
    for msg in st.session_state.leiter_chat:
        if msg['zeit'] == 'Info': st.markdown(f"<div class='chat-system'>ℹ️ {msg['text']}</div>", unsafe_allow_html=True)
        elif msg['von'] == user['name']: st.markdown(f"<div class='chat-bubble-user'><b>Du</b> ({msg['zeit']})<br>{msg['text']}</div>", unsafe_allow_html=True)
        else: st.markdown(f"<div class='chat-bubble-other'><b>{msg['von']}</b> ({msg['zeit']})<br>{msg['text']}</div>", unsafe_allow_html=True)
            
    with st.form(key="chat_form", clear_on_submit=True):
        col_msg, col_btn = st.columns([4, 1])
        with col_msg: neue_nachricht = st.text_input("Nachricht schreiben...", placeholder="Schreiben und Enter drücken...")
        with col_btn: submit_button = st.form_submit_button("Senden", use_container_width=True)
        if submit_button and neue_nachricht.strip():
            st.session_state.leiter_chat.append({'von': user['name'], 'text': neue_nachricht, 'zeit': datetime.now().strftime("%H:%M")})
            st.rerun()
    st.write("---")

# ----------------------------------------------------
# KALENDER-GENERIERUNG INKLUSIVE GEBURTSTAGE
# ----------------------------------------------------
st.write("### 📅 Dienstplan- & Geburtstagskalender")
heute = datetime.now().date()
aktueller_sonntag = heute - timedelta(days=(heute.weekday() + 1) % 7)
if heute.weekday() == 6: aktueller_sonntag = heute
st.success(f"📢 **Aktuelle Woche:** {get_dienst_gruppe(aktueller_sonntag)} hat Dienst.")

kalender_events = []

# 1. Dienstplan-Wochen generieren
for i in range(-4, 150):
    w_sonntag = datetime(2026, 6, 21).date() + timedelta(weeks=i)
    w_samstag = w_sonntag + timedelta(days=6)
    grp = get_dienst_gruppe(w_sonntag)
    farbe = "#1e3a8a" if "Andreas K." in grp else "#8b5cf6" if "Slawik V." in grp else "#f97316"
    kalender_events.append({"title": f"🛠️ {grp}", "start": w_sonntag.isoformat(), "end": (w_samstag + timedelta(days=1)).isoformat(), "backgroundColor": farbe, "borderColor": farbe, "allDay": True})

# 2. NEU: Geburtstage des EIGENEN Teams einbetten (Sichtbar für alle Gruppenmitglieder)
for m in st.session_state.mitglieder:
    # Bedingung: Muss in der gleichen Gruppe sein. Wenn der User 'Chef' ist, sieht er alle Geburtstage.
    if user['rolle'] == "Chef" or m['gruppe'] == user['gruppe']:
        if m.get('geburtstag') and m['geburtstag'].strip() != "":
            geb_date = datetime.strptime(m['geburtstag'], "%Y-%m-%d").date()
            # Geburtstag auf das aktuelle Planungsjahr (2026) übertragen
            geb_2026 = datetime(2026, geb_date.month, geb_date.day).date()
            
            kalender_events.append({
                "title": f"🎉 Geb.: {m['name']}",
                "start": geb_2026.isoformat(),
                "end": (geb_2026 + timedelta(days=1)).isoformat(),
                "backgroundColor": "#eab308", # Gold-Gelb für gute Sichtbarkeit
                "borderColor": "#ca8a04",
                "allDay": True
            })

# 3. Urlaube & Engpässe
urlaubs_tage_zaehler = {}
for u in st.session_state.urlaube:
    u_mitglied = next((m for m in st.session_state.mitglieder if m['name'] == u['name']), None)
    if u_mitglied:
        akt_tag = u['von']
        if isinstance(akt_tag, str): akt_tag = datetime.strptime(akt_tag, "%Y-%m-%d").date()
        u_bis_date = u['bis']
        if isinstance(u_bis_date, str): u_bis_date = datetime.strptime(u_bis_date, "%Y-%m-%d").date()
        
        while akt_tag <= u_bis_date:
            if u_mitglied['gruppe'] == get_dienst_gruppe(akt_tag):
                if akt_tag not in urlaubs_tage_zaehler: urlaubs_tage_zaehler[akt_tag] = []
                if u['name'] not in urlaubs_tage_zaehler[akt_tag]: urlaubs_tage_zaehler[akt_tag].append(u['name'])
            akt_tag += timedelta(days=1)

for tag, namen_liste in urlaubs_tage_zaehler.items():
    anzahl_fehlende = len(namen_liste)
    u_farbe = "#eab308" if anzahl_fehlende == 1 else "#ef4444"
    kalender_events.append({"title": f"⚠️ Urlaub: {', '.join(namen_liste)}", "start": tag.isoformat(), "end": (tag + timedelta(days=1)).isoformat(), "backgroundColor": u_farbe, "borderColor": u_farbe, "allDay": True})

calendar(events=kalender_events, options={"initialView": "dayGridMonth", "locale": "de"}, key="fecg_calendar")
st.write("---")

# ----------------------------------------------------
# ABFRAGEN & INTERAKTIONEN
# ----------------------------------------------------
st.write("### 📋 Aktuelle Anwesenheits-Abfragen für dich")
abfragen_gefunden = False
for k_abfrage, v_abfrage in list(st.session_state.gruppen_abfragen.items()):
    is_fuer_alle = v_abfrage.get('typ', 'gruppe') == 'alle'
    is_fuer_meine_gruppe = k_abfrage.startswith(user['gruppe'])
    if is_fuer_alle or is_fuer_meine_gruppe:
        datum_str = k_abfrage.split("_")[1]
        ziel_datum = datetime.strptime(datum_str, "%Y-%m-%d").date()
        if is_fuer_alle:
            helfer_liste = v_abfrage.get('helfer', [])
            max_benoetigt = v_abfrage.get('bedarf', 1)
            if user['name'] in helfer_liste:
                abfragen_gefunden = True; st.success(f"✅ Du hast für den {ziel_datum.strftime('%
