"""Nebenkostenabrechnung – Streamlit-App.

Start:  streamlit run nebenkosten_app.py
"""

from __future__ import annotations

import json
from datetime import date

import pandas as pd
import streamlit as st

from nebenkosten.berechnung import (
    berechne, eur, menge, parse_datum, verbrauchsaufteilung, zahl,
)
from nebenkosten import speicher
from nebenkosten.modell import (
    ABRECHNUNGSARTEN, DIFFERENZ_VERTEILUNG, SCHLUESSEL, Position, Stammdaten,
    as_dict, from_dict, standard_positionen,
)
from nebenkosten.pdf import dateiname, erzeuge_pdf

st.set_page_config(page_title="Nebenkostenabrechnung", page_icon="🏠", layout="wide")

SCHLUESSEL_LABELS = list(SCHLUESSEL.values())
LABEL_ZU_KEY = {v: k for k, v in SCHLUESSEL.items()}

# Spalten der Kostentabelle
SP_AKTIV = "Abrechnen"
SP_NAME = "Kostenart"
SP_BETRAG = "Kosten fürs ganze Haus (€)"
SP_VERTEILUNG = "Verteilung"
SP_LOHN = "davon Lohnkosten (€)"
SP_ZEIT = "zeitanteilig"
SP_BELEG = "Welcher Beleg?"

SPALTEN_EINFACH = (SP_AKTIV, SP_NAME, SP_BETRAG, SP_VERTEILUNG, SP_BELEG)
SPALTEN_ERWEITERT = (SP_AKTIV, SP_NAME, SP_BETRAG, SP_VERTEILUNG, SP_LOHN, SP_ZEIT, SP_BELEG)

BEHALTEN = {"stamm", "positionen", "erweitert"}


# --------------------------------------------------------------------------
# Zustand
# --------------------------------------------------------------------------
def init_state() -> None:
    # Nach dem Laden einer Datei müssen die Eingabefelder ihre alten Werte
    # vergessen. Das passiert hier, bevor irgendein Feld gezeichnet wird.
    if st.session_state.pop("_felder_leeren", False):
        for schluessel in [k for k in st.session_state if k not in BEHALTEN]:
            del st.session_state[schluessel]

    if "stamm" in st.session_state:
        return

    gespeichert = speicher.laden()
    if gespeichert:
        st.session_state.stamm, st.session_state.positionen = gespeichert
        return

    jahr = date.today().year - 1
    st.session_state.stamm = Stammdaten(
        zeitraum_von=date(jahr, 1, 1).isoformat(),
        zeitraum_bis=date(jahr, 12, 31).isoformat(),
        nutzung_von=date(jahr, 1, 1).isoformat(),
        nutzung_bis=date(jahr, 12, 31).isoformat(),
    )
    st.session_state.positionen = standard_positionen()


def sichern() -> None:
    """Alles in die Datei schreiben. Fehler landen sichtbar in der Seitenleiste."""
    try:
        speicher.speichern(st.session_state.stamm, st.session_state.positionen)
        st.session_state["_speicherfehler"] = ""
    except OSError as fehler:
        st.session_state["_speicherfehler"] = str(fehler)


def neu_zeichnen() -> None:
    st.session_state["_felder_leeren"] = True
    st.rerun()


def positionen_als_df(positionen: list[Position]) -> pd.DataFrame:
    return pd.DataFrame([{
        SP_AKTIV: p.aktiv,
        SP_NAME: p.bezeichnung,
        SP_BETRAG: float(p.betrag),
        SP_VERTEILUNG: SCHLUESSEL.get(p.schluessel, SCHLUESSEL["flaeche"]),
        SP_LOHN: float(p.arbeitskosten),
        SP_ZEIT: p.zeitanteilig,
        SP_BELEG: p.hinweis,
    } for p in positionen])


def df_als_positionen(df: pd.DataFrame, bestehend: list[Position]) -> list[Position]:
    """Tabelle zurück in Positionen wandeln.

    Zählerstände stehen nicht in der Tabelle, sondern im Tab „Zählerstände“ –
    sie werden über den Namen der Kostenart mitgenommen.
    """
    vorrat: dict[str, list[Position]] = {}
    for p in bestehend:
        vorrat.setdefault(p.bezeichnung.strip().lower(), []).append(p)

    positionen: list[Position] = []
    for _, r in df.iterrows():
        name = str(r.get(SP_NAME) or "").strip()
        if not name:
            continue

        def zahlwert(spalte: str, standard: float = 0.0) -> float:
            wert = r.get(spalte, standard)
            try:
                return float(wert) if pd.notna(wert) else standard
            except (TypeError, ValueError):
                return standard

        alt = vorrat.get(name.lower(), [])
        vorgaenger = alt.pop(0) if alt else None

        positionen.append(Position(
            bezeichnung=name,
            betrag=zahlwert(SP_BETRAG),
            schluessel=LABEL_ZU_KEY.get(str(r.get(SP_VERTEILUNG)), "flaeche"),
            verbrauch_gesamt=vorgaenger.verbrauch_gesamt if vorgaenger else 0.0,
            verbrauch_mieter=vorgaenger.verbrauch_mieter if vorgaenger else 0.0,
            zaehler_haus_alt=vorgaenger.zaehler_haus_alt if vorgaenger else 0.0,
            zaehler_haus_neu=vorgaenger.zaehler_haus_neu if vorgaenger else 0.0,
            zaehler_mieter_alt=vorgaenger.zaehler_mieter_alt if vorgaenger else 0.0,
            zaehler_mieter_neu=vorgaenger.zaehler_mieter_neu if vorgaenger else 0.0,
            zaehler_eigen_alt=vorgaenger.zaehler_eigen_alt if vorgaenger else 0.0,
            zaehler_eigen_neu=vorgaenger.zaehler_eigen_neu if vorgaenger else 0.0,
            verbrauch_eigen_direkt=vorgaenger.verbrauch_eigen_direkt if vorgaenger else 0.0,
            einheit=vorgaenger.einheit if vorgaenger else "",
            arbeitskosten=zahlwert(SP_LOHN, vorgaenger.arbeitskosten if vorgaenger else 0.0),
            zeitanteilig=bool(r.get(SP_ZEIT, vorgaenger.zeitanteilig if vorgaenger else True)),
            aktiv=bool(r.get(SP_AKTIV, True)),
            hinweis=str(r.get(SP_BELEG) or ""),
        ))
    return positionen


def _fmt(iso: str) -> str:
    d = parse_datum(iso)
    return d.strftime("%d.%m.%Y") if d else "—"


def datum_feld(label: str, wert: str, key: str, hilfe: str | None = None) -> str:
    vorgabe = parse_datum(wert) or date.today()
    return st.date_input(label, value=vorgabe, key=key, format="DD.MM.YYYY",
                         help=hilfe).isoformat()


init_state()
stamm: Stammdaten = st.session_state.stamm

# --------------------------------------------------------------------------
# Seitenleiste
# --------------------------------------------------------------------------
with st.sidebar:
    erweitert = st.toggle(
        "Mehr Einstellungen anzeigen", key="erweitert",
        help="Zeigt zusätzliche Felder: Lohnkosten für die Steuererklärung des "
             "Mieters, anteilige Abrechnung bei Ein- oder Auszug, Anschreiben.")

    st.header("Gespeichert wird automatisch")
    stand = speicher.gespeichert_am()
    if st.session_state.get("_speicherfehler"):
        st.error(f"Speichern nicht möglich: {st.session_state['_speicherfehler']}")
    elif stand:
        st.success(f"Zuletzt gespeichert: {stand.strftime('%d.%m.%Y um %H:%M:%S')}")
    else:
        st.info("Wird gespeichert, sobald du etwas eingibst.")
    st.caption(f"Ordner: `{speicher.ORDNER}`")

    st.download_button(
        "💾 Sicherungskopie herunterladen",
        data=json.dumps(as_dict(stamm, st.session_state.positionen),
                        ensure_ascii=False, indent=2).encode("utf-8"),
        file_name=f"nebenkosten_{(parse_datum(stamm.zeitraum_bis) or date.today()).year}.json",
        mime="application/json",
        width="stretch",
        help="Zusätzliche Kopie für den Fall, dass der Rechner kaputtgeht.",
    )
    hochgeladen = st.file_uploader("📂 Sicherungskopie einlesen", type="json")
    if hochgeladen is not None and st.button("Daten übernehmen", width="stretch"):
        try:
            neu_stamm, neu_pos = from_dict(json.load(hochgeladen))
            st.session_state.stamm = neu_stamm
            st.session_state.positionen = neu_pos
            sichern()
            neu_zeichnen()
        except Exception as fehler:  # noqa: BLE001 – Nutzerdatei kann alles enthalten
            st.error(f"Datei konnte nicht gelesen werden: {fehler}")

    abgelegt = speicher.archiv()
    if abgelegt:
        with st.expander(f"📁 Fertige Abrechnungen ({len(abgelegt)})"):
            auswahl = st.selectbox("Frühere Abrechnung", abgelegt,
                                   format_func=lambda pfad: pfad.stem.replace("_", " "))
            if st.button("Diese Abrechnung öffnen", width="stretch"):
                geladen = speicher.aus_archiv(auswahl)
                if geladen:
                    st.session_state.stamm, st.session_state.positionen = geladen
                    sichern()
                    neu_zeichnen()
                else:
                    st.error("Die Datei konnte nicht gelesen werden.")

    st.divider()
    if st.button("📅 Nächstes Jahr vorbereiten", width="stretch",
                 help="Schiebt den Zeitraum um ein Jahr weiter und leert Beträge "
                      "und Zählerstände. Namen und Flächen bleiben stehen."):
        for feld in ("zeitraum_von", "zeitraum_bis", "nutzung_von", "nutzung_bis"):
            d = parse_datum(getattr(stamm, feld))
            if d:
                try:
                    setattr(stamm, feld, d.replace(year=d.year + 1).isoformat())
                except ValueError:  # 29.02.
                    setattr(stamm, feld, d.replace(year=d.year + 1, day=28).isoformat())
        for p in st.session_state.positionen:
            p.betrag = p.arbeitskosten = 0.0
            p.verbrauch_gesamt = p.verbrauch_mieter = 0.0
            p.zaehler_haus_alt = p.zaehler_haus_neu = p.zaehler_haus_alt = 0.0
            p.zaehler_mieter_alt = p.zaehler_mieter_neu = 0.0
        stamm.datum = date.today().isoformat()
        stamm.abrechnungsart = "jahr"
        stamm.auszug_am = ""
        sichern()
        neu_zeichnen()

    if st.button("🗑️ Alles zurücksetzen", width="stretch"):
        st.session_state.pop("stamm", None)
        st.session_state.pop("positionen", None)
        neu_zeichnen()

    st.divider()
    st.caption(
        "Die App erstellt das Abrechnungsschreiben, sie ist keine Rechtsberatung. "
        "Bei Streit mit dem Mieter hilft der Haus- und Grundbesitzerverein oder "
        "ein Anwalt für Mietrecht."
    )

st.title("🏠 Nebenkostenabrechnung")

with st.expander("So geht's – bitte einmal lesen",
                 expanded=not (stamm.mieter_name or stamm.flaeche_gesamt)):
    st.markdown(
        """
**Was die App macht:** Sie verteilt die Kosten des Hauses auf dich und deinen Mieter,
zieht ab, was er schon vorausgezahlt hat, und schreibt daraus ein fertiges PDF.

**Was die App nicht weiß:** wie hoch deine Rechnungen waren. Die Beträge musst du
eintippen – die App kennt weder deinen Grundsteuerbescheid noch deine Gasrechnung.

**Einmal eintragen, dann steht es:** Haus, Wohnflächen, Grundstück und deine Daten
gibst du nur beim ersten Mal ein. Die App speichert alles automatisch und weiß es
beim nächsten Mal wieder. Jedes Jahr änderst du nur noch Zeitraum, Zählerstände
und Rechnungsbeträge.

**Das brauchst du für eine Abrechnung:**

* Grundsteuerbescheid, Müllgebühren, Wasser- und Abwasserrechnung
* Rechnungen für Gas, Öl oder Pellets, Schornsteinfeger, Wartung
* Gebäude- und Haftpflichtversicherung, Allgemeinstrom, Gartenpflege
* Zählerstände am Anfang und am Ende: Hauptzähler, Wohnung des Mieters, deine Wohnung
* was dein Mieter monatlich an Nebenkostenvorauszahlung überwiesen hat

**Zwei Dinge, die du vorher wissen solltest:**

1. In deinem Mietvertrag muss stehen, dass der Mieter die Nebenkosten trägt.
   Steht da nichts, darfst du ihm auch nichts berechnen.
2. Die Abrechnung muss innerhalb von 12 Monaten nach dem Ende des Abrechnungszeitraums
   bei ihm ankommen. Für 2025 also bis zum 31.12.2026. Danach kannst du nichts mehr
   nachfordern – ein Guthaben musst du ihm trotzdem auszahlen.
        """
    )

tab_haus, tab_diese, tab_kosten, tab_zaehler, tab_vz, tab_ergebnis = st.tabs(
    ["1 · Haus (bleibt gleich)", "2 · Diese Abrechnung", "3 · Kosten",
     "4 · Zählerstände", "5 · Vorauszahlungen", "6 · Fertige Abrechnung"]
)

# --------------------------------------------------------------------------
# 1 Haus und Vermieter – die Daten, die jedes Jahr gleich bleiben
# --------------------------------------------------------------------------
with tab_haus:
    st.caption("Diese Angaben trägst du einmal ein. Die App merkt sie sich dauerhaft.")
    links, rechts = st.columns(2)
    with links:
        st.subheader("Du als Vermieter")
        stamm.vermieter_name = st.text_input("Dein Name", stamm.vermieter_name, key="v_name")
        stamm.vermieter_strasse = st.text_input("Straße und Hausnummer", stamm.vermieter_strasse, key="v_str")
        stamm.vermieter_plz_ort = st.text_input("PLZ und Ort", stamm.vermieter_plz_ort, key="v_ort")
        stamm.vermieter_iban = st.text_input(
            "Deine IBAN", stamm.vermieter_iban, key="v_iban",
            help="Steht im PDF, falls dein Mieter etwas nachzahlen muss.")
        if erweitert:
            stamm.vermieter_bank = st.text_input("Bank", stamm.vermieter_bank, key="v_bank")

    with rechts:
        st.subheader("Das Haus")
        stamm.objekt_strasse = st.text_input("Straße und Hausnummer", stamm.objekt_strasse, key="o_str")
        stamm.objekt_plz_ort = st.text_input("PLZ und Ort", stamm.objekt_plz_ort, key="o_ort")
        stamm.mieter_wohnung = st.text_input(
            "Welche Wohnung ist vermietet?", stamm.mieter_wohnung, key="m_wohnung",
            help="Zum Beispiel „Wohnung Obergeschoss“. Steht so im PDF.")
        stamm.grundstuecksflaeche = st.number_input(
            "Grundstück (m²)", min_value=0.0, step=10.0,
            value=float(stamm.grundstuecksflaeche), key="g_flaeche",
            help="Nur zur Information im Kopf der Abrechnung. Für die Verteilung "
                 "der Kosten wird die Wohnfläche benutzt.")

    st.divider()
    st.subheader("Wohnflächen und Wohnungen")
    st.caption("Danach werden die meisten Kosten verteilt. Die Wohnfläche steht im Mietvertrag.")
    g1, g2 = st.columns(2)
    with g1:
        stamm.flaeche_gesamt = st.number_input(
            "Wohnfläche des ganzen Hauses (m²)", min_value=0.0, step=1.0,
            value=float(stamm.flaeche_gesamt), key="f_gesamt",
            help="Deine Wohnung plus die Wohnung des Mieters.")
        stamm.flaeche_mieter = st.number_input(
            "davon Wohnung des Mieters (m²)", min_value=0.0, step=1.0,
            value=float(stamm.flaeche_mieter), key="f_mieter")
        if stamm.flaeche_gesamt and stamm.flaeche_mieter:
            st.caption(f"Anteil des Mieters: "
                       f"**{zahl(stamm.flaeche_mieter / stamm.flaeche_gesamt * 100)} %**")
    with g2:
        stamm.einheiten_gesamt = st.number_input(
            "Wohnungen im Haus", min_value=1.0, step=1.0,
            value=float(stamm.einheiten_gesamt), key="e_gesamt")
        stamm.einheiten_mieter = st.number_input(
            "davon vermietet", min_value=0.0, step=1.0,
            value=float(stamm.einheiten_mieter), key="e_mieter")

# --------------------------------------------------------------------------
# 2 Diese Abrechnung – Art, Zeitraum, Mieter
# --------------------------------------------------------------------------
with tab_diese:
    st.subheader("Was für eine Abrechnung ist das?")
    arten = list(ABRECHNUNGSARTEN)
    stamm.abrechnungsart = st.radio(
        "Art der Abrechnung",
        arten,
        index=arten.index(stamm.abrechnungsart) if stamm.abrechnungsart in arten else 0,
        format_func=lambda k: ABRECHNUNGSARTEN[k],
        horizontal=True,
        key="art",
        label_visibility="collapsed",
        help="Die Auswahl steht auch im PDF über der Abrechnung.")

    if stamm.ist_endabrechnung:
        st.caption(
            "Bei einem Auszug wird nur bis zum Auszugstag abgerechnet. Alle Kosten, die "
            "nicht über einen Zähler laufen, werden dabei tageweise geteilt."
        )
        z1, z2 = st.columns(2)
        with z1:
            stamm.zeitraum_von = datum_feld("Abrechnung ab", stamm.zeitraum_von, "z_von",
                                            "In der Regel der 1. Januar des Auszugsjahres – "
                                            "oder der Einzugstag, wenn er später war.")
        with z2:
            stamm.auszug_am = datum_feld("Auszug am", stamm.auszug_am or stamm.zeitraum_bis, "auszug",
                                         "Letzter Tag des Mietverhältnisses.")
        stamm.zeitraum_bis = stamm.auszug_am
        stamm.nutzung_von, stamm.nutzung_bis = stamm.zeitraum_von, stamm.auszug_am
        st.info("Zum Mietende: Prüfe, ob dein Mieter die Vorauszahlungen wirklich für alle "
                "Monate gezahlt hat – Tab „Vorauszahlungen“.")
    else:
        z1, z2 = st.columns(2)
        with z1:
            stamm.zeitraum_von = datum_feld("Vom", stamm.zeitraum_von, "z_von")
        with z2:
            stamm.zeitraum_bis = datum_feld(
                "Bis", stamm.zeitraum_bis, "z_bis",
                "Normalerweise ein volles Kalenderjahr, also 01.01. bis 31.12.")
        if erweitert:
            st.caption("Nur nötig, wenn der Mieter mitten im Jahr eingezogen ist:")
            m1, m2 = st.columns(2)
            with m1:
                stamm.nutzung_von = datum_feld("Mieter wohnt hier seit", stamm.nutzung_von, "n_von")
            with m2:
                stamm.nutzung_bis = datum_feld("Mieter wohnt hier bis", stamm.nutzung_bis, "n_bis")
        else:
            stamm.nutzung_von, stamm.nutzung_bis = stamm.zeitraum_von, stamm.zeitraum_bis

    st.divider()
    st.subheader("Dein Mieter")
    m1, m2 = st.columns(2)
    with m1:
        stamm.mieter_name = st.text_input("Name des Mieters", stamm.mieter_name, key="m_name")
        if erweitert:
            stamm.anrede = st.text_input(
                "Anrede im Brief", stamm.anrede, key="m_anrede",
                help="Zum Beispiel „Sehr geehrter Herr Müller,“.")
    with m2:
        stamm.personen_gesamt = st.number_input(
            "Personen im Haus insgesamt", min_value=0.0, step=1.0,
            value=float(stamm.personen_gesamt), key="p_gesamt",
            help="Alle Bewohner zusammen, deine Familie mitgezählt.")
        stamm.personen_mieter = st.number_input(
            "davon beim Mieter", min_value=0.0, step=1.0,
            value=float(stamm.personen_mieter), key="p_mieter")

    if erweitert:
        st.divider()
        st.subheader("Anschreiben")
        a1, a2, a3 = st.columns(3)
        with a1:
            stamm.ort = st.text_input("Ort für die Datumszeile", stamm.ort, key="s_ort")
        with a2:
            stamm.datum = datum_feld("Datum der Abrechnung", stamm.datum, "s_datum")
        with a3:
            stamm.zahlungsfrist_tage = int(st.number_input(
                "Zahlungsfrist (Tage)", min_value=0, max_value=90, step=1,
                value=int(stamm.zahlungsfrist_tage), key="s_frist"))

# --------------------------------------------------------------------------
# 3 Kosten
# --------------------------------------------------------------------------
with tab_kosten:
    st.subheader("Was hat das Haus in diesem Zeitraum gekostet?")
    st.caption(
        "Trag pro Zeile ein, was **für das ganze Haus** angefallen ist – die App rechnet "
        "aus, welcher Anteil auf den Mieter entfällt. Zeilen, die es bei dir nicht gibt, "
        "einfach links abwählen. Eigene Zeilen unten anfügen."
    )

    bearbeitet = st.data_editor(
        positionen_als_df(st.session_state.positionen),
        key="kosten_editor",
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        column_order=SPALTEN_ERWEITERT if erweitert else SPALTEN_EINFACH,
        column_config={
            SP_AKTIV: st.column_config.CheckboxColumn(width="small", default=True),
            SP_NAME: st.column_config.TextColumn(width="medium", required=True),
            SP_BETRAG: st.column_config.NumberColumn(format="%.2f", min_value=0.0, step=10.0),
            SP_VERTEILUNG: st.column_config.SelectboxColumn(
                options=SCHLUESSEL_LABELS, default=SCHLUESSEL["flaeche"], width="medium",
                help="Wie sollen die Kosten aufgeteilt werden? Nach Wohnfläche ist der "
                     "Normalfall. „Nach Zählerstand“ nur, wenn es einen eigenen Zähler "
                     "für die Wohnung gibt. „Nur der Mieter“ heißt: die Kosten trägt er allein."),
            SP_LOHN: st.column_config.NumberColumn(
                format="%.2f", min_value=0.0,
                help="Der Lohnanteil auf der Rechnung (z. B. Gärtner, Schornsteinfeger). "
                     "Dein Mieter kann ihn von der Steuer absetzen; die App bescheinigt ihn im PDF."),
            SP_ZEIT: st.column_config.CheckboxColumn(
                width="small", default=True,
                help="Bei Ein- oder Auszug mitten im Zeitraum nur für die Tage abrechnen, "
                     "die der Mieter da war."),
            SP_BELEG: st.column_config.TextColumn(width="large"),
        },
    )
    st.session_state.positionen = df_als_positionen(bearbeitet, st.session_state.positionen)

    summe = sum(p.betrag for p in st.session_state.positionen if p.aktiv)
    st.info(f"Kosten des Hauses insgesamt: **{eur(summe)} €**")

    with st.expander("Was darfst du überhaupt abrechnen?"):
        st.markdown(
            """
**Ja:** laufende Kosten, die jedes Jahr wieder anfallen – Grundsteuer, Wasser, Abwasser,
Müll, Heizung, Schornsteinfeger, Gebäude- und Haftpflichtversicherung, Allgemeinstrom,
Gartenpflege, Straßenreinigung, Winterdienst, Hausmeisterlohn.

**Nein:** alles, was das Haus in Ordnung hält oder deine eigene Verwaltung betrifft –
Reparaturen, neue Fenster, Heizungsaustausch, Rücklagen, Kontogebühren, dein Aufwand
fürs Abrechnen, Rechtsschutz- und Mietausfallversicherung.

**Aufpassen bei Wartungsrechnungen:** Steht auf der Rechnung Wartung *und* Reparatur,
darf nur der Wartungsanteil in die Abrechnung.

**Kabelanschluss** darf seit dem 01.07.2024 nicht mehr über die Nebenkosten abgerechnet
werden.

**Eigene Arbeit** (du mähst den Rasen, räumst Schnee) darfst du ansetzen – mit dem
Betrag, den eine Firma dafür nehmen würde, aber ohne Mehrwertsteuer.
            """
        )

# --------------------------------------------------------------------------
# 4 Zählerstände
# --------------------------------------------------------------------------
with tab_zaehler:
    st.subheader("Zählerstände")
    verbrauchszeilen = [(i, p) for i, p in enumerate(st.session_state.positionen)
                        if p.aktiv and p.schluessel == "verbrauch"]
    if not verbrauchszeilen:
        st.info(
            "Hier erscheint jede Kostenart, die du im Tab „Kosten“ auf **nach Zählerstand** "
            "gestellt hast. Typisch sind Wasser und Abwasser, manchmal auch Strom oder Gas."
        )
    else:
        st.caption(
            "Trag für jeden Zähler den Stand am Anfang und am Ende des Abrechnungszeitraums "
            "ein – den Verbrauch rechnet die App aus. **Hauptzähler** ist der Zähler fürs "
            "ganze Haus, dazu die Zähler der beiden Wohnungen."
        )
        st.radio(
            "Der Hauptzähler zeigt mehr an als die Wohnungszähler zusammen. Wie soll diese "
            "Differenz verteilt werden?",
            list(DIFFERENZ_VERTEILUNG),
            index=list(DIFFERENZ_VERTEILUNG).index(stamm.zaehlerdifferenz)
            if stamm.zaehlerdifferenz in DIFFERENZ_VERTEILUNG else 0,
            format_func=lambda k: DIFFERENZ_VERTEILUNG[k],
            horizontal=True,
            key="differenz_art",
            help="Die Differenz entsteht durch Messtoleranz, den Gartenwasserhahn oder "
                 "undichte Leitungen. Sie darf nicht allein dem Mieter angelastet werden. "
                 "Ohne besondere Vereinbarung im Mietvertrag ist die Wohnfläche der "
                 "gesetzliche Maßstab (§ 556a BGB); nach gemessenem Verbrauch ist ebenfalls "
                 "üblich. Trägst du deinen eigenen Zähler nicht ein, bleibt die ganze "
                 "Differenz bei dir.")
        stamm.zaehlerdifferenz = st.session_state["differenz_art"]

    for i, p in verbrauchszeilen:
        with st.container(border=True):
            kopf, einheit_spalte = st.columns([3, 1])
            kopf.markdown(f"**{p.bezeichnung}**")
            p.einheit = einheit_spalte.text_input(
                "Einheit", p.einheit or "m³", key=f"zae{i}_einheit",
                help="Was zählt der Zähler? Bei Wasser m³, bei Strom kWh.")

            haus, wohnung, eigen = st.columns(3)
            with haus:
                st.markdown("**Hauptzähler (ganzes Haus)**")
                p.zaehler_haus_alt = st.number_input(
                    "Stand am Anfang", min_value=0.0, step=1.0,
                    value=float(p.zaehler_haus_alt), key=f"zae{i}_haus_alt")
                p.zaehler_haus_neu = st.number_input(
                    "Stand am Ende", min_value=0.0, step=1.0,
                    value=float(p.zaehler_haus_neu), key=f"zae{i}_haus_neu")
            with wohnung:
                st.markdown("**Wohnung des Mieters**")
                p.zaehler_mieter_alt = st.number_input(
                    "Stand am Anfang ", min_value=0.0, step=1.0,
                    value=float(p.zaehler_mieter_alt), key=f"zae{i}_m_alt")
                p.zaehler_mieter_neu = st.number_input(
                    "Stand am Ende ", min_value=0.0, step=1.0,
                    value=float(p.zaehler_mieter_neu), key=f"zae{i}_m_neu")
            with eigen:
                st.markdown("**Deine eigene Wohnung**")
                p.zaehler_eigen_alt = st.number_input(
                    "Stand am Anfang  ", min_value=0.0, step=1.0,
                    value=float(p.zaehler_eigen_alt), key=f"zae{i}_e_alt")
                p.zaehler_eigen_neu = st.number_input(
                    "Stand am Ende  ", min_value=0.0, step=1.0,
                    value=float(p.zaehler_eigen_neu), key=f"zae{i}_e_neu")

            with st.expander("Kein Zähler vorhanden? Verbrauch direkt eintragen"):
                d1, d2, d3 = st.columns(3)
                p.verbrauch_gesamt = d1.number_input(
                    "Verbrauch ganzes Haus", min_value=0.0, step=1.0,
                    value=float(p.verbrauch_gesamt), key=f"zae{i}_v_haus",
                    help="Steht auf der Jahresrechnung des Versorgers.")
                p.verbrauch_mieter = d2.number_input(
                    "Verbrauch Mieterwohnung", min_value=0.0, step=1.0,
                    value=float(p.verbrauch_mieter), key=f"zae{i}_v_mieter")
                p.verbrauch_eigen_direkt = d3.number_input(
                    "Verbrauch deine Wohnung", min_value=0.0, step=1.0,
                    value=float(p.verbrauch_eigen_direkt), key=f"zae{i}_v_eigen")
                st.caption("Diese Felder gelten nur, wenn oben keine Zählerstände stehen.")

            if p.verbrauch_haus > 0:
                aufteilung = verbrauchsaufteilung(p, stamm)
                anteil = aufteilung.menge_mieter / p.verbrauch_haus * 100
                einheit = p.einheit
                if aufteilung.differenz > 0:
                    st.success(
                        f"Hauptzähler **{menge(p.verbrauch_haus)} {einheit}** · "
                        f"Mieter **{menge(aufteilung.mieter_verbrauch)}** · "
                        f"du **{menge(aufteilung.eigen_verbrauch)}** · "
                        f"Differenz **{menge(aufteilung.differenz)}**, davon "
                        f"{menge(aufteilung.differenz_mieter)} für den Mieter "
                        f"({aufteilung.differenz_text}) → angerechnet "
                        f"**{menge(aufteilung.menge_mieter)} {einheit}** = **{zahl(anteil)} %**"
                    )
                else:
                    st.success(
                        f"Hauptzähler **{menge(p.verbrauch_haus)} {einheit}**, davon Mieter "
                        f"**{menge(aufteilung.menge_mieter)} {einheit}** = **{zahl(anteil)} %**"
                    )
                    if aufteilung.eigen_verbrauch <= 0:
                        st.caption("Trag auch den Zähler deiner eigenen Wohnung ein – sonst "
                                   "trägst du die gesamte Differenz zum Hauptzähler allein.")
            else:
                st.warning("Noch kein Verbrauch erkennbar – bitte die Zählerstände eintragen.")

# --------------------------------------------------------------------------
# 5 Vorauszahlungen
# --------------------------------------------------------------------------
with tab_vz:
    st.subheader("Was hat dein Mieter schon gezahlt?")
    st.caption(
        "Die monatliche Nebenkostenvorauszahlung aus dem Mietvertrag – der Betrag, den "
        "er zusätzlich zur Kaltmiete überweist."
    )
    v1, v2 = st.columns(2)
    with v1:
        stamm.vorauszahlung_monatlich = st.number_input(
            "Vorauszahlung pro Monat (€)", min_value=0.0, step=10.0,
            value=float(stamm.vorauszahlung_monatlich), key="vz_monat")
        stamm.vorauszahlung_monate = int(st.number_input(
            "Für wie viele Monate?", min_value=0, max_value=12, step=1,
            value=int(stamm.vorauszahlung_monate), key="vz_monate"))
        st.info(f"Zusammen: **{eur(stamm.vorauszahlung_monatlich * stamm.vorauszahlung_monate)} €**")
    with v2:
        abweichend = st.checkbox(
            "Er hat tatsächlich etwas anderes gezahlt", key="vz_abweichend",
            value=stamm.vorauszahlung_manuell is not None,
            help="Zum Beispiel, wenn sich die Vorauszahlung im Jahr geändert hat oder "
                 "eine Zahlung ausgefallen ist.")
        if abweichend:
            stamm.vorauszahlung_manuell = st.number_input(
                "Tatsächlich gezahlt (€)", min_value=0.0, step=10.0,
                value=float(stamm.vorauszahlung_manuell or 0.0), key="vz_manuell")
        else:
            stamm.vorauszahlung_manuell = None

    st.divider()
    st.subheader("Heizt du mit Gas oder Öl?")
    st.caption(
        "Dann trägst du seit 2023 einen Teil der CO2-Abgabe selbst – je schlechter das "
        "Haus gedämmt ist, desto mehr. Den Betrag findest du in der Jahresrechnung deines "
        "Gas- oder Öllieferanten (Stichwort „CO2-Kosten“ oder „CO2-Kostenaufteilung“). "
        "Steht dort nichts, frag beim Versorger nach. Bei Fernwärme oder Wärmepumpe: 0 lassen."
    )
    c1, c2 = st.columns(2)
    with c1:
        stamm.co2_abzug = st.number_input(
            "Dein Anteil an den CO2-Kosten (€)", min_value=0.0, step=1.0,
            value=float(stamm.co2_abzug), key="co2",
            help="Wird vom Anteil des Mieters abgezogen.")
    with c2:
        stamm.anpassung_vorschlagen = st.checkbox(
            "Im PDF ankündigen, dass die Vorauszahlung angepasst wird",
            value=stamm.anpassung_vorschlagen, key="anpassung",
            help="Sinnvoll, wenn die bisherige Vorauszahlung deutlich zu niedrig oder "
                 "zu hoch war. Die App schlägt einen Betrag vor. Bei einer Abrechnung "
                 "zum Mietende brauchst du das nicht.")

# --------------------------------------------------------------------------
# 6 Ergebnis
# --------------------------------------------------------------------------
with tab_ergebnis:
    ergebnis = berechne(stamm, st.session_state.positionen)
    st.caption(f"{stamm.bezeichnung_abrechnung} für "
               f"{stamm.mieter_name or 'deinen Mieter'} · "
               f"{_fmt(stamm.zeitraum_von)} bis {_fmt(stamm.zeitraum_bis)}")

    for fehler in ergebnis.fehler:
        st.error(fehler)
    for warnung in ergebnis.warnungen:
        st.warning(warnung)

    k1, k2, k3 = st.columns(3)
    k1.metric("Anteil des Mieters", f"{eur(ergebnis.umlage)} €")
    k2.metric("Schon gezahlt", f"{eur(ergebnis.vorauszahlungen)} €")
    k3.metric("Nachzahlung" if ergebnis.ist_nachzahlung else "Guthaben",
              f"{eur(ergebnis.betrag_absolut)} €")

    if ergebnis.zeilen:
        if ergebnis.betrag_absolut < 0.01:
            st.success("Die Vorauszahlungen decken die Kosten genau – niemand zahlt etwas nach.")
        elif ergebnis.ist_nachzahlung:
            st.success(f"Dein Mieter muss **{eur(ergebnis.betrag_absolut)} €** nachzahlen.")
        else:
            st.success(f"Du musst deinem Mieter **{eur(ergebnis.betrag_absolut)} €** erstatten.")

        st.dataframe(
            pd.DataFrame([{
                "Kostenart": z.bezeichnung,
                "Kosten Haus (€)": z.gesamtkosten,
                "So wurde verteilt": z.schluessel_text,
                "Anteil Mieter (€)": z.anteil,
            } for z in ergebnis.zeilen]),
            width="stretch", hide_index=True,
            column_config={
                "Kosten Haus (€)": st.column_config.NumberColumn(format="%.2f"),
                "Anteil Mieter (€)": st.column_config.NumberColumn(format="%.2f"),
            },
        )
    else:
        st.info("Trag im Tab „Kosten“ ein, was das Haus gekostet hat.")

    e1, e2 = st.columns(2)
    with e1:
        if ergebnis.arbeitskosten_mieter:
            st.caption(f"Für die Steuererklärung deines Mieters: **{eur(ergebnis.arbeitskosten_mieter)} €** "
                       "Lohnkosten stehen im PDF.")
        if ergebnis.tage_nutzung and ergebnis.tage_nutzung < ergebnis.tage_zeitraum:
            st.caption(f"Der Mieter hat {ergebnis.tage_nutzung} von {ergebnis.tage_zeitraum} Tagen "
                       "hier gewohnt – so viel wurde berechnet.")
    with e2:
        if ergebnis.empfehlung_vorauszahlung and not stamm.ist_endabrechnung:
            st.caption(f"Passende Vorauszahlung ab jetzt: **{eur(ergebnis.empfehlung_vorauszahlung)} €** "
                       "im Monat.")

    st.divider()
    if ergebnis.fehler:
        st.error("Bitte die roten Punkte oben korrigieren, dann gibt es das PDF.")
    elif not ergebnis.zeilen:
        st.info("Ohne Kosten gibt es nichts abzurechnen.")
    else:
        if st.download_button(
            "📄 Abrechnung als PDF speichern",
            data=erzeuge_pdf(stamm, ergebnis),
            file_name=dateiname(stamm),
            mime="application/pdf",
            type="primary",
            width="stretch",
        ):
            try:
                abgelegt = speicher.archivieren(stamm, st.session_state.positionen)
                st.success(f"Abrechnung abgelegt unter `{abgelegt.name}` – "
                           "du findest sie in der Seitenleiste wieder.")
            except OSError as fehler:
                st.warning(f"Ablegen nicht möglich: {fehler}")
        st.caption(
            "Vor dem Aushändigen kurz prüfen: Namen, Zeitraum, Beträge, IBAN. "
            "Das PDF ausdrucken, unterschreiben und dem Mieter geben – "
            "am besten mit Kopien der Rechnungen."
        )

# Nach jeder Eingabe alles dauerhaft sichern.
sichern()
