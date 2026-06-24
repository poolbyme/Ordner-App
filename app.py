import streamlit as st
from datetime import datetime, timedelta

# OBERFLÄCHE INITIALISIEREN
st.set_page_config(page_title="Ordner Team App", page_icon="⛪", layout="centered")

# LIVE-SPEICHER INITIALISIEREN (Verhindert Datenbank-Fehler online)
if "mitglieder" not in st.session_state:
    st.session_state.mitglieder = [
        # Gruppe 1 (4 Personen)
        {'name': 'Komjagin Andreas', 'email': 'andreas@kirche.de', 'gruppe': 'Gruppe 1', 'rolle': 'Chef'},
        {'name': 'Hauf Valintin', 'email': 'valintin@kirche.de', 'gruppe': 'Gruppe 1', 'rolle': 'Mitarbeiter'},
        {'name': 'Geier Enriko', 'email': 'enriko@kirche.de', 'gruppe': 'Gruppe 1', 'rolle': 'Mitarbeiter'},
        {'name': 'Ilchuk Vasyl', 'email': 'vasyl@kirche.de', 'gruppe': 'Gruppe 1', 'rolle': 'Mitarbeiter'},
        # Gruppe 2 (4 Personen)
        {'name': 'Volkov Slawik', 'email': 'slawik@kirche.de', 'gruppe': 'Gruppe 2', 'rolle': 'Teamleiter'},
        {'name': 'Tissen Eduard', 'email': 'eduard@kirche.de', 'gruppe': 'Gruppe 2', 'rolle': 'Mitarbeiter'},
        {'name': 'Eberhart Wili', 'email': 'wili@kirche.de', 'gruppe': 'Gruppe 2', 'rolle': 'Mitarbeiter'},
        {'name': 'Paul Steffen', 'email': 'steffen@kirche.de', 'gruppe': 'Gruppe 2', 'rolle': 'Mitarbeiter'},
        # Gruppe 3 (3 Personen)
        {'name': 'Schäfer Peter', 'email': 'peter@kirche.de', 'gruppe': 'Gruppe 3', 'rolle': 'Teamleiter'},
        {'name': 'Akulenko Wili', 'email': 'wili.a@kirche.de', 'gruppe': 'Gruppe 3', 'rolle': 'Mitarbeiter'},
        {'name': 'Hermann Bogdan', 'email': 'bogdan@kirche.de', 'gruppe': 'Gruppe 3', 'rolle': 'Mitarbeiter'}
    ]

if "urlaube" not in st.session_state:
    st.session_state.urlaube = [] # Speichert Wörterbücher: {'email': ..., 'von': ..., 'bis': ...}

if "anfragen" not in st.session_state:
    st.session_state.anfragen = [] # Speichert offene Hilferufe

# HELFER: Wer hat diese Woche Dienst?
def get_dienst_gruppe(datum):
    basis_datum = datetime(2026, 6, 21).date()
    wochen = (datum - basis_datum).days // 7
    return ["Gruppe 1", "Gruppe 2", "Gruppe 3"][wochen % 3]

st.title("⛪ Ordner-Team App Kirchengemeinde")

# LOGIN IN DER SEITENLEISTE
st.sidebar.header("🔐 Login")
user_email = st.sidebar.text_input("Deine E-Mail:", value="andreas@kirche.de").strip()

# Benutzer suchen
user = next((m for m in st.session_state.mitglieder if m['email'] == user_email), None)

if user:
    st.sidebar.success(f"Hallo {user['name']}!\n{user['rolle']} ({user['gruppe']})")
    
    # ----------------------------------------------------
    # 1. STATUSANZEIGE (DIENSTWOCHE & FARBEN)
    # ----------------------------------------------------
    st.write("### 📅 Aktuelle Dienstwoche")
    heute = datetime.now().date()
    aktueller_sonntag = heute - timedelta(days=(heute.weekday() + 1) % 7)
    naechster_samstag = aktueller_sonntag + timedelta(days=6)
    dienst_gruppe = get_dienst_gruppe(aktueller_sonntag)
    
    # Zählen, wie viele der aktuellen Dienstgruppe im Urlaub sind
    g_mitglieder = [m['email'] for m in st.session_state.mitglieder if m['gruppe'] == daten_gruppe] if 'daten_gruppe' in locals() else [m['email'] for m in st.session_state.mitglieder if m['gruppe'] == dienst_gruppe]
    abwesende_zaehler = 0
    
    for url in st.session_state.urlaube:
        if url['email'] in g_mitglieder:
            # Überschneidungsprüfung
            if not (url['von'] > naechster_samstag or url['bis'] < aktueller_sonntag):
                abwesende_zaehler += 1
                
    if abwesende_zaehler == 0:
        st.success(f"🟢 *{dienst_gruppe}* hat Dienst. Alle Personen sind einsatzbereit!")
    elif abwesende_zaehler == 1:
        st.warning(f"🟡 *{dienst_gruppe}* hat Dienst. 1 Person ist im Urlaub / abwesend!")
    else:
        st.error(f"🔴 *{dienst_gruppe}* hat Dienst. {abwesende_zaehler} Personen im Urlaub! Dringend Ersatz benötigt!")

    # ----------------------------------------------------
    # 2. ANFRAGEN / HILFERUFE ANZEIGEN (Für alle sichtbar)
    # ----------------------------------------------------
    st.write("---")
    st.write("### 📢 Offene Suchen & Helferanfragen")
    
    aktive_anfragen = [a for a in st.session_state.anfragen if a['gesucht'] > 0]
    
    if not aktive_anfragen:
        st.info("Aktuell liegen keine Hilferufe oder Sondereinsätze vor.")
    else:
        for idx, anfrage in enumerate(st.session_state.anfragen):
            if anfrage['gesucht'] > 0:
                # Farbliche Unterscheidung der Kachel je nach Typ
                typ_titel = "⚠️ ERSATZ GESUCHT (Ausfall)" if anfrage['typ'] == "Ausfall" else "🎄 SONDEREINSATZ (Verstärkung)"
                bg_color = "orange" if anfrage['typ'] == "Ausfall" else "blue"
                
                st.markdown(f"*{typ_titel}*")
                st.info(f"Für das Datum: *{anfrage['datum'].strftime('%d.%m.%Y')}\n\nBenötigte Ordner: *{anfrage['gesucht']}*\n\n*Bereits zugesagt: {', '.join(anfrage['helfer']) if anfrage['helfer'] else 'Noch niemand'}")
                
                # Prüfen ob man selbst schon hilft oder in der Dienstgruppe ist
                if user['name'] in anfrage['helfer']:
                    st.text("✅ Du hast für diesen Dienst bereits verbindlich zugesagt!")
                elif user['gruppe'] == get_dienst_gruppe(anfrage['datum']) and anfrage['typ'] == "Ausfall":
                    st.text("ℹ️ Du hast in dieser Woche ohnehin regulären Dienst.")
                else:
                    if st.button(f"🤝 Verbindlich zusagen & helfen", key=f"zusage_{idx}"):
                        anfrage['gesucht'] -= 1
                        anfrage['helfer'].append(user['name'])
                        st.success("Danke! Deine Zusage wurde verbindlich registriert.")
                        st.rerun()

    # ----------------------------------------------------
    # 3. MITARBEITER BEREICH: URLAUB MELDEN
    # ----------------------------------------------------
    st.write("---")
    st.subheader("🌴 Abwesenheit / Urlaub melden")
    von_tag = st.date_input("Urlaub von:", value=heute, key="u_von")
    bis_tag = st.date_input("Urlaub bis:", value=heute + timedelta(days=7), key="u_bis")
    
    if st.button("Urlaub eintragen & speichern"):
        st.session_state.urlaube.append({'email': user_email, 'von': von_tag, 'bis': bis_tag})
        st.success("Dein Urlaub wurde verbindlich im System hinterlegt!")
        st.rerun()

    # ----------------------------------------------------
    # 4. CHEF & LEITER BEREICH (ANFRAGEN STARTEN / MITARBEITER)
    # ----------------------------------------------------
    if user['rolle'] in ["Chef", "Teamleiter"]:
        st.write("---")
        st.subheader("🛠️ Leiter-Bereich: Suchen & Hilfe koordinieren")
        
        tab1, tab2 = st.tabs(["🆘 Hilfe/Ersatz anfordern", "➕ Mitarbeiter hinzufügen (Nur Chef)"])
        
        with tab1:
            st.write("Starte hier eine Anfrage an das gesamte Team.")
            anfrage_typ = st.radio("Grund der Suche:", ["Ersatz wegen Ausfall / Urlaub", "Verstärkung wegen Feiertag / Event"])
            such_datum = st.date_input("Für welches Datum?", value=heute + timedelta(days=1))
            anzahl_helfer = st.number_input("Wie viele Ordner werden insgesamt gesucht?", min_value=1, max_value=6, value=1)
            
            if st.button("Hilferuf an alle Mitarbeiter senden"):
                typ_kurz = "Ausfall" if "Ausfall" in anfrage_typ else "Sondereinsatz"
                st.session_state.anfragen.append({
                    'typ': typ_kurz,
                    'datum': such_datum,
                    'gesucht': anzahl_helfer,
                    'helfer': []
                })
                st.success("Anfrage wurde erfolgreich für alle Mitarbeiter geschaltet!")
                st.rerun()
                
        with tab2:
            if user['rolle'] == "Chef":
                st.write("Neues Mitglied im System anlegen:")
                n_name = st.text_input("Vollständiger Name:")
                n_email = st.text_input("E-Mail-Adresse:")
                n_grp = st.selectbox("Gruppe:", ["Gruppe 1", "Gruppe 2", "Gruppe 3"])
                n_rol = st.selectbox("Rolle:", ["Mitarbeiter", "Teamleiter"])
                
                if st.button("Mitarbeiter abspeichern"):
                    if n_name and n_email:
                        st.session_state.mitglieder.append({'name': n_name, 'email': n_email, 'gruppe': n_grp, 'rolle': n_rol})
                        st.success(f"{n_name} wurde hinzugefügt!")
                        st.rerun()
            else:
                st.info("Mitarbeiter hinzufügen kann nur der Hauptverantwortliche (Chef).")

else:
    st.sidebar.error("E-Mail im System nicht gefunden.")
    st.warning("Bitte nutze deine hinterlegte E-Mail (z.B. 'andreas@kirche.de' für den Chef).")
