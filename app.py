import streamlit as st
from datetime import datetime, timedelta
from streamlit_calendar import calendar

st.set_page_config(page_title="Ordner Team App", page_icon="⛪", layout="wide")

# CSS FÜR SCHÖNERE FARBEN & CHAT-SPRECHBLASEN
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .chat-bubble-user {
        background-color: #e1ffc7;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 8px;
        border-left: 5px solid #28a745;
    }
    .chat-bubble-other {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 8px;
        border-left: 5px solid #007bff;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }
    .chat-system {
        background-color: #eee;
        padding: 5px;
        border-radius: 5px;
        text-align: center;
        font-size: 0.9em;
        color: #555;
    }
    .card-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.05);
        border-top: 4px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

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

if "leiter_chat" not in st.session_state:
    st.session_state.leiter_chat = [
        {'von': 'System', 'text': 'Willkommen im internen Chat der Gruppenleiter!', 'zeit': 'Info'}
    ]

def get_dienst_gruppe(datum):
    basis_datum = datetime(2026, 6, 21).date()
    wochen = (datum - basis_datum).days // 7
    return ["Gruppe 1", "Gruppe 2", "Gruppe 3"][wochen % 3]

# HEADER BANNER
STREAMPAGE_BANNER = "https://images.unsplash.com/photo-1438032005730-c779502df39b?q=80&w=1200&auto=format&fit=crop"
st.image(STREAMPAGE_BANNER, use_container_width=True)

st.title("⛪ Ordner-Team Planer & Leiter-Zentrale")

# TEST-LOGIN IN DER SEITENLEISTE
st.sidebar.header("🔐 Ansicht wechseln")
mitarbeiter_namen = [m['name'] for m in st.session_state.mitglieder]
ausgewaehlter_name = st.sidebar.selectbox("Du agierst gerade als:", mitarbeiter_namen, index=0)
user = next((m for m in st.session_state.mitglieder if m['name'] == ausgewaehlter_name), None)

st.sidebar.info(f"Rolle: {user['rolle']}\nTeam: {user['gruppe']}")

# ----------------------------------------------------
# INTERNER LEITER-CHAT (WHATSAPP-STYLE)
# ----------------------------------------------------
if user['rolle'] in ["Chef", "Teamleiter"]:
    st.write("### 💬 Interner Gruppenleiter-Chat")
    
    for msg in st.session_state.leiter_chat:
        if msg['zeit'] == 'Info':
            st.markdown(f"<div class='chat-system'>ℹ️ {msg['text']}</div>", unsafe_allow_html=True)
        elif msg['von'] == user['name']:
            st.markdown(f"<div class='chat-bubble-user'><b>Du</b> ({msg['zeit']})<br>➔ {msg['text']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-bubble-other'><b>{msg['von']}</b> ({msg['zeit']})<br>➔ {msg['text']}</div>", unsafe_allow_html=True)
