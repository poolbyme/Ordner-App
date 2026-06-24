import streamlit as st
from datetime import datetime, timedelta
from streamlit_calendar import calendar
import os
import json

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
# MITGLIEDER DAUERHAFT SPEICHERN (DATEI-DATENBANK)
# ----------------------------------------------------
DB_FILE = "mitglieder_data.json"

def lade_mitglieder():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # Standard-Liste beim ersten allerersten Start
        return [
            {'name': 'Komjagin Andreas', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Chef', 'passwort': 'Ordner'},
            {'name': 'Hauf Valintin', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
            {'name': 'Geier Enriko', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
            {'name': 'Ilchuk Vasyl', 'gruppe': 'Gruppe 1 (Andreas K.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
            {'name': 'Volkov Slawik', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Teamleiter', 'passwort': 'Ordner'},
            {'name': 'Tissen Eduard', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
            {'name': 'Eberhart Wili', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
            {'name': 'Paul Steffen', 'gruppe': 'Gruppe 2 (Slawik V.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
            {'name': 'Schäfer Peter', 'gruppe': 'Gruppe 3 (Peter S.)', 'rolle': 'Teamleiter', 'passwort': 'Ordner'},
            {'name': 'Akulenko Wili', 'gruppe': 'Gruppe 3 (Peter S.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'},
            {'name': 'Hermann Bogdan', 'gruppe': 'Gruppe 3 (Peter S.)', 'rolle': 'Mitarbeiter', 'passwort': 'Ordner'}
        ]

def speichere_mitglieder(liste):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=4)

# In den Session State laden
if "mitglieder" not in st.session_state:
    st.session_state.mitglieder = lade_mitglieder()

# Weitere Speicher initialisieren
if "urlaube" not in st.session_state:
    st.session_state.urlaube = []
if "gruppen_abfragen" not in st.session_state:
    st.session_state.gruppen_abfragen = {}
if "ersatz_suchen" not in st.session_state:
    st.session_state.ersatz_suchen = []
if "leiter_chat" not in st.session_state:
    st.session_state.leiter_chat = [{'von': 'System', 'text': 'Willkommen im internen Chat der Gruppenleiter!', 'zeit': 'Info'}]
if "eingeloggt_als" not in st.session_state:
    st.session_state.eingeloggt_als = None
if "passwort_aendern_fuer" not in st.session_state:
    st.session_state.passwort_aendern_fuer = None
if "show_abfrage_form" not in st.session_state:
    st.session_state.show_abfrage_form = False
if "abfrage_typ" not in st.session_state:
    st.session_state.abfrage_typ = None
if "show_urlaub_form" not in st.session_state:
    st.session_state.show_urlaub_form = False

def get_dienst_gruppe(datum):
    basis_datum = datetime(2026, 6, 21).date()
    wochen = (datum - basis_datum).days // 7
    return ["Gruppe 1 (Andreas K.)", "Gruppe 2 (Slawik V.)", "Gruppe 3 (Peter S.)"][wochen % 3]

def sende_whatsapp_benachrichtigung(nachrichtstext):
    pass

# ----------------------------------------------------
# LOGIN- & ERST-REGISTRIER-SYSTEM (MIT PASSWORT-ZWANG)
# ----------------------------------------------------
if st.session_state.eingeloggt_als is None:
    st.markdown("<h1 class='main-title'>⛪ FECG Bruchmühlbach — Ordner App Login</h1>", unsafe_allow_html=True)
    
    if st.session_state.passwort_aendern_fuer is not None:
        u_name = st.session_state.passwort_aendern_fuer
        st.warning(f"⚠️ Hallo **{u_name}**! Du bist neu oder nutzt das Standard-Passwort.")
        st.write("Bitte vergebe jetzt dein eigenes, persönliches Passwort, um vollen Zugriff zu erhalten.")
        
        neues_pw = st.text_input("Dein neues persönliches Passwort:", type="password", key="new_pw_input")
        neues_pw_wdhl = st.text_input("Passwort wiederholen:", type="password", key="new_pw_confirm")
        
        if st.button("Sichern & Einloggen", use_container_width=True):
            if neues_pw == "Ordner" or neues_pw.strip() == "":
                st.error("Das neue Passwort darf nicht 'Ordner' heißen oder leer sein!")
            elif neues_pw != neues_pw_wdhl:
                st.error("Die Passwörter stimmen nicht überein!")
            else:
                # In der Liste aktualisieren und permanent speichern
                for m in st.session_state.mitglieder:
                    if m['name'] == u_name:
                        m['passwort'] = neues_pw
                speichere_mitglieder(st.session_state.mitglieder)
                
                st.session_state.eingeloggt_als = u_name
                st.session_state.passwort_aendern_fuer = None
                st.success("Dein Passwort wurde sicher gespeichert!")
                st.rerun()
        st.stop()

    else:
        col_login, _ = st.columns([1, 1])
        with col_login:
            st.write("Wähle deinen Namen aus und gib dein Passwort ein.")
            alle_namen = sorted([m['name'] for m in st.session_state.mitglieder])
            login_name = st.selectbox("Dein Name:", options=alle_namen)
            passwort_eingabe = st.text_input("Dein Passwort (bei neuen Profilen 'Ordner'):", type="password")
            
            if st.button("Einloggen", use_container_width=True):
                user_check = next((m for m in st.session_state.mitglieder if m['name'] == login_name), None)
                if user_check and passwort_eingabe == user_check['passwort']:
                    if passwort_eingabe == "Ordner":
                        st.session_state.passwort_aendern_fuer = login_name
                        st.rerun()
                    else:
                        st.session_state.eingeloggt_als = login_name
                        st.success("Erfolgreich eingeloggt!")
                        st.rerun()
                else:
                    st.error("Falsches Passwort für diesen Namen!")
        st.stop()

user = next((m for m in st.session_state.mitglieder if m['name'] == st.session_state.eingeloggt_als), None)

# ----------------------------------------------------
# APP OBERFLÄCHE & SIDEBAR
# ----------------------------------------------------
st.markdown("<h1 class='main-title'>⛪ FECG Bruchmühlbach — Ordner-Zentrale</h1>", unsafe_allow_html=True)

st.sidebar.header("👤 Dein Profil")
st.sidebar.success(f"Eingeloggt: **{user['name']}**")
st.sidebar.info(f"Rolle: {user['rolle']}\nTeam: {user['gruppe']}")

# MITGLIEDER-VERWALTUNG (SPEICHERT JETZT DAUERHAFT)
if user['rolle'] in ["Chef", "Teamleiter"]:
    st.sidebar.write("---")
    st.sidebar.subheader("👥 Mitglieder verwalten")
    
    with st.sidebar.expander("➕ Neues Mitglied anlegen"):
        neu_name = st.text_input("Vollständiger Name:", placeholder="z.B. Müller Johann")
        neu_rolle = st.selectbox("Rolle:", options=["Mitarbeiter", "Teamleiter"])
        if st.button("Hinzufügen", use_container_width=True):
            if neu_name.strip() == "":
                st.sidebar.error("Name darf nicht leer sein!")
            elif any(m['name'].lower() == neu_name.strip().lower() for m in st.session_state.mitglieder):
                st.sidebar.error("Name existiert bereits!")
            else:
                st.session_state.mitglieder.append({
                    'name': neu_name.strip(),
                    'gruppe': user['gruppe'],
                    'rolle': neu_rolle,
                    'passwort': 'Ordner'
                })
                speichere_mitglieder(st.session_state.mitglieder)
                st.sidebar.success(f"Erstellt! Sag ihm, sein Passwort ist: Ordner")
                st.rerun()
                
    with st.sidebar.expander("🗑️ Mitglied entfernen"):
        eigene_leute = [m['name'] for m in st.session_state.mitglieder if m['gruppe'] == user['gruppe'] and m['name'] != user['name']]
        if eigene_leute:
            loesch_name = st.selectbox("Wer soll gelöscht werden?", options=eigene_leute)
            if st.button("Verbindlich Löschen", use_container_width=True):
                st.session_state.mitglieder = [m for m in st.session_state.mitglieder if m['name'] != loesch_name]
                speichere_mitglieder(st.session_state.mitglieder)
                st.sidebar.warning(f"{loesch_name} wurde entfernt.")
                st.rerun()
        else:
            st.sidebar.text("Keine Mitglieder zum Löschen.")

st.sidebar.write("---")
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
            st.session_state.leiter_chat.append({'von': user['name'], 'text': neue_nachricht, 'zeit': jetzt_zeit})
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
st.success(f"📢 **Aktuelle Woche:** {dienst_gruppe} hat Dienst.")

kalender_events = []
start_basis = datetime(2026, 6, 21).date()
for i in range(-4, 150):
    w_sonntag = start_basis + timedelta(weeks=i)
    w_samstag = w_sonntag + timedelta(days=6)
    grp = get_dienst_gruppe(w_sonntag)
    farbe = "#1e3a8a" if "Andreas K." in grp else "#8b5cf6" if "Slawik V." in grp else "#f97316"
        
    kalender_events.append({
        "title": f"🛠️ {grp}",
        "start": w_sonntag.isoformat(),
        "end": (w_samstag + timedelta(days=1)).isoformat(),
        "backgroundColor": farbe,
        "borderColor": farbe,
        "allDay": True
    })

urlaubs_tage_zaehler = {}
for u in st.session_state.urlaube:
    u_mitglied = next((m for m in st.session_state.mitglieder if m['name'] == u['name']), None)
    if u_mitglied:
        akt_tag = u['von']
        while akt_tag <= u['bis']:
            if u_mitglied['gruppe'] == get_dienst_gruppe(akt_tag):
                if akt_tag not in urlaubs_tage_zaehler: urlaubs_tage_zaehler[akt_tag] = []
                if u['name'] not in urlaubs_tage_zaehler[akt_tag]: urlaubs_tage_zaehler[akt_tag].append(u['name'])
            akt_tag += timedelta(days=1)

for tag, namen_liste in urlaubs_tage_zaehler.items():
    anzahl_fehlende = len(namen_liste)
    namen_text = ", ".join(namen_liste)
    u_farbe = "#eab308" if anzahl_fehlende == 1 else "#ef4444"
    u_titel = f"⚠️ Urlaub (1/4 fehlt): {namen_text}" if anzahl_fehlende == 1 else f"🚨 ENG ({anzahl_fehlende}/4 fehlt): {namen_text}"
    kalender_events.append({"title": u_titel, "start": tag.isoformat(), "end": (tag + timedelta(days=1)).isoformat(), "backgroundColor": u_farbe, "borderColor": u_farbe, "allDay": True})

calendar(events=kalender_events, options={"initialView": "dayGridMonth", "locale": "de"}, key="fecg_calendar")
st.write("---")

# ----------------------------------------------------
# 2. ANWESENHEITS-RÜCKMELDE-SYSTEM
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
                abfragen_gefunden = True
                st.success(f"✅ Du hast für den {ziel_datum.strftime('%d.%m.%Y')} verbindlich zugesagt!")
                continue
            if len(helfer_liste) >= max_benoetigt:
                continue
                
            abfragen_gefunden = True
            st.error(f"🚨 **HILFERUF AN ALLE:** Für den {ziel_datum.strftime('%d.%m.%Y')} werden noch **{max_benoetigt - len(helfer_liste)} von {max_benoetigt}** Ordnern gesucht!")
            if st.button(f"🤝 Als {user['name']} verbindlich einspringen", key=f"gesamt_zusage_{k_abfrage}", use_container_width=True):
                v_abfrage['helfer'].append(user['name'])
                v_abfrage['rueckmeldungen'][user['name']] = "🟢 Eingesprungen"
                st.success("Erfolgreich eingetragen!")
                st.rerun()
                
        elif is_fuer_meine_gruppe:
            if user['name'] in v_abfrage['rueckmeldungen']: continue
            abfragen_gefunden = True
            st.info(f"➔ [Deine Gruppe] **Offene Abfrage:** Wer ist am {ziel_datum.strftime('%d.%m.%Y')} einsatzbereit?")
            col_da, col_weg = st.columns(2)
            with col_da:
                if st.button("🟢 Ich bin DA", key=f"da_{k_abfrage}"):
                    v_abfrage['rueckmeldungen'][user['name']] = "🟢 Bin da"
                    st.rerun()
            with col_weg:
                if st.button("🔴 Ich bin NICHT da", key=f"weg_{k_abfrage}"):
                    v_abfrage['rueckmeldungen'][user['name']] = "🔴 Nicht da"
                    st.rerun()

if not abfragen_gefunden:
    st.write("✅ Keine offenen Abfragen ausstehend.")
st.write("---")

# ----------------------------------------------------
# 3. INTERAKTIONEN (ABFRAGE & URLAUB)
# ----------------------------------------------------
col_box1, col_box2 = st.columns(2)

with col_box1:
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.subheader("🚀 Anwesenheits-Abfrage")
    if user['rolle'] in ["Chef", "Teamleiter"]:
        if not st.session_state.show_abfrage_form:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("👥 Eigene Gruppenabfrage", use_container_width=True):
                    st.session_state.show_abfrage_form = True
                    st.session_state.abfrage_typ = "gruppe"
                    st.rerun()
            with c2:
                if st.button("🌍 Gesamtabfrage (ALLE)", use_container_width=True):
                    st.session_state.show_abfrage_form = True
                    st.session_state.abfrage_typ = "alle"
                    st.rerun()
        else:
            if st.session_state.abfrage_typ == "alle":
                col_dat, col_anz = st.columns([2, 1])
                with col_dat: gewaehltes_datum = st.date_input("Für welchen Tag:", value=aktueller_sonntag, key="abfrage_picker_all")
                with col_anz: bedarf_personen = st.number_input("Benötigte Personen:", min_value=1, max_value=10, value=2, step=1)
            else:
                gewaehltes_datum = st.date_input("Für welchen Tag:", value=aktueller_sonntag, key="abfrage_picker_grp")
                bedarf_personen = 0
                
            c_send, c_cancel = st.columns(2)
            with c_send:
                if st.button("✅ Starten", use_container_width=True):
                    key = f"{user['gruppe'] if st.session_state.abfrage_typ=='gruppe' else 'ALLE'}_{gewaehltes_datum.strftime('%Y-%m-%d')}"
                    st.session_state.gruppen_abfragen[key] = {'status': 'offen', 'typ': st.session_state.abfrage_typ, 'bedarf': bedarf_personen, 'helfer': [], 'rueckmeldungen': {}}
                    st.session_state.show_abfrage_form = False
                    st.rerun()
            with c_cancel:
                if st.button("❌ Abbrechen", use_container_width=True):
                    st.session_state.show_abfrage_form = False
                    st.rerun()
                    
        st.write("#### 📊 Status deiner Abfragen:")
        for k, v in st.session_state.gruppen_abfragen.items():
            if k.startswith(user['gruppe']) or v.get('typ') == 'alle':
                d_str = datetime.strptime(k.split("_")[1], "%Y-%m-%d").strftime("%d.%m.%Y")
                if v.get('typ') == 'alle':
                    st.write(f"**Tag: {d_str} (Gesamtabfrage):** {len(v['helfer'])} von {v['bedarf']} Plätzen")
                else:
                    st.write(f"**Tag: {d_str} (Eigene Gruppe):**")
                    for m in [x for x in st.session_state.mitglieder if x['gruppe'] == user['gruppe']]:
                        st.text(f" • {m['name']}: {v['rueckmeldungen'].get(m['name'], '⏳ Warten')}")
    st.markdown("</div>", unsafe_allow_html=True)

with col_box2:
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.subheader("🌴 Urlaubsverwaltung")
    if not st.session_state.show_urlaub_form:
        if st.button("📅 Urlaub eintragen", use_container_width=True):
            st.session_state.show_urlaub_form = True
            st.rerun()
    else:
        u_von = st.date_input("Urlaub von:", value=heute, key="u_von")
        u_bis = st.date_input("Urlaub bis:", value=heute + timedelta(days=7), key="u_bis")
        cs, cc = st.columns(2)
        with cs:
            if st.button("✅ Speichern", use_container_width=True):
                st.session_state.urlaube.append({'name': user['name'], 'von': u_von, 'bis': u_bis})
                st.session_state.show_urlaub_form = False
                st.rerun()
        with cc:
            if st.button("❌ Abbrechen", use_container_width=True):
                st.session_state.show_urlaub_form = False
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
