"""Aussehen der App und Einrichtung als Symbol auf dem Startbildschirm.

Alles hier ist Kosmetik: Fällt ein Kniff aus, weil Streamlit seine internen
Namen ändert, sieht die App schlichter aus – funktionieren tut sie weiter.
"""

from __future__ import annotations

import base64
import json
from functools import lru_cache
from pathlib import Path

import streamlit as st

# Der Baustein für eigenes HTML heißt je nach Streamlit-Fassung anders: seit
# 1.63 st.iframe, davor st.components.v1.html (das wird abgekündigt). st.iframe
# lässt die Höhe 0 nicht zu, deshalb ist die kleinste erlaubte Höhe hinterlegt.
_html_baustein = getattr(st, "iframe", None)
_html_hoehe = 1
if _html_baustein is None:  # pragma: no cover - ältere Streamlit-Fassungen
    _html_hoehe = 0
    try:
        from streamlit.components.v1 import html as _html_baustein
    except ImportError:
        _html_baustein = None

STATISCH = Path(__file__).resolve().parents[1] / "static"
ICON = STATISCH / "app-icon-180.png"
ICON_GROSS = STATISCH / "app-icon.png"
# Randfüllend und ohne Durchsichtigkeit – iOS füllt durchsichtige Ecken schwarz.
ICON_APPLE = STATISCH / "app-icon-apple.png"

# Farben: einmal für hell, einmal für dunkel – die App folgt dem Gerät.
FARBEN_HELL = {
    "grund": "#f4f7fa",
    "flaeche": "#ffffff",
    "rand": "#e3e9f0",
    "text": "#12263a",
    "gedaempft": "#5b6b7c",
    "akzent": "#176a94",
    "akzent_dunkel": "#0e2b47",
    "schatten": "0 1px 2px rgba(16,40,64,.06), 0 8px 24px rgba(16,40,64,.06)",
}
FARBEN_DUNKEL = {
    "grund": "#0f1620",
    "flaeche": "#172230",
    "rand": "#24344a",
    "text": "#e8eef5",
    "gedaempft": "#9fb0c2",
    "akzent": "#1f6f96",
    "akzent_dunkel": "#0b1926",
    "schatten": "0 1px 2px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.35)",
}


@lru_cache(maxsize=4)
def _bild_als_datenadresse(pfad: str) -> str:
    daten = Path(pfad).read_bytes()
    return "data:image/png;base64," + base64.b64encode(daten).decode("ascii")


def _variablen(farben: dict) -> str:
    return "\n".join(f"    --nk-{name.replace('_', '-')}: {wert};" for name, wert in farben.items())


def _stil() -> str:
    return f"""
<style>
:root {{
{_variablen(FARBEN_HELL)}
    --nk-radius: 14px;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
{_variablen(FARBEN_DUNKEL)}
  }}
}}

/* ---------- Grundgerüst ---------- */
.stApp {{ background: var(--nk-grund); }}
[data-testid="stAppViewContainer"] > .main .block-container {{
    max-width: 1120px;
    padding-top: 1.2rem;
    padding-bottom: 4rem;
}}
[data-testid="stDecoration"], footer {{ display: none !important; }}
[data-testid="stHeader"] {{ background: transparent; height: 0; }}
/* In der Werkzeugleiste sitzt neben „Deploy" und dem Menue auch der Knopf, der
   die Seitenleiste aufklappt. Blendet man die Leiste ganz aus, gibt es auf dem
   Handy keinen Weg mehr in die Seitenleiste - und damit keinen an Sichern,
   Laden und die Angabe, wo die Daten liegen. Also nur die Teile ausblenden,
   die niemand braucht, und den Knopf freistellen. */
[data-testid="stToolbarActions"], [data-testid="stAppDeployButton"],
#MainMenu, [data-testid="stMainMenu"] {{ display: none !important; }}
[data-testid="stToolbar"] {{ background: transparent; }}
[data-testid="stExpandSidebarButton"] {{
    position: fixed; top: .45rem; left: .45rem; z-index: 1000;
    background: var(--nk-flaeche); border: 1px solid var(--nk-rand);
    border-radius: 10px; width: 2.6rem; height: 2.6rem;
    box-shadow: 0 2px 8px rgba(16, 40, 66, .12);
}}
h1, h2, h3, h4 {{ color: var(--nk-text); letter-spacing: -.01em; }}
h4 {{ font-size: 1.02rem; margin: 1.4rem 0 .4rem; }}

/* ---------- Kopfzeile ---------- */
.nk-kopf {{
    display: flex; align-items: center; gap: 14px;
    padding: 16px 18px; margin-bottom: 14px;
    border-radius: var(--nk-radius);
    background: linear-gradient(135deg, var(--nk-akzent-dunkel), var(--nk-akzent));
    box-shadow: var(--nk-schatten);
}}
.nk-kopf img {{ width: 46px; height: 46px; border-radius: 11px; flex: none; }}
.nk-kopf .nk-titel {{ color: #fff; font-size: 1.24rem; font-weight: 650; line-height: 1.2; }}
.nk-kopf .nk-unter {{ color: rgba(255,255,255,.82); font-size: .84rem; margin-top: 2px; }}

/* ---------- Reiter als Kacheln ---------- */
.stApp [role="tablist"] {{
    gap: 6px; flex-wrap: wrap; background: transparent;
    border-bottom: none !important; box-shadow: none !important; padding-bottom: 4px;
}}
.stApp [role="tablist"]::after, .stApp [role="tablist"]::before {{ display: none !important; }}
.stApp [role="tab"] {{
    height: auto !important; padding: 8px 14px !important; border-radius: 999px !important;
    background: var(--nk-flaeche); border: 1px solid var(--nk-rand) !important;
    color: var(--nk-gedaempft); font-weight: 550; font-size: .88rem;
    box-shadow: none !important;
}}
.stApp [role="tab"]::after, .stApp [role="tab"]::before {{ display: none !important; }}
.stApp [role="tab"][aria-selected="true"], .stApp [role="tab"][data-selected] {{
    background: var(--nk-akzent) !important; border-color: var(--nk-akzent) !important;
    color: #fff !important;
}}
.stApp [role="tab"][aria-selected="true"] p, .stApp [role="tab"][data-selected] p {{
    color: #fff !important;
}}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"],
.react-aria-SelectionIndicator {{ display: none !important; }}

/* ---------- Bereichswahl (Segmentschalter) als Kacheln ---------- */
.stApp [role="radiogroup"]:has(button[data-variant="segmented_control"]) {{
    gap: 6px; flex-wrap: wrap; border: none !important; background: transparent !important;
}}
.stApp button[data-variant="segmented_control"] {{
    border-radius: 999px !important; padding: 8px 14px !important;
    background: var(--nk-flaeche) !important; border: 1px solid var(--nk-rand) !important;
    color: var(--nk-gedaempft) !important; font-weight: 550; font-size: .88rem;
    box-shadow: none !important; margin: 0 !important;
}}
.stApp button[data-variant="segmented_control"][aria-checked="true"],
.stApp button[data-variant="segmented_control"][data-selected="true"] {{
    background: var(--nk-akzent) !important; border-color: var(--nk-akzent) !important;
    color: #fff !important;
}}
.stApp button[data-variant="segmented_control"][aria-checked="true"] p,
.stApp button[data-variant="segmented_control"][data-selected="true"] p {{
    color: #fff !important;
}}

/* ---------- Suche und Fragezeichen ---------- */
.stApp [data-testid="stTextInput"]:has(input[aria-label="Suchen"]) input {{
    font-size: .95rem;
}}
.stApp [data-testid="stPopover"] button {{
    border-radius: 50% !important; width: 38px; min-width: 38px; height: 38px;
    padding: 0 !important; font-size: 1.05rem; font-weight: 700;
    color: var(--nk-akzent) !important;
}}
.stApp [data-testid="stPopover"] button svg {{ display: none; }}

/* ---------- Karten, Kennzahlen, Hinweise ---------- */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) {{
    border-radius: var(--nk-radius);
}}
.stApp details, div[data-testid="stExpander"] {{
    border: 1px solid var(--nk-rand) !important; border-radius: var(--nk-radius) !important;
    background: var(--nk-flaeche); box-shadow: var(--nk-schatten); overflow: hidden;
}}
.stApp details summary {{ font-weight: 550; padding: .55rem .9rem; }}
[data-testid="stMetric"] {{
    background: var(--nk-flaeche); border: 1px solid var(--nk-rand);
    border-radius: var(--nk-radius); padding: 14px 16px; box-shadow: var(--nk-schatten);
}}
[data-testid="stMetricLabel"] p {{
    font-size: .74rem !important; text-transform: uppercase; letter-spacing: .06em;
    color: var(--nk-gedaempft) !important; font-weight: 600;
}}
[data-testid="stMetricValue"] {{ font-size: 1.6rem !important; font-weight: 650; }}
.stAlert {{ border-radius: 12px; border: 1px solid var(--nk-rand); }}

/* ---------- Bedienelemente ---------- */
.stButton button, .stDownloadButton button, .stFormSubmitButton button {{
    border-radius: 11px; font-weight: 600; padding: .55rem 1rem;
    border: 1px solid var(--nk-rand); transition: transform .06s ease, box-shadow .15s ease;
}}
.stButton button:hover, .stDownloadButton button:hover {{ transform: translateY(-1px); }}
.stDownloadButton button[kind="primary"], .stButton button[kind="primary"] {{
    background: var(--nk-akzent); border-color: var(--nk-akzent); color: #fff;
    box-shadow: var(--nk-schatten);
}}
input, textarea, [data-baseweb="select"] > div, [data-baseweb="input"] {{
    border-radius: 10px !important;
}}
.stApp [data-testid="stTextInput"] > div, .stApp [data-testid="stNumberInput"] > div,
.stApp [data-baseweb="select"] > div {{
    background: var(--nk-flaeche) !important;
    border: 1px solid var(--nk-rand) !important;
}}
.stApp [data-testid="stTextInput"] input, .stApp [data-testid="stNumberInput"] input {{
    background: transparent !important;
}}
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {{
    border-radius: 12px; overflow: hidden; border: 1px solid var(--nk-rand);
}}

/* ---------- Seitenleiste ---------- */
[data-testid="stSidebarContent"] {{
    background: var(--nk-flaeche); border-right: 1px solid var(--nk-rand);
}}

/* ---------- Handy ---------- */
@media (max-width: 640px) {{
    [data-testid="stAppViewContainer"] > .main .block-container {{
        padding: .6rem .8rem 3rem; }}
    .nk-kopf {{ padding: 12px 14px; }}
    .nk-kopf img {{ width: 38px; height: 38px; }}
    .nk-kopf .nk-titel {{ font-size: 1.05rem; }}
    .stTabs [data-baseweb="tab-list"] {{
        flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; }}
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {{ display: none; }}
    .stTabs [data-baseweb="tab"] {{ white-space: nowrap; }}
    [data-testid="stMetricValue"] {{ font-size: 1.3rem !important; }}
    input, .stButton button, .stDownloadButton button {{ min-height: 44px; }}
}}

/* Der Rahmen, der die Startbildschirm-Angaben einträgt, ist 1px hoch, weil
   Streamlit die Höhe 0 nicht mehr zulässt. Hier nimmt er keinen Platz ein.
   Kein display:none - dann führen manche Browser das Skript darin nicht aus. */
[data-testid="stIFrame"] {{ height: 0 !important; min-height: 0 !important; }}
</style>
"""


def _statisch_wird_ausgeliefert() -> bool:
    """Liefert Streamlit den Ordner static/ unter /app/static/ aus?"""
    try:
        return bool(st.get_option("server.enableStaticServing"))
    except Exception:  # pragma: no cover - je nach Streamlit-Fassung
        return False


def _symboladresse(datei: Path, ausgeliefert: bool) -> str:
    """Echte Adresse, wenn der Ordner static/ ausgeliefert wird – sonst leer.

    Nur das apple-touch-icon braucht das: iOS nimmt für den Startbildschirm
    keine Datenadresse an, sondern ausschließlich eine echte URL. Auf der
    Streamlit Community Cloud wird static/ aber nicht zuverlässig ausgeliefert,
    auch mit enableStaticServing nicht – deshalb ist das hier ein Angebot und
    keine Zusage, und alles andere kommt ohne aus.
    """
    if not datei.exists() or not ausgeliefert:
        return ""
    return "/app/static/" + datei.name


def _startbildschirm_angaben() -> dict:
    """Manifest und Symbole für den Startbildschirm.

    Die Symbole stecken als Datenadresse direkt in der Seite. Damit hängt das
    Bild auf dem Startbildschirm an nichts weiter – weder an einer Einstellung
    in .streamlit/config.toml noch daran, ob der Betreiber Dateien ausliefert.
    """
    def daten(datei: Path) -> str:
        return _bild_als_datenadresse(str(datei)) if datei.exists() else ""

    gross = daten(ICON_GROSS)
    klein = daten(ICON) or gross
    symbole = []
    if klein:
        symbole.append({"src": klein, "sizes": "180x180", "type": "image/png"})
    if gross:
        symbole.append({"src": gross, "sizes": "512x512", "type": "image/png"})
        symbole.append({"src": gross, "sizes": "512x512", "type": "image/png",
                        "purpose": "maskable"})
    # Fürs iPhone die echte Adresse, wenn es sie gibt; sonst bleibt nur die
    # Datenadresse, mit der iOS zwar nichts anfängt, Chrome aber schon.
    apfel = _symboladresse(ICON_APPLE, _statisch_wird_ausgeliefert()) or daten(ICON_APPLE) or klein
    return {
        "manifest": {
            "name": "Nebenkostenabrechnung",
            "short_name": "Nebenkosten",
            "description": "Betriebskostenabrechnung für die vermietete Wohnung",
            "display": "standalone",
            "orientation": "portrait",
            "background_color": "#f6f8fb",
            "theme_color": "#0e2b47",
            "lang": "de",
            "icons": symbole,
        },
        "symbol": klein,
        "apfel": apfel,
    }


def _startbildschirm() -> None:
    """Symbol, Name und Farbe für „Zum Startbildschirm hinzufügen" hinterlegen.

    Die Angaben gehören in den Kopf der Seite. Streamlit rendert Bausteine in
    einem eigenen Rahmen, deshalb schreibt dieses Schnipsel sie von dort aus in
    die umgebende Seite – einmal, danach ist alles schon vorhanden.

    start_url und scope trägt erst das Skript ein: In einer Datenadresse sind
    relative Angaben ungültig und der Browser wirft das Manifest weg.
    """
    if _html_baustein is None:
        return
    angaben = json.dumps(_startbildschirm_angaben())
    _html_baustein(
        """
<script>
(function () {
  const kopf = window.parent.document.head;
  if (!kopf || kopf.querySelector('link[rel="manifest"]')) return;
  const angaben = ANGABEN;
  const ort = window.parent.location;
  // Im Manifest muss jede Adresse vollstaendig sein: es haengt selbst in einer
  // Datenadresse, und dagegen laesst sich nichts Relatives aufloesen.
  const voll = (a) => (a && a.startsWith('/') ? ort.origin + a : a);
  const manifest = Object.assign({}, angaben.manifest, {
    start_url: ort.origin + ort.pathname,
    scope: ort.origin + ort.pathname.replace(/[^/]*$/, ''),
    icons: (angaben.manifest.icons || []).map(
      (s) => Object.assign({}, s, {src: voll(s.src)})),
  });
  const alsAdresse = 'data:application/manifest+json;base64,' +
    btoa(unescape(encodeURIComponent(JSON.stringify(manifest))));
  const eintraege = [
    ['link', {rel: 'manifest', href: alsAdresse}],
    ['meta', {name: 'apple-mobile-web-app-capable', content: 'yes'}],
    ['meta', {name: 'apple-mobile-web-app-title', content: 'Nebenkosten'}],
    ['meta', {name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent'}],
    ['meta', {name: 'theme-color', content: '#0e2b47'}],
    ['meta', {name: 'mobile-web-app-capable', content: 'yes'}],
  ];
  if (angaben.apfel) {
    for (const alt of kopf.querySelectorAll('link[rel="apple-touch-icon"]')) alt.remove();
    eintraege.push(['link', {rel: 'apple-touch-icon', sizes: '180x180', href: angaben.apfel}]);
  }
  if (angaben.symbol) {
    eintraege.push(['link', {rel: 'icon', type: 'image/png', href: angaben.symbol}]);
  }
  for (const [art, eigenschaften] of eintraege) {
    const knoten = window.parent.document.createElement(art);
    for (const [name, wert] of Object.entries(eigenschaften)) knoten.setAttribute(name, wert);
    kopf.appendChild(knoten);
  }
})();
</script>
""".replace("ANGABEN", angaben),
        height=_html_hoehe,
    )


def anwenden() -> None:
    """Stil laden und die App als Startbildschirm-Symbol anmeldbar machen."""
    st.markdown(_stil(), unsafe_allow_html=True)
    _startbildschirm()


def kopfzeile(titel: str, untertitel: str = "") -> None:
    logo = f'<img src="{_bild_als_datenadresse(str(ICON))}" alt="">' if ICON.exists() else ""
    st.markdown(
        f"""<div class="nk-kopf">{logo}
        <div><div class="nk-titel">{titel}</div>
        <div class="nk-unter">{untertitel}</div></div></div>""",
        unsafe_allow_html=True,
    )


def startbildschirm_hilfe() -> None:
    """Anleitung, wie die App als Symbol auf dem Handy landet."""
    with st.expander("📲 App auf den Startbildschirm legen"):
        st.markdown(
            """
Die App läuft im Browser, lässt sich aber wie eine richtige App ablegen – mit
eigenem Symbol, ohne Adresszeile.

**iPhone und iPad (Safari)**
1. Die Adresse der App in **Safari** öffnen (nicht in Chrome).
2. Unten auf **Teilen** tippen (Quadrat mit Pfeil nach oben).
3. **Zum Home-Bildschirm** wählen, Namen bestätigen.

**Android (Chrome)**
1. Die Adresse in **Chrome** öffnen.
2. Oben rechts auf die **drei Punkte** tippen.
3. **App installieren** oder **Zum Startbildschirm hinzufügen** wählen.

Läuft die App auf dem eigenen Rechner, muss dieser eingeschaltet und im selben
WLAN sein. Soll sie von überall erreichbar sein, gehört sie in die Streamlit
Cloud – dann bitte auch die Google-Tabelle als Ablage einrichten, sonst sind die
Daten nach einem Neustart weg.
            """
        )
