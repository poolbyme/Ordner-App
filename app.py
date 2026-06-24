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
    try:
        pass
    except Exception as e:
        print(f"WhatsApp-Fehler: {e}")

# 1. LIVE-SPEICHER INITIALISIEREN
if "mitglieder" not in st.session_state:
    st.session_state.mitglieder = [
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

if "passwort_aendern_fuer" not in st.session_state:
    st.session_state.passwort_aendern_fuer = None

# ZUSTÄNDE FÜR DIE POP-UPS
if "show_abfrage_form" not in st.session_state:
    st.session_state.show_abfrage_form = False

if "abfrage_typ" not in st.session_state:
    st.session_state.abfrage_typ = None  # "gruppe" oder "alle"

if "show_urlaub_form" not in st.session_state:
    st.session_state.show_urlaub_form = False

def get_dienst_gruppe(datum):
    basis_datum = datetime(2026, 6, 21).date()
    wochen = (datum - basis_datum).days // 7
    return ["Gruppe 1 (Andreas K.)", "Gruppe 2 (Slawik V.)", "Gruppe 3 (Peter S.)"][wochen % 3]


# ----------------------------------------------------
# LOGIN- & REGISTRIER-SYSTEM
# ----------------------------------------------------
if st.session_state.eingeloggt_als is None:
    st.markdown("<h1 class='main-title'>⛪ FECG Bruchmühlbach — Ordner App Login</h1>", unsafe_allow_html=True)
    
    if st.session_state.passwort_aendern_fuer is not None:
        u_name = st.session_state.passwort_aendern_fuer
        st.warning(f"⚠️ Hallo *{u_name}*! Du nutzt aktuell noch das Standard-Passwort 'Ordner'.")
        st.write("Aus Sicherheitsgründen musst du jetzt ein eigenes, persönliches Passwort vergeben.")
        
        neues_pw = st.text_input("Dein neues persönliches Passwort:", type="password", key="new_pw_input")
        neues_pw_wdhl = st.text_input("Passwort wiederholen:", type="password", key="new_pw_confirm")
        
        if st.button("Sichern & Einloggen", use_container_width=True):
            if neues_pw == "Ordner" or neues_pw.strip() == "":
                st.error("Das neue Passwort darf nicht leer sein oder wieder 'Ordner' heißen!")
            elif neues_pw != neues_pw_wdhl:
                st.error("Die Passwörter stimmen nicht überein!")
            else:
                for m in st.session_state.mitglieder:
                    if m['name'] == u_name:
                        m['passwort'] = neues_pw
                st.session_state.eingeloggt_als = u_name
                st.session_state.passwort_aendern_fuer = None
                st.success("Dein persönliches Passwort wurde erfolgreich gespeichert!")
                st.rerun()
        st.stop()

    else:
        col_login, _ = st.columns([1, 1])
        with col_login:
            st.write("Bitte wähle deinen Namen aus und gib dein Passwort ein.")
            alle_namen = [m['name'] for m in st.session_state.mitglieder]
            login_name = st.selectbox("Dein Name:", options=alle_namen)
            passwort_eingabe = st.text_input("Dein Passwort (beim 1. Mal 'Ordner'):", type="password")
            
            if st.button("Einloggen", use_container_width=True):
                user_check = next((m for m in st.session_state.mitglieder if m['name'] == login_name), None)
                if user_check and passwort_eingabe == user_check['passwort']:
                    if passwort_eingabe == "Ordner":
                        st.session_state.passwort_aendern_fuer = login_name
                        st.rerun()
                    else:
                        st.session_state.eingeloggt_als = login_name
                        st.success(f"Erfolgreich eingeloggt!")
                        st.rerun()
                else:
                    st.error("Falsches Passwort für diesen Namen!")
        st.stop()

user = next((m for m in st.session_state.mitglieder if m['name'] == st.session_state.eingeloggt_als), None)


# ----------------------------------------------------
# APP OBERFLÄCHE (NACH ERFOLGREICHEM LOGIN)
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

# INTELLIGENTE URLAUBS-LOGIK MIT GRUPPEN-ÜBERSCHNEIDUNGS-FILTER
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
# 2. ANWESENHEITS-RÜCKMELDE-SYSTEM (INTELLIGENT FÜR GRUPPE & GESAMT)
# ----------------------------------------------------
st.write("### 📋 Aktuelle Anwesenheits-Abfragen für dich")
abfragen_gefunden = False

for k_abfrage, v_abfrage in list(st.session_state.gruppen_abfragen.items()):
    is_fuer_alle = v_abfrage.get('typ', 'gruppe') == 'alle'
    is_fuer_meine_gruppe = k_abfrage.startswith(user['gruppe'])
    
    if is_fuer_alle or is_fuer_meine_gruppe:
        datum_str = k_abfrage.split("_")[1]
        ziel_datum = datetime.strptime(datum_str, "%Y-%m-%d").date()
        
        # SONDERLOGIK FÜR GESAMTABFRAGE (Max. Anzahl Personen & kein Nein-Button)
        if is_fuer_alle:
            helfer_liste = v_abfrage.get('helfer', [])
            max_benoetigt = v_abfrage.get('bedarf', 1)
            
            # Wenn der aktuelle Benutzer bereits zugesagt hat
            if user['name'] in helfer_liste:
                abfragen_gefunden = True
                st.success(f"✅ Du hast für *Sonntag, den {ziel_datum.strftime('%d.%m.%Y')}* verbindlich zugesagt einzuspringen!")
                continue
                
            # Wenn das Limit der Gesamtabfrage bereits voll ist
            if len(helfer_liste) >= max_benoetigt:
                continue # Abfrage wird für andere unsichtbar, da voll besetzt
                
            abfragen_gefunden = True
            st.error(f"🚨 *DRINGENDER HILFERUF AN ALLE GRUPPEN:* Für Sonntag, den {ziel_datum.strftime('%d.%m.%Y')} werden dringend noch *{max_benoetigt - len(helfer_liste)} von {max_benoetigt}* Ordner(n) gesucht!")
            
            if st.button(f"🤝 Als {user['name']} verbindlich einspringen", key=f"gesamt_zusage_{k_abfrage}", use_container_width=True):
                v_abfrage['helfer'].append(user['name'])
                v_abfrage['rueckmeldungen'][user['name']] = "🟢 Eingesprungen"
                st.success("Vielen Dank! Deine Zusage ist verbindlich registriert.")
                st.rerun()
                
        # NORMALE LOGIK FÜR DIE EIGENE GRUPPE (Mit Auswahl Ja/Nein)
        elif is_fuer_meine_gruppe:
            if user['name'] in v_abfrage['rueckmeldungen']:
                continue  # Hat schon abgestimmt
            
            abfragen_gefunden = True
            st.info(f"➔ [Deine Gruppe] *Offene Abfrage:* Wer ist am Sonntag, den {ziel_datum.strftime('%d.%m.%Y')} einsatzbereit?")
            
            col_da, col_weg = st.columns(2)
            with col_da:
                if st.button("🟢 Ich bin verbindlich DA", key=f"da_{k_abfrage}"):
                    v_abfrage['rueckmeldungen'][user['name']] = "🟢 Bin da"
                    st.success("Erfolgreich eingetragen!")
                    st.rerun()
            with col_weg:
                if st.button("🔴 Ich bin NICHT da", key=f"weg_{k_abfrage}"):
                    v_abfrage['rueckmeldungen'][user['name']] = "🔴 Nicht da"
                    st.warning("Abwesenheit eingetragen.")
                    st.rerun()

if not abfragen_gefunden:
    st.write("✅ Keine offenen Abfragen ausstehend oder du hast bereits verbindlich abgestimmt!")
st.write("---")

# ----------------------------------------------------
# 3. POP-UP SCHNITTSTELLE FÜR LEITER & URLAUB
# ----------------------------------------------------
col_box1, col_box2 = st.columns(2)

# BOX 1: ABFRAGE STARTEN
with col_box1:
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.subheader("🚀 Anwesenheits-Abfrage")
    
    if user['rolle'] in ["Chef", "Teamleiter"]:
        if not st.session_state.show_abfrage_form:
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("👥 Eigene Gruppenabfrage", use_container_width=True, help="Nur für dein eigenes Team"):
                    st.session_state.show_abfrage_form = True
                    st.session_state.abfrage_typ = "gruppe"
                    st.rerun()
            with col_b2:
                if st.button("🌍 Gesamtabfrage (ALLE)", use_container_width=True, help="Hilferuf mit genauer Personenanzahl an alle"):
                    st.session_state.show_abfrage_form = True
                    st.session_state.abfrage_typ = "alle"
                    st.rerun()
        else:
            typ_text = "NUR DEINE GRUPPE" if st.session_state.abfrage_typ == "gruppe" else "ALLE ORDNER (Bedarfs-Abfrage)"
            st.warning(f"Typ der Abfrage: *{typ_text}*")
            
            # Unterschiedliche Eingabefelder je nach Typ
            if st.session_state.abfrage_typ == "alle":
                col_dat, col_anz = st.columns([2, 1])
                with col_dat:
                    gewaehltes_datum = st.date_input("Für welchen Sonntag:", value=aktueller_sonntag, key="abfrage_picker_all")
                with col_anz:
                    bedarf_personen = st.number_input("Benötigte Personen:", min_value=1, max_value=10, value=2, step=1)
            else:
                gewaehltes_datum = st.date_input("Für welchen Sonntag:", value=aktueller_sonntag, key="abfrage_picker_grp")
                bedarf_personen = 0
            
            col_send, col_cancel = st.columns(2)
            with col_send:
                if st.button("✅ Verbindlich starten", use_container_width=True):
                    if st.session_state.abfrage_typ == "gruppe":
                        neuer_abfrage_key = f"{user['gruppe']}_{gewaehltes_datum.strftime('%Y-%m-%d')}"
                        msg_text = f"📢 FECG Bruchmühlbach Ordner-App\n\nHallo {user['gruppe']}! {user['name']} hat eine neue Anwesenheits-Abfrage für Sonntag, den {gewaehltes_datum.strftime('%d.%m.%Y')} gestartet. Bitte stimmt ab:\n🔗 https://fecg-ordner.streamlit.app"
                    else:
                        neuer_abfrage_key = f"ALLE_{gewaehltes_datum.strftime('%Y-%m-%d')}"
                        msg_text = f"🚨 FECG Bruchmühlbach Ordner-App — HILFERUF\n\nHallo Männer! Für Sonntag, den {gewaehltes_datum.strftime('%d.%m.%Y')} werden dringend noch {int(bedarf_personen)} Ersatz-Ordner gebraucht! Wer helfen kann, klickt bitte sofort hier auf zusagen:\n🔗 https://fecg-ordner.streamlit.app"
                    
                    st.session_state.gruppen_abfragen[neuer_abfrage_key] = {
                        'status': 'offen', 
                        'typ': st.session_state.abfrage_typ,
                        'gestartet_von': user['name'],
                        'bedarf': bedarf_personen,
                        'helfer': [],
                        'rueckmeldungen': {}
                    }
                    
                    sende_whatsapp_benachrichtigung(msg_text)
                    st.session_state.show_abfrage_form = False
                    st.session_state.abfrage_typ = None
                    st.success("Abfrage erfolgreich gestartet!")
                    st.rerun()
            with col_cancel:
                if st.button("❌ Abbrechen", key="cancel_abfrage", use_container_width=True):
                    st.session_state.show_abfrage_form = False
                    st.session_state.abfrage_typ = None
                    st.rerun()
                    
        # AUSWERTUNG FÜR LEITER
        st.write("#### 📊 Status deiner gestarteten Abfragen:")
        for k_abfrage, v_abfrage in st.session_state.gruppen_abfragen.items():
            if k_abfrage.startswith(user['gruppe']) or v_abfrage.get('typ') == 'alle':
                d_str = k_abfrage.split("_")[1]
                
                if v_abfrage.get('typ') == 'alle':
                    h_liste = v_abfrage.get('helfer', [])
                    b_max = v_abfrage.get('bedarf', 1)
                    st.write(f"*Sonntag, {d_str} (Gesamtabfrage):*")
                    st.info(f"Besetzt: *{len(h_liste)} von {b_max} Plätzen*")
                    if h_liste:
                        st.text(f"Eingesprungen sind: {', '.join(h_liste)}")
                    else:
                        st.text("⏳ Noch keine Zusagen vorhanden.")
                else:
                    st.write(f"*Sonntag, {d_str} (Eigene Gruppe):*")
                    team = [m for m in st.session_state.mitglieder if m['gruppe'] == user['gruppe']]
                    for t_mitglied in team:
                        status = v_abfrage['rueckmeldungen'].get(t_mitglied['name'], "⏳ Keine Rückmeldung")
                        st.text(f" • {t_mitglied['name']}: {status}")
    else:
        st.info("Nur Gruppenleiter können Abfragen starten.")
    st.markdown("</div>", unsafe_allow_html=True)

# BOX 2: URLAUB EINTRAGEN
with col_box2:
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.subheader("🌴 Urlaubsverwaltung")
    
    if not st.session_state.show_urlaub_form:
        if st.button("📅 Abwesenheit / Urlaub eintragen", use_container_width=True):
            st.session_state.show_urlaub_form = True
            st.rerun()
    else:
        st.info("📅 Wähle den Zeitraum deines Urlaubs aus:")
        u_von = st.date_input("Urlaub von (Erster Tag):", value=heute, key="u_von")
        u_bis = st.date_input("Urlaub bis (Letzter Tag):", value=heute + timedelta(days=7), key="u_bis")
        
        col_save_u, col_cancel_u = st.columns(2)
        with col_save_u:
            if st.button("✅ Verbindlich eintragen", use_container_width=True):
                st.session_state.urlaube.append({'name': user['name'], 'von': u_von, 'bis': u_bis})
                st.session_state.show_urlaub_form = False
                st.success("Urlaub erfolgreich eingetragen!")
                st.rerun()
        with col_cancel_u:
            if st.button("❌ Abbrechen", key="cancel_urlaub", use_container_width=True):
                st.session_state.show_urlaub_form = False
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.write("---")

# ----------------------------------------------------
# 4. GRUPPENÜBERGREIFENDE ERSATZSUCHE (ALT-LOGIK BLEIBT ALS BACKUP)
# ----------------------------------------------------
st.write("### 📢 Gruppenübergreifende Notfall-Suchen")
aktive_ersatz_suchen = [s for s in st.session_state.ersatz_suchen if user['gruppe'] != s['von_gruppe']]

if not aktive_ersatz_suchen:
    st.write("Keine offenen Ersatzsuchen aus anderen Gruppen vorhanden.")
else:
    for idx, suche in enumerate(st.session_state.ersatz_suchen):
        if user['gruppe'] != suche['von_gruppe']:
            st.warning(f"⚠️ *{suche['von_gruppe']}* sucht dringend {suche['anzahl']} Ersatz-Ordner für Sonntag!")
            st.write(f"Bereits zugesagt: {', '.join(suche['helfer']) if suche['helfer'] else 'Niemand'}")
            
            if user['name'] in suche['helfer']:
                st.success("✅ Du hast hier bereits verbindlich zugesagt!")
            else:
                if st.button(f"🤝 Als {user['name']} verbindlich einspringen", key=f"ersatz_{idx}"):
                    suche['helfer'].append(user['name'])
                    st.rerun()
