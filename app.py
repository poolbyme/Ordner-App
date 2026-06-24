import os
import streamlit as st
import json
from datetime import datetime, timedelta
from streamlit_calendar import calendar

# 1. KONFIGURATION
st.set_page_config(page_title="FECG Bruchmühlbach - Ordner Team", page_icon="⛪", layout="wide")

# 2. URL-PARAMETER-RETTUNG (Damit man beim F5-Refresh eingeloggt bleibt)
params = st.query_params
if "user" in params and "eingeloggt_als" not in st.session_state:
    st.session_state.eingeloggt_als = params["user"]

# 3. CSS DESIGN
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    .main-title { color: #1e3a8a; font-family: 'Arial', sans-serif; font-weight: bold; text-align: center; margin-bottom: 20px; }
    .chat-bubble-user { background-color: #dcf8c6; padding: 12px; border-radius: 12px; margin-bottom: 10px; border-right: 4px solid #25d366; max-width: 85%; margin-left: auto; box-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
    .chat-bubble-other { background-color: #ffffff; padding: 12px; border-radius: 12px; margin-bottom: 10px; border-left: 4px solid #3b82f6; max-width: 85%; margin-right: auto; box-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
    .chat-system { background-color: #e5e7eb; padding: 6px; border-radius: 20px; text-align: center; font-size: 0.85em; color: #4b5563; margin-bottom: 15px; }
    .card-box { background-color: #ffffff; padding: 22px; border-radius: 12px; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05); border-top: 5px solid #1e3a8a; margin-bottom: 20px; }
    .popup-box { background-color: #ffe4e6; padding: 15px; border-left: 6px solid #f43f5e; border-radius: 8px; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# 4. DATENBANKEN
DB_FILE = "mitglieder_data.json"
CHAT_FILE = "chat_data.json"

def hole_standard_liste():
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

def lade_chat():
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return [{'von': 'System', 'text': 'Willkommen im internen Chat!', 'zeit': 'Info', 'an': 'Alle', 'gelesen_von': []}]

def speichere_chat(chat_liste):
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(chat_liste, f, ensure_ascii=False, indent=4)

if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        st.session_state.mitglieder = json.load(f)
else:
    st.session_state.mitglieder = hole_standard_liste()
    speichere_mitglieder(st.session_state.mitglieder)

st.session_state.leiter_chat = lade_chat()

# INITIALISIERUNG SESSION STATE
defaults = {"urlaube":[], "gruppen_abfragen":{}, "passwort_aendern_fuer":None, "show_abfrage_form":False, "abfrage_typ":None, "show_urlaub_form":False, "gewaehltes_mitglied":None}
for key, value in defaults.items():
    if key not in st.session_state: st.session_state[key] = value

def get_dienst_gruppe(datum):
    basis_datum = datetime(2026, 6, 21).date()
    wochen = (datum - basis_datum).days // 7
    return ["Gruppe 1 (Andreas K.)", "Gruppe 2 (Slawik V.)", "Gruppe 3 (Peter S.)"][wochen % 3]

alle_leiter = sorted([m['name'] for m in st.session_state.mitglieder if m['rolle'] in ["Chef", "Teamleiter"]])

# LOGIN CHECK
if "eingeloggt_als" not in st.session_state or st.session_state.eingeloggt_als is None:
    st.markdown("<h1 class='main-title'>⛪ FECG Bruchmühlbach — Ordner App Login</h1>", unsafe_allow_html=True)
    if st.session_state.passwort_aendern_fuer is not None:
        u_name = st.session_state.passwort_aendern_fuer
        st.warning(f"⚠️ Hallo **{u_name}**! Bitte vergebe dein Passwort.")
        neues_pw = st.text_input("Neues Passwort:", type="password")
        if st.button("Sichern & Einloggen"):
            for m in st.session_state.mitglieder:
                if m['name'] == u_name: m['passwort'] = neues_pw
            speichere_mitglieder(st.session_state.mitglieder)
            st.session_state.eingeloggt_als = u_name
            st.query_params["user"] = u_name
            st.rerun()
    else:
        with st.form("login_form"):
            login_name = st.selectbox("Dein Name:", options=sorted([m['name'] for m in st.session_state.mitglieder]))
            pw = st.text_input("Passwort:", type="password")
            submit = st.form_submit_button("Einloggen")
        
            if submit:
                user_check = next((m for m in st.session_state.mitglieder if m['name'] == login_name), None)
                if user_check and pw == user_check['passwort']:
                    if pw == "Ordner": 
                        st.session_state.passwort_aendern_fuer = login_name
                    else: 
                        st.session_state.eingeloggt_als = login_name
                        st.query_params["user"] = login_name
                    st.rerun()
                else:
                    st.error("Passwort falsch!")
    st.stop()

user = next((m for m in st.session_state.mitglieder if m['name'] == st.session_state.eingeloggt_als), None)

# ----------------------------------------------------
# SIDEBAR NAVIGATION
# ----------------------------------------------------
st.markdown("<h1 class='main-title'>⛪ FECG Bruchmühlbach — Ordner-Zentrale</h1>", unsafe_allow_html=True)

st.sidebar.header("👤 Dein Profil")
st.sidebar.success(f"**{user['name']}**")
geb_formatiert = "Nicht eingetragen"
if user.get('geburtstag'):
    geb_formatiert = datetime.strptime(user['geburtstag'], "%Y-%m-%d").strftime("%d.%m.%Y")
st.sidebar.info(f"Rolle: {user['rolle']}\nTeam: {user['gruppe']}\nGeburtstag: {geb_formatiert}")

with st.sidebar.expander("⚙️ Meine Profildaten ändern"):
    mein_neues_tel = st.text_input("📱 Telefonnummer:", value=user.get('telefon', ''), key="my_own_tel")
    mein_neues_adr = st.text_input("🏠 Anschrift:", value=user.get('anschrift', ''), key="my_own_adr")
    aktueller_geb_date = datetime.strptime(user['geburtstag'], "%Y-%m-%d").date() if user.get('geburtstag') else datetime(1995, 1, 1).date()
    mein_neuer_geb = st.date_input("📅 Geburtstag:", value=aktueller_geb_date, key="my_own_geb")
    
    if st.button("💾 Profil aktualisieren", use_container_width=True):
        user['telefon'] = mein_neues_tel
        user['anschrift'] = mein_neues_adr
        user['geburtstag'] = mein_neuer_geb.strftime("%Y-%m-%d")
        speichere_mitglieder(st.session_state.mitglieder)
        st.sidebar.success("Daten aktualisiert!")
        st.rerun()

# UNTERMENÜ: "TEAMVERWAUTUNG & STAMMDATEN"
st.sidebar.write("---")
with st.sidebar.expander("👥 Teamverwaltung & Stammdaten", expanded=True):
    eigenes_team = [m for m in st.session_state.mitglieder if m['gruppe'] == user['gruppe']]
    namen_eigenes_team = ["-- Bitte wählen --"] + sorted([m['name'] for m in eigenes_team])
    
    andere_mitglieder = [m for m in st.session_state.mitglieder if m['gruppe'] != user['gruppe']]
    namen_andere = ["-- Bitte wählen --"] + sorted([m['name'] for m in andere_mitglieder])

    if st.session_state.gewaehltes_mitglied is not None:
        if st.button("🔄 Anderes Mitglied suchen", use_container_width=True):
            st.session_state.gewaehltes_mitglied = None
            st.rerun()

    if st.session_state.gewaehltes_mitglied is None:
        st.write(f"**🛡️ Mein Team ({user['gruppe']})**")
        wahl_team = st.selectbox("Mitglied aus deinem Team wählen:", options=namen_eigenes_team, key="select_team_box")
        if wahl_team != "-- Bitte wählen --":
            st.session_state.gewaehltes_mitglied = wahl_team
            st.rerun()

        if user['rolle'] == "Chef":
            st.write("**🌍 Alle anderen Ordner-Mitglieder**")
            wahl_andere = st.selectbox("Anderes Mitglied wählen:", options=namen_andere, key="select_andere_box")
            if wahl_andere != "-- Bitte wählen --":
                st.session_state.gewaehltes_mitglied = wahl_andere
                st.rerun()

    if st.session_state.gewaehltes_mitglied:
        person_daten = next((m for m in st.session_state.mitglieder if m['name'] == st.session_state.gewaehltes_mitglied), None)
        if person_daten:
            st.markdown(f"### 📝 Daten bearbeiten:\n**{person_daten['name']}**")
            p_telefon = st.text_input("📱 Telefonnummer:", value=person_daten.get('telefon', ''), key="edit_tel")
            p_anschrift = st.text_input("🏠 Anschrift:", value=person_daten.get('anschrift', ''), key="edit_adr")
            p_geb_date = datetime.strptime(person_daten['geburtstag'], "%Y-%m-%d").date() if person_daten.get('geburtstag') else datetime(1995, 1, 1).date()
            p_geb = st.date_input("📅 Geburtstag:", value=p_geb_date, key="edit_geb")
            p_infos = st.text_area("ℹ️ Notizen:", value=person_daten.get('infos', ''), key="edit_inf")
            
            if st.button("💾 Änderungen speichern", use_container_width=True):
                person_daten['telefon'] = p_telefon
                person_daten['anschrift'] = p_anschrift
                person_daten['geburtstag'] = p_geb.strftime("%Y-%m-%d")
                person_daten['infos'] = p_infos
                speichere_mitglieder(st.session_state.mitglieder)
                st.success("Änderungen erfolgreich gespeichert!")
                st.rerun()

# UNTERMENÜ: "INTERNER CHAT"
if user['rolle'] in ["Chef", "Teamleiter"]:
    with st.sidebar.expander("💬 Interner Leiter-Chat"):
        for msg in st.session_state.leiter_chat:
            if msg['zeit'] == 'Info': 
                st.markdown(f"<div class='chat-system'>ℹ️ {msg['text']}</div>", unsafe_allow_html=True)
            else:
                ziel_info = f" ➔ 🔒 <i>{msg['an']}</i>" if msg['an'] != "Alle" else ""
                if msg['von'] == user['name']: 
                    st.markdown(f"<div class='chat-bubble-user'><b>Du</b>{ziel_info} ({msg['zeit']})<br>{msg['text']}</div>", unsafe_allow_html=True)
                else: 
                    st.markdown(f"<div class='chat-bubble-other'><b>{msg['von']}</b>{ziel_info} ({msg['zeit']})<br>{msg['text']}</div>", unsafe_allow_html=True)
                
        with st.form(key="chat_form_sidebar", clear_on_submit=True):
            neue_nachricht = st.text_input("Nachricht...", placeholder="Schreiben...")
            chat_partner_optionen = ["Alle"] + [leiter for leiter in alle_leiter if leiter != user['name']]
            empfaenger = st.selectbox("An wen (optional):", options=chat_partner_optionen)
            
            if st.form_submit_button("Senden", use_container_width=True) and neue_nachricht.strip():
                st.session_state.leiter_chat.append({
                    'von': user['name'], 
                    'text': neue_nachricht, 
                    'zeit': datetime.now().strftime("%H:%M"),
                    'an': empfaenger,
                    'gelesen_von': []
                })
                speichere_chat(st.session_state.leiter_chat)
                st.rerun()

# System-Verwaltung
if user['rolle'] in ["Chef", "Teamleiter"]:
    st.sidebar.subheader("⚙️ System-Verwaltung")
    with st.sidebar.expander("➕ Neues Mitglied anlegen"):
        with st.form("sidebar_add_member_form", clear_on_submit=True):
            neu_name = st.text_input("Vollständiger Name:", placeholder="z.B. Müller Johann")
            neu_gruppe_chef = user['gruppe']
            if user['rolle'] == "Chef":
                neu_gruppe_chef = st.selectbox("Gruppe zuweisen:", options=["Gruppe 1 (Andreas K.)", "Gruppe 2 (Slawik V.)", "Gruppe 3 (Peter S.)"])
            neu_rolle = st.selectbox("Rolle:", options=["Mitarbeiter", "Teamleiter"])
            
            if st.form_submit_button("Hinzufügen", use_container_width=True):
                if neu_name.strip() and not any(m['name'].lower() == neu_name.strip().lower() for m in st.session_state.mitglieder):
                    st.session_state.mitglieder.append({
                        'name': neu_name.strip(), 'gruppe': neu_gruppe_chef, 'rolle': neu_rolle, 'passwort': 'Ordner',
                        'telefon': '', 'anschrift': '', 'infos': '', 'geburtstag': ''
                    })
                    speichere_mitglieder(st.session_state.mitglieder)
                    st.success(f"🎉 **{neu_name}** wurde registriert.")
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
                
if st.sidebar.button("🚪 Abmelden"):
    st.query_params.clear()
    st.session_state.eingeloggt_als = None
    st.rerun()

# ====================================================
# HAUPTSEITE (Mit automatischem Pop-up System)
# ====================================================

if user['rolle'] in ["Chef", "Teamleiter"]:
    ungelesene_nachrichten = []
    
    for idx, msg in enumerate(st.session_state.leiter_chat):
        if msg['zeit'] == 'Info' or msg['von'] == user['name']:
            continue
        
        an_ziel = str(msg.get('an', '')).strip().lower()
        aktueller_user = str(user['name']).strip().lower()
        
        if (an_ziel == aktueller_user or an_ziel == "alle") and user['name'] not in msg.get('gelesen_von', []):
            ungelesene_nachrichten.append((idx, msg))
            
# --- KORREKTER SCHLEIFEN-BLOCK ---
if 'ungelesene_nachrichten' in locals() and ungelesene_nachrichten:
    for eintrag in ungelesene_nachrichten:
        # Hier holen wir das Dictionary aus dem Tupel (eintrag[1] ist das Dictionary)
        nachricht = eintrag[1] if isinstance(eintrag, tuple) else eintrag
        
        if isinstance(nachricht, dict):
            st.markdown("<div class='popup-box'>", unsafe_allow_html=True)
            st.warning("🔔 WICHTIGE NACHRICHT IM LEITER-CHAT AN DICH!")
            
            sender = nachricht.get('von', 'Unbekannt')
            zeit = nachricht.get('zeit', 'Keine Zeit')
            text = nachricht.get('text', 'Kein Inhalt')
            
            st.write(f"**Von {sender} ({zeit}):** {text}")

            # Buttons für Aktion
            col1, col2 = st.columns(2)
            with col1:
                # Eindeutiger Key durch Index + Zeit
                if st.button("👁️ Als gelesen markieren", key=f"read_{zeit}_{sender}"):
                    if 'gelesen_von' not in nachricht: nachricht['gelesen_von'] = []
                    nachricht['gelesen_von'].append(user['name'])
                    speichere_chat(st.session_state.leiter_chat)
                    st.rerun()
            with col2:
                if st.button("💬 Antworten", key=f"reply_{zeit}_{sender}"):
                    st.session_state.seite = "Chat"
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Falls es doch ein String ist, zeigen wir ihn einfach so an
            st.warning(f"🔔 Nachricht: {nachricht}")

# 1. DIENSTPLAN- & GEBURTSTAGSKALENDER
st.write("### 📅 Dienstplan- & Geburtstagskalender")
heute = datetime.now().date()
aktueller_sonntag = heute - timedelta(days=(heute.weekday() + 1) % 7)
if heute.weekday() == 6: 
    aktueller_sonntag = heute
st.success(f"📢 **Aktuelle Woche:** {get_dienst_gruppe(aktueller_sonntag)} hat Dienst.")

kalender_events = []

for i in range(-4, 150):
    w_sonntag = datetime(2026, 6, 21).date() + timedelta(weeks=i)
    w_samstag = w_sonntag + timedelta(days=6)
    grp = get_dienst_gruppe(w_sonntag)
    
    farbe = "#1e3a8a" if "Gruppe 1" in grp else "#8b5cf6" if "Gruppe 2" in grp else "#f97316"
    kalender_events.append({
        "title": f"🛠️ {grp}", 
        "start": w_sonntag.isoformat(), 
        "end": (w_samstag + timedelta(days=1)).isoformat(), 
        "backgroundColor": farbe, 
        "borderColor": farbe, 
        "allDay": True
    })

# Geburtstage einbetten
aktuelles_jahr = datetime.now().year
for m in st.session_state.mitglieder:
    if user['rolle'] == "Chef" or m['gruppe'] == user['gruppe']:
        if m.get('geburtstag') and m['geburtstag'].strip() != "":
            try:
                geb_date = datetime.strptime(m['geburtstag'], "%Y-%m-%d").date()
            except ValueError:
                continue
            
            for jahr in range(aktuelles_jahr, aktuelles_jahr + 2):
                try:
                    geb_aktuell = datetime(jahr, geb_date.month, geb_date.day).date()
                    kalender_events.append({
                        "title": f"🎉 Geb.: {m['name']}",
                        "start": geb_aktuell.isoformat(),
                        "end": (geb_aktuell + timedelta(days=1)).isoformat(),
                        "backgroundColor": "#eab308", 
                        "borderColor": "#ca8a04",
                        "allDay": True
                    })
                except ValueError:
                    geb_aktuell = datetime(jahr, 2, 28).date()
                    kalender_events.append({
                        "title": f"🎉 Geb.: {m['name']}",
                        "start": geb_aktuell.isoformat(),
                        "end": (geb_aktuell + timedelta(days=1)).isoformat(),
                        "backgroundColor": "#eab308", 
                        "borderColor": "#ca8a04",
                        "allDay": True
                    })

# Urlaube verarbeiten
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
    kalender_events.append({
        "title": f"⚠️ Urlaub: {', '.join(namen_liste)}", 
        "start": tag.isoformat(), 
        "end": (tag + timedelta(days=1)).isoformat(), 
        "backgroundColor": u_farbe, 
        "borderColor": u_farbe, 
        "allDay": True
    })

# Kalender rendern
calendar_key = f"fecg_calendar_{len(kalender_events)}"
calendar(events=kalender_events, options={"initialView": "dayGridMonth", "locale": "de"}, key=calendar_key)
st.write("---")

# 2. ANWESENHEITS-ABFRAGEN
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
                abfragen_gefunden = True; st.success(f"✅ Du hast für den {ziel_datum.strftime('%d.%m.%Y')} verbindlich zugesagt!"); continue
            if len(helfer_liste) >= max_benoetigt: continue
            abfragen_gefunden = True
            st.error(f"🚨 **HILFERUF AN ALLE:** Für den {ziel_datum.strftime('%d.%m.%Y')} werden noch Helfer gesucht!")
            if st.button(f"🤝 Als {user['name']} einspringen", key=f"gesamt_zusage_{k_abfrage}", use_container_width=True):
                v_abfrage['helfer'].append(user['name'])
                v_abfrage['rueckmeldungen'][user['name']] = "🟢 Eingesprungen"; st.rerun()
        elif is_fuer_meine_gruppe:
            if user['name'] in v_abfrage['rueckmeldungen']: continue
            abfragen_gefunden = True
            st.info(f"➔ [Deine Gruppe] **Offene Abfrage:** {ziel_datum.strftime('%d.%m.%Y')}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🟢 Ich bin DA", key=f"da_{k_abfrage}"): v_abfrage['rueckmeldungen'][user['name']] = "🟢 Bin da"; st.rerun()
            with c2:
                if st.button("🔴 Ich bin NICHT da", key=f"weg_{k_abfrage}"): v_abfrage['rueckmeldungen'][user['name']] = "🔴 Nicht da"; st.rerun()
if not abfragen_gefunden: 
    st.write("✅ Keine offenen Abfragen ausstehend.")
st.write("---")

# Interaktive Formularboxen
col_box1, col_box2 = st.columns(2)
with col_box1:
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.subheader("🚀 Neue Abfrage starten")
    if user['rolle'] in ["Chef", "Teamleiter"]:
        if not st.session_state.show_abfrage_form:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("👥 Eigene Gruppenabfrage", use_container_width=True): st.session_state.show_abfrage_form = True; st.session_state.abfrage_typ = "gruppe"; st.rerun()
            with c2:
                if st.button("🌍 Gesamtabfrage (ALLE)", use_container_width=True): st.session_state.show_abfrage_form = True; st.session_state.abfrage_typ = "alle"; st.rerun()
        else:
            gewaehltes_datum = st.date_input("Für welchen Tag:", value=aktueller_sonntag)
            bedarf_personen = st.number_input("Benötigte Personen:", min_value=1, value=2) if st.session_state.abfrage_typ == "alle" else 0
            if st.button("✅ Starten", use_container_width=True):
                key = f"{user['gruppe'] if st.session_state.abfrage_typ=='gruppe' else 'ALLE'}_{gewaehltes_datum.strftime('%Y-%m-%d')}"
                st.session_state.gruppen_abfragen[key] = {'status': 'offen', 'typ': st.session_state.abfrage_typ, 'bedarf': bedarf_personen, 'helfer': [], 'rueckmeldungen': {}}
                st.session_state.show_abfrage_form = False; st.rerun()
    else:
        st.write("Nur für Gruppenleiter verfügbar.")
    st.markdown("</div>", unsafe_allow_html=True)

with col_box2:
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.subheader("🌴 Urlaubsverwaltung")
    if not st.session_state.show_urlaub_form:
        if st.button("📅 Urlaub eintragen", use_container_width=True): st.session_state.show_urlaub_form = True; st.rerun()
    else:
        u_von = st.date_input("Urlaub von:", value=heute)
        u_bis = st.date_input("Urlaub bis:", value=heute + timedelta(days=7))
        if st.button("✅ Speichern", use_container_width=True):
            st.session_state.urlaube.append({'name': user['name'], 'von': u_von, 'bis': u_bis})
            st.session_state.show_urlaub_form = False; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
