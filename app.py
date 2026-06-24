import streamlit as st
import sqlite3
from datetime import datetime, timedelta

# 1. DATENBANK INITIALISIEREN
def init_db():
    conn = sqlite3.connect('kirche_ordner.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mitglieder (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, gruppe TEXT, rolle TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS urlaub (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, von_datum TEXT, bis_datum TEXT)''')
    c.execute("SELECT COUNT(*) FROM mitglieder")
    if c.fetchone()[0] == 0:
        alle_mitglieder = [
            ('Komjagin Andreas', 'andreas@kirche.de', 'Gruppe 1', 'Chef'),
            ('Hauf Valintin', 'valintin@kirche.de', 'Gruppe 1', 'Mitarbeiter'),
            ('Geier Enriko', 'enriko@kirche.de', 'Gruppe 1', 'Mitarbeiter'),
            ('Ilchuk Vasyl', 'vasyl@kirche.de', 'Gruppe 1', 'Mitarbeiter'),
            ('Volkov Slawik', 'slawik@kirche.de', 'Gruppe 2', 'Teamleiter'),
            ('Tissen Eduard', 'eduard@kirche.de', 'Gruppe 2', 'Mitarbeiter'),
            ('Eberhart Wili', 'wili@kirche.de', 'Gruppe 2', 'Mitarbeiter'),
            ('Paul Steffen', 'steffen@kirche.de', 'Gruppe 2', 'Mitarbeiter'),
            ('Schäfer Peter', 'peter@kirche.de', 'Gruppe 3', 'Teamleiter'),
            ('Akulenko Wili', 'wili.a@kirche.de', 'Gruppe 3', 'Mitarbeiter'),
            ('Hermann Bogdan', 'bogdan@kirche.de', 'Gruppe 3', 'Mitarbeiter')
        ]
        c.executemany("INSERT INTO mitglieder (name, email, gruppe, rolle) VALUES (?, ?, ?, ?)", alle_mitglieder)
    conn.commit()
    conn.close()

init_db()

def get_dienst_gruppe(datum):
    basis_datum = datetime(2026, 6, 21).date()
    tage_differenz = (datum - basis_datum).days
    return ["Gruppe 1", "Gruppe 2", "Gruppe 3"][(tage_differenz // 7) % 3]

st.set_page_config(page_title="Ordner Team App", page_icon="⛪")
st.title("⛪ Ordner-Team App Kirchengemeinde")

st.sidebar.header("🔐 Login")
user_email = st.sidebar.text_input("Deine E-Mail:", value="andreas@kirche.de").strip()

conn = sqlite3.connect('kirche_ordner.db')
c = conn.cursor()
c.execute("SELECT name, gruppe, rolle FROM mitglieder WHERE email = ?", (user_email,))
user_data = c.fetchone()

if user_data:
    name, gruppe, rolle = user_data
    st.sidebar.success(f"Hallo {name}!\nRolle: {rolle} ({gruppe})")
    
    # STATUSANZEIGE
    st.write("### 📅 Aktuelle Dienstwoche")
    heute = datetime.now().date()
    aktueller_sonntag = heute - timedelta(days=(heute.weekday() + 1) % 7)
    naechster_samstag = aktueller_sonntag + timedelta(days=6)
    dienst_gruppe = get_dienst_gruppe(aktueller_sonntag)
    
    # Urlaube prüfen
    c.execute("SELECT email FROM mitglieder WHERE gruppe = ?", (dienst_gruppe,))
    g_mitglieder = [m[0] for m in c.fetchall()]
    abwesende = 0
    for m_email in g_mitglieder:
        c.execute("SELECT COUNT(*) FROM urlaub WHERE email = ? NOT (von_datum > ? OR bis_datum < ?)", 
                  (m_email, naechster_samstag.strftime('%Y-%m-%d'), aktueller_sonntag.strftime('%Y-%m-%d')))
        if c.fetchone()[0] > 0: abwesende += 1
            
    if abwesende == 0: st.success(f"🟢 *{dienst_gruppe}* hat Dienst. Alle da!")
    elif abwesende == 1: st.warning(f"🟡 *{dienst_gruppe}* hat Dienst. 1 Person im Urlaub!")
    else: st.error(f"🔴 *{dienst_gruppe}* hat Dienst. {abwesende} Personen im Urlaub! Hilfe nötig!")

    # CHEF REGISTRIERUNG
    if rolle == "Chef":
        st.write("---")
        st.subheader("🛠️ Chef-Bereich: Mitarbeiter hinzufügen")
        n_name = st.text_input("Name:")
        n_email = st.text_input("E-Mail:")
        n_grp = st.selectbox("Gruppe:", ["Gruppe 1", "Gruppe 2", "Gruppe 3"])
        n_rol = st.selectbox("Rolle:", ["Mitarbeiter", "Teamleiter"])
        if st.button("Speichern"):
            if n_name and n_email:
                try:
                    c.execute("INSERT INTO mitglieder (name, email, gruppe, rolle) VALUES (?, ?, ?, ?)", (n_name, n_email, n_grp, n_rol))
                    conn.commit()
                    st.success("Hinzugefügt!")
                    st.rerun()
                except: st.error("E-Mail existiert schon!")

    # URLAUBS BUTTON FÜR MITARBEITER
    st.write("---")
    st.subheader("🌴 Abwesenheit melden")
    von = st.date_input("Von:", value=heute)
    bis = st.date_input("Bis:", value=heute+timedelta(days=7))
    if st.button("Urlaub eintragen"):
        c.execute("INSERT INTO urlaub (email, von_datum, bis_datum) VALUES (?, ?, ?)", (user_email, von.strftime('%Y-%m-%d'), bis.strftime('%Y-%m-%d')))
        conn.commit()
        st.success("Urlaub gespeichert!")
        st.rerun()
else:
    st.sidebar.error("E-Mail unbekannt.")
conn.close()
