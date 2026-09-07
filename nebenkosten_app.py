"""Nebenkostenabrechnung – Streamlit-App.

Start:  streamlit run nebenkosten_app.py
"""

from __future__ import annotations

import json
from datetime import date

import pandas as pd
import streamlit as st

from nebenkosten.berechnung import (
    berechne, co2_vermieteranteil, eur, menge, parse_datum, verbrauchsaufteilung,
    warmwasser_kwh, zaehlerquelle, zahl,
)
from nebenkosten import speicher
from nebenkosten.modell import (
    ABRECHNUNGSARTEN, DIFFERENZ_VERTEILUNG, KATEGORIEN, PARTEIEN, SCHLUESSEL,
    ZAEHLER_GRUNDLAGE, ZWISCHEN_ANLAESSE, Position, Stammdaten, Zaehlerstand,
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
SP_GRUND = "Grundkosten (%)"
SP_LOHN = "davon Lohnkosten (€)"
SP_ZEIT = "zeitanteilig"
SP_BELEG = "Welcher Beleg?"

SPALTEN_EINFACH = (SP_AKTIV, SP_NAME, SP_BETRAG, SP_VERTEILUNG, SP_BELEG)
SPALTEN_ERWEITERT = (SP_AKTIV, SP_NAME, SP_BETRAG, SP_VERTEILUNG, SP_GRUND, SP_LOHN,
                     SP_ZEIT, SP_BELEG)

BEHALTEN = {"stamm", "positionen", "erweitert"}


# --------------------------------------------------------------------------
# Zustand
# --------------------------------------------------------------------------
def init_state() -> None:
    ablage_einrichten()

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


def ablage_einrichten() -> None:
    """Falls Zugangsdaten hinterlegt sind, in die Google-Tabelle speichern."""
    if st.session_state.get("_ablage_geprueft"):
        return
    st.session_state["_ablage_geprueft"] = True
    try:
        zugang = st.secrets.get("gcp_json")
        adresse = st.secrets.get("nebenkosten_sheet_url")
    except Exception:  # noqa: BLE001 – ohne secrets.toml wirft st.secrets
        return
    if not zugang or not adresse:
        return
    try:
        from nebenkosten.cloud import TabellenSpeicher

        daten = json.loads(zugang) if isinstance(zugang, str) else dict(zugang)
        speicher.konfiguriere(TabellenSpeicher(str(adresse), daten))
    except Exception as fehler:  # noqa: BLE001 – Netz, Rechte, Tabelle fehlt
        st.session_state["_ablagefehler"] = str(fehler)


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
        SP_GRUND: float(p.grundkosten_anteil),
        SP_LOHN: float(p.arbeitskosten),
        SP_ZEIT: p.zeitanteilig,
        SP_BELEG: p.hinweis,
    } for p in positionen])


def df_als_positionen(df: pd.DataFrame, bestehend: list[Position],
                      kategorie: str = "sonstiges") -> list[Position]:
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
            kategorie=vorgaenger.kategorie if vorgaenger else kategorie,
            betrag=zahlwert(SP_BETRAG),
            schluessel=LABEL_ZU_KEY.get(str(r.get(SP_VERTEILUNG)), "flaeche"),
            einheit=vorgaenger.einheit if vorgaenger else "",
            zaehler=vorgaenger.zaehler if vorgaenger else [],
            zaehler_grundlage=vorgaenger.zaehler_grundlage if vorgaenger else "hauptzaehler",
            zaehler_von=vorgaenger.zaehler_von if vorgaenger else "",
            verbrauch_gesamt=vorgaenger.verbrauch_gesamt if vorgaenger else 0.0,
            verbrauch_mieter=vorgaenger.verbrauch_mieter if vorgaenger else 0.0,
            verbrauch_eigen_direkt=vorgaenger.verbrauch_eigen_direkt if vorgaenger else 0.0,
            grundkosten_anteil=zahlwert(
                SP_GRUND, vorgaenger.grundkosten_anteil if vorgaenger else 0.0),
            arbeitskosten=zahlwert(SP_LOHN, vorgaenger.arbeitskosten if vorgaenger else 0.0),
            zeitanteilig=bool(r.get(SP_ZEIT, vorgaenger.zeitanteilig if vorgaenger else True)),
            aktiv=bool(r.get(SP_AKTIV, True)),
            hinweis=str(r.get(SP_BELEG) or ""),
        ))
    return positionen


ZAE_NAME, ZAE_WER = "Zähler", "Wer"
ZAE_ALT, ZAE_NEU, ZAE_VERBRAUCH = "Stand Anfang", "Stand Ende", "Verbrauch"
PARTEI_LABELS = list(PARTEIEN.values())
LABEL_ZU_PARTEI = {v: k for k, v in PARTEIEN.items()}


def zaehler_als_df(pos: Position) -> pd.DataFrame:
    return pd.DataFrame(
        [{ZAE_NAME: z.name, ZAE_WER: PARTEIEN.get(z.partei, PARTEIEN["mieter"]),
           ZAE_ALT: float(z.alt), ZAE_NEU: float(z.neu), ZAE_VERBRAUCH: z.verbrauch}
         for z in pos.zaehler],
        columns=[ZAE_NAME, ZAE_WER, ZAE_ALT, ZAE_NEU, ZAE_VERBRAUCH])


def df_als_zaehler(df: pd.DataFrame) -> list[Zaehlerstand]:
    staende = []
    for _, r in df.iterrows():
        name = str(r.get(ZAE_NAME) or "").strip()
        if not name:
            continue

        def wert(spalte: str) -> float:
            try:
                roh = r.get(spalte)
                return float(roh) if pd.notna(roh) else 0.0
            except (TypeError, ValueError):
                return 0.0

        staende.append(Zaehlerstand(
            name=name,
            partei=LABEL_ZU_PARTEI.get(str(r.get(ZAE_WER)), "mieter"),
            alt=wert(ZAE_ALT), neu=wert(ZAE_NEU)))
    return staende


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
    handy = st.toggle(
        "📱 Handy-Ansicht", key="handy",
        help="Statt breiter Tabellen einzelne Eingabefelder untereinander – "
             "auf einem kleinen Bildschirm viel einfacher zu tippen.")
    erweitert = st.toggle(
        "Mehr Einstellungen anzeigen", key="erweitert",
        help="Zeigt zusätzliche Felder: Lohnkosten für die Steuererklärung des "
             "Mieters, anteilige Abrechnung bei Ein- oder Auszug, Anschreiben.")

    st.header("Gespeichert wird automatisch")
    stand = speicher.gespeichert_am()
    if st.session_state.get("_ablagefehler"):
        st.warning(f"Google-Tabelle nicht erreichbar, es wird in eine Datei gespeichert: "
                   f"{st.session_state['_ablagefehler']}")
    if st.session_state.get("_speicherfehler"):
        st.error(f"Speichern nicht möglich: {st.session_state['_speicherfehler']}")
    elif stand:
        st.success(f"Zuletzt gespeichert: {stand.strftime('%d.%m.%Y um %H:%M:%S')}")
    else:
        st.info("Wird gespeichert, sobald du etwas eingibst.")

    with st.expander("Wo liegen meine Daten?"):
        st.markdown(f"**Ablage:** {speicher.beschreibung()}")
        st.code(speicher.adresse(), language=None)
        if speicher.beschreibung() == "Datei auf diesem Gerät":
            st.markdown(
                f"Fertige Abrechnungen: `{speicher.ARCHIV}`\n\n"
                "Die Datei kannst du kopieren, mitnehmen und hier wieder einlesen. "
                "Läuft die App in der Cloud, ist sie nach einem Neustart weg – "
                "dann bitte regelmäßig eine Sicherungskopie herunterladen."
            )
        else:
            st.markdown("Fertige Abrechnungen stehen als weitere Zeilen in derselben Tabelle.")
        st.markdown(
            "**Das PDF** landet dort, wo dein Gerät Downloads ablegt – am Rechner im "
            "Ordner Downloads, am Handy unter Dateien / Downloads."
        )

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
                                   format_func=speicher.archivname)
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
            p.verbrauch_gesamt = p.verbrauch_mieter = p.verbrauch_eigen_direkt = 0.0
            for z in p.zaehler:
                # Der Endstand des alten Jahres ist der Anfangsstand des neuen.
                z.alt, z.neu = z.neu, 0.0
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

    if stamm.ist_zwischenabrechnung:
        st.caption(
            "Eine Zwischenabrechnung ist eine Momentaufnahme – zum Beispiel beim Wechsel "
            "des Gasanbieters oder wenn dein Mieter wissen will, ob seine Vorauszahlung "
            "passt. Sie ist rechtlich unverbindlich: Nachzahlen muss er erst nach der "
            "regulären Abrechnung. Die App rechnet den Stand hoch aufs ganze Jahr und "
            "schlägt eine passende Vorauszahlung vor."
        )
        z1, z2 = st.columns(2)
        with z1:
            stamm.zeitraum_von = datum_feld("Zwischenabrechnung ab", stamm.zeitraum_von, "z_von")
        with z2:
            stamm.zeitraum_bis = datum_feld(
                "Stichtag", stamm.zeitraum_bis, "z_bis",
                "Bis zu diesem Tag wird gerechnet – meist der Tag der Zählerablesung.")
        stamm.nutzung_von, stamm.nutzung_bis = stamm.zeitraum_von, stamm.zeitraum_bis
        stamm.anlass = st.text_input(
            "Warum diese Zwischenabrechnung?", stamm.anlass, key="anlass",
            placeholder=ZWISCHEN_ANLAESSE[0],
            help="Steht so im PDF. Üblich: " + ", ".join(ZWISCHEN_ANLAESSE) + ".")
    elif stamm.ist_endabrechnung:
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
            if stamm.ist_verbindlich:
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

    def kategorie_positionen(schluessel: str) -> list[Position]:
        return [p for p in st.session_state.positionen if p.kategorie == schluessel]

    def zusammenfuehren(schluessel: str, neue: list[Position]) -> None:
        """Bearbeitete Zeilen einer Kategorie zurück in die Gesamtliste."""
        zusammen: list[Position] = []
        eingefuegt = False
        for p in st.session_state.positionen:
            if p.kategorie != schluessel:
                zusammen.append(p)
            elif not eingefuegt:
                zusammen.extend(neue)
                eingefuegt = True
        if not eingefuegt:
            zusammen.extend(neue)
        st.session_state.positionen = zusammen

    if handy:
        for schluessel, name in KATEGORIEN.items():
            st.markdown(f"#### {name}")
            gruppe = kategorie_positionen(schluessel)
            for i, p in enumerate(gruppe):
                if not p.aktiv:
                    continue
                p.betrag = st.number_input(
                    f"{p.bezeichnung} (€)", min_value=0.0, step=10.0,
                    value=float(p.betrag), key=f"kos_{schluessel}_{i}_betrag", help=p.hinweis)
            with st.expander(f"Zeilen für „{name}“ ein- und ausschalten"):
                for i, p in enumerate(gruppe):
                    p.aktiv = st.checkbox(p.bezeichnung, value=p.aktiv,
                                          key=f"kos_{schluessel}_{i}_aktiv", help=p.hinweis)
        with st.expander("Wie wird verteilt?"):
            for i, p in enumerate(st.session_state.positionen):
                if not p.aktiv:
                    continue
                gewaehlt = st.selectbox(
                    p.bezeichnung, SCHLUESSEL_LABELS, key=f"kos{i}_schluessel",
                    index=SCHLUESSEL_LABELS.index(SCHLUESSEL.get(p.schluessel,
                                                                 SCHLUESSEL["flaeche"])))
                p.schluessel = LABEL_ZU_KEY.get(gewaehlt, "flaeche")
        if erweitert:
            with st.expander("Grundkosten-Anteil (Heizung, Warmwasser)"):
                for i, p in enumerate(st.session_state.positionen):
                    if not p.aktiv or p.schluessel != "verbrauch":
                        continue
                    p.grundkosten_anteil = st.number_input(
                        f"{p.bezeichnung}: nach Wohnfläche (%)", min_value=0.0, max_value=50.0,
                        step=5.0, value=float(p.grundkosten_anteil), key=f"kos{i}_grund")
            with st.expander("Lohnkosten für die Steuererklärung des Mieters"):
                for i, p in enumerate(st.session_state.positionen):
                    if not p.aktiv or not p.betrag:
                        continue
                    p.arbeitskosten = st.number_input(
                        f"{p.bezeichnung}: davon Lohnkosten (€)", min_value=0.0, step=10.0,
                        value=float(p.arbeitskosten), key=f"kos{i}_lohn")
    else:
        for schluessel, name in KATEGORIEN.items():
            gruppe = kategorie_positionen(schluessel)
            teilsumme = sum(p.betrag for p in gruppe if p.aktiv)
            st.markdown(f"#### {name} · {eur(teilsumme)} €")
            bearbeitet = st.data_editor(
                positionen_als_df(gruppe),
                key=f"kosten_editor_{schluessel}",
                num_rows="dynamic",
                width="stretch",
                hide_index=True,
                column_order=SPALTEN_ERWEITERT if erweitert else SPALTEN_EINFACH,
                column_config={
                    SP_AKTIV: st.column_config.CheckboxColumn(width="small", default=True),
                    SP_NAME: st.column_config.TextColumn(width="medium", required=True),
                    SP_BETRAG: st.column_config.NumberColumn(format="%.2f", min_value=0.0,
                                                            step=10.0),
                    SP_VERTEILUNG: st.column_config.SelectboxColumn(
                        options=SCHLUESSEL_LABELS, default=SCHLUESSEL["flaeche"], width="medium",
                        help="Nach Wohnfläche ist der Normalfall. „Nach Zählerstand“ nur, wenn "
                             "es einen eigenen Zähler gibt. „Nur der Mieter“ bzw. „nur ich "
                             "selbst“ für Kosten, die eine Seite allein trägt."),
                    SP_GRUND: st.column_config.NumberColumn(
                        format="%.0f", min_value=0.0, max_value=50.0, step=5.0,
                        help="Nur bei Verteilung nach Zählerstand: Anteil, der nach Wohnfläche "
                             "verteilt wird. Bei Heizung und Warmwasser sind 30 % üblich."),
                    SP_LOHN: st.column_config.NumberColumn(
                        format="%.2f", min_value=0.0,
                        help="Lohnanteil auf der Rechnung – dein Mieter kann ihn von der "
                             "Steuer absetzen; die App bescheinigt ihn im PDF."),
                    SP_ZEIT: st.column_config.CheckboxColumn(
                        width="small", default=True,
                        help="Bei Ein- oder Auszug mitten im Zeitraum nur für die Tage "
                             "abrechnen, die der Mieter da war."),
                    SP_BELEG: st.column_config.TextColumn(width="large"),
                },
            )
            zusammenfuehren(schluessel, df_als_positionen(bearbeitet, gruppe, schluessel))

    summe = sum(p.betrag for p in st.session_state.positionen if p.aktiv)
    st.info(f"Kosten des Hauses insgesamt: **{eur(summe)} €**")

    with st.expander("🔥 Gasrechnung auf Heizung und Warmwasser aufteilen"):
        st.caption(
            "Wenn deine Wärmemengenzähler nur die Heizung messen, steckt im Gas auch das "
            "Warmwasser. Die Heizkostenverordnung (§ 9) rechnet den Warmwasseranteil so heraus: "
            "**Q = 2,5 × Warmwassermenge in m³ × (Warmwassertemperatur − 10 °C)**, plus Zuschlag "
            "für die Verluste der Anlage."
        )
        w1, w2, w3 = st.columns(3)
        ww_menge = w1.number_input("Warmwasser im ganzen Haus (m³)", min_value=0.0, step=1.0,
                                   value=float(st.session_state.get("ww_menge", 0.0)),
                                   key="ww_menge")
        ww_temp = w2.number_input(
            "Warmwassertemperatur (°C)", min_value=20.0, max_value=80.0, step=5.0,
            value=float(st.session_state.get("ww_temp", 60.0)), key="ww_temp",
            help="Ohne gemessene Temperatur schreibt die Heizkostenverordnung 60 °C vor. "
                 "Einen niedrigeren Wert darfst du nur ansetzen, wenn du ihn wirklich misst.")
        ww_nutzung = w3.number_input(
            "Zuschlag für Anlagenverluste", min_value=1.0, max_value=1.5, step=0.01,
            value=float(st.session_state.get("ww_nutzung", 1.11)), key="ww_nutzung",
            help="1,11 entspricht einem Nutzungsgrad von 90 % – der übliche Wert.")

        g1, g2 = st.columns(2)
        gas_kwh = g1.number_input("Gasverbrauch im Zeitraum (kWh)", min_value=0.0, step=100.0,
                                  value=float(st.session_state.get("gas_kwh", 0.0)), key="gas_kwh")
        gas_kosten = g2.number_input("Gaskosten im Zeitraum (€)", min_value=0.0, step=10.0,
                                     value=float(st.session_state.get("gas_kosten", 0.0)),
                                     key="gas_kosten")

        if ww_menge > 0 and gas_kwh > 0 and gas_kosten > 0:
            ww_bedarf = warmwasser_kwh(ww_menge, ww_temp, ww_nutzung)
            anteil = min(ww_bedarf / gas_kwh, 1.0)
            kosten_ww = round(gas_kosten * anteil, 2)
            kosten_heizung = round(gas_kosten - kosten_ww, 2)
            st.success(
                f"Warmwasser braucht **{menge(round(ww_bedarf))} kWh** = **{zahl(anteil * 100)} %** "
                f"des Gases → **{eur(kosten_ww)} €** für Warmwasser, "
                f"**{eur(kosten_heizung)} €** für die Heizung."
            )
            if st.button("Diese Beträge in die Kostenzeilen übernehmen", key="ww_uebernehmen"):
                getroffen = []
                for p in st.session_state.positionen:
                    name = p.bezeichnung.lower()
                    if "warmwasser" in name:
                        p.betrag, p.aktiv = kosten_ww, True
                        getroffen.append(p.bezeichnung)
                    elif "heizung" in name:
                        p.betrag, p.aktiv = kosten_heizung, True
                        getroffen.append(p.bezeichnung)
                if getroffen:
                    sichern()
                    neu_zeichnen()
                else:
                    st.warning("Keine Zeile mit „Heizung“ oder „Warmwasser“ gefunden.")
        else:
            st.caption("Trag Warmwassermenge, Gasverbrauch und Gaskosten ein, dann rechnet die "
                       "App die Aufteilung aus.")

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
            "gestellt hast. Typisch sind Wasser, Abwasser, Heizung und Warmwasser."
        )
    else:
        st.caption(
            "Zu jeder Kostenart gehören beliebig viele Zähler – Hauptzähler, die Zähler "
            "deines Mieters und deine eigenen. Trag Anfangs- und Endstand ein, den "
            "Verbrauch rechnet die App. Zeilen lassen sich ändern, löschen und unten "
            "ergänzen."
        )
        st.radio(
            "Der Hauptzähler zeigt mehr an als die Wohnungszähler zusammen. Wie soll diese "
            "Differenz auf euch beide verteilt werden?",
            list(DIFFERENZ_VERTEILUNG),
            index=list(DIFFERENZ_VERTEILUNG).index(stamm.zaehlerdifferenz)
            if stamm.zaehlerdifferenz in DIFFERENZ_VERTEILUNG else 0,
            format_func=lambda k: DIFFERENZ_VERTEILUNG[k],
            horizontal=True,
            key="differenz_art",
            help="Die Differenz entsteht durch Messtoleranz, den Gartenwasserhahn oder "
                 "undichte Leitungen – und dadurch, dass kein Zähler exakt misst. "
                 "„Nach gemessenem Verbrauch“ heißt: Wer mehr verbraucht hat, trägt auch "
                 "mehr von der Differenz. „Nach Wohnfläche“ ist der gesetzliche "
                 "Ersatzmaßstab (§ 556a BGB).")
        stamm.zaehlerdifferenz = st.session_state["differenz_art"]

    with st.expander("Wie teile ich die Gasrechnung auf Heizung und Warmwasser auf?"):
        st.markdown(
            """
Wenn deine Wärmemengenzähler nur die Heizung messen, steckt im Gasverbrauch auch die
Wärme fürs Warmwasser. Diesen Teil rechnet man üblicherweise so heraus
(Faustformel aus der Heizkostenverordnung):

**Wärme fürs Warmwasser in kWh = 2,5 × Warmwassermenge in m³ × (Warmwassertemperatur in °C − 10)**

Beispiel: 55 m³ Warmwasser bei 60 °C → 2,5 × 55 × 50 = **6.875 kWh**.

Bei einem Gaspreis von z. B. 0,12 €/kWh sind das rund 825 € der Gasrechnung. Diesen
Betrag trägst du in die Zeile **Warmwasser (Gas)** ein, den Rest der Gasrechnung in
**Heizung (Gas)**. So wird der Warmwasseranteil nach den Warmwasserzählern verteilt
und der Heizungsanteil nach den Wärmemengenzählern.
            """
        )

    namen_aller = [p.bezeichnung for p in st.session_state.positionen
                   if p.aktiv and p.schluessel == "verbrauch"]

    for i, p in verbrauchszeilen:
        with st.container(border=True):
            k1, k2, k3 = st.columns([2, 1, 2])
            k1.markdown(f"### {p.bezeichnung}")
            p.einheit = k2.text_input(
                "Einheit", p.einheit or "m³", key=f"zae{i}_einheit",
                help="Was misst der Zähler? Wasser m³, Wärmemenge kWh, Gas m³.")
            andere = [n for n in namen_aller if n != p.bezeichnung]
            auswahl = ["(eigene Zähler)"] + andere
            vorgabe = p.zaehler_von if p.zaehler_von in andere else "(eigene Zähler)"
            gewaehlt = k3.selectbox(
                "Zähler", auswahl, index=auswahl.index(vorgabe), key=f"zae{i}_von",
                help="Abwasser wird meist nach der Frischwassermenge abgerechnet – dann "
                     "hier „Wasser“ auswählen, statt dieselben Stände noch einmal einzutippen.")
            p.zaehler_von = "" if gewaehlt == "(eigene Zähler)" else gewaehlt

            if p.zaehler_von:
                st.info(f"Es werden die Zählerstände von **{p.zaehler_von}** benutzt.")
            else:
                p.zaehler_grundlage = st.radio(
                    "Woraus ergibt sich der Anteil des Mieters?",
                    list(ZAEHLER_GRUNDLAGE),
                    index=list(ZAEHLER_GRUNDLAGE).index(p.zaehler_grundlage)
                    if p.zaehler_grundlage in ZAEHLER_GRUNDLAGE else 0,
                    format_func=lambda k: ZAEHLER_GRUNDLAGE[k],
                    horizontal=True,
                    key=f"zae{i}_grundlage",
                    help="**Anteil am Hauptzähler**: Die Rechnung hängt am Hauptzähler "
                         "(Wasser). Was der Hauptzähler mehr anzeigt als die Unterzähler, "
                         "wird verteilt. **Nur die Unterzähler**: Die Zähler messen etwas "
                         "anderes als die Rechnung – Wärmemenge in kWh bei einer Gasrechnung. "
                         "Dann zählt nur das Verhältnis der Unterzähler zueinander, und ein "
                         "Hauptzähler steht bloß zur Information dabei.")

                if handy:
                    for nr, z in enumerate(p.zaehler):
                        st.markdown(f"**{z.name or 'Zähler'}** · {PARTEIEN.get(z.partei, '')}")
                        sa, se = st.columns(2)
                        z.alt = sa.number_input(
                            "Stand Anfang", min_value=0.0, step=1.0, value=float(z.alt),
                            key=f"zae{i}_{nr}_alt", label_visibility="collapsed",
                            placeholder="Anfang")
                        z.neu = se.number_input(
                            "Stand Ende", min_value=0.0, step=1.0, value=float(z.neu),
                            key=f"zae{i}_{nr}_neu", label_visibility="collapsed",
                            placeholder="Ende")
                        st.caption(f"Anfang → Ende, Verbrauch {menge(z.verbrauch)} {p.einheit}")
                    with st.expander("Zähler umbenennen, zuordnen oder löschen"):
                        for nr, z in enumerate(p.zaehler):
                            z.name = st.text_input("Name", z.name, key=f"zae{i}_{nr}_name")
                            z.partei = LABEL_ZU_PARTEI.get(st.selectbox(
                                "Wem gehört der Zähler?", PARTEI_LABELS,
                                index=PARTEI_LABELS.index(PARTEIEN.get(z.partei,
                                                                       PARTEIEN["mieter"])),
                                key=f"zae{i}_{nr}_partei"), "mieter")
                            if st.button("Diesen Zähler löschen", key=f"zae{i}_{nr}_weg"):
                                p.zaehler.pop(nr)
                                neu_zeichnen()
                            st.divider()
                        if st.button("Zähler hinzufügen", key=f"zae{i}_plus"):
                            p.zaehler.append(Zaehlerstand("Neuer Zähler", "mieter"))
                            neu_zeichnen()
                else:
                    bearbeitet_zae = st.data_editor(
                        zaehler_als_df(p),
                        key=f"zae{i}_tabelle",
                        num_rows="dynamic",
                        width="stretch",
                        hide_index=True,
                        disabled=[ZAE_VERBRAUCH],
                        column_config={
                            ZAE_NAME: st.column_config.TextColumn(width="medium", required=True),
                            ZAE_WER: st.column_config.SelectboxColumn(
                                options=PARTEI_LABELS, default=PARTEIEN["mieter"], width="medium",
                        help="„Gemeinsam genutzt“ ist für Zähler, die keiner Wohnung allein "
                             "gehören – etwa die Außenzapfstelle. Die Menge wird dann nach "
                             "demselben Maßstab geteilt wie die Differenz. Nutzt den "
                             "Außenhahn nur eine Seite, gehört der Zähler zu dieser Wohnung."),
                            ZAE_ALT: st.column_config.NumberColumn(format="%.3f", min_value=0.0),
                            ZAE_NEU: st.column_config.NumberColumn(format="%.3f", min_value=0.0),
                            ZAE_VERBRAUCH: st.column_config.NumberColumn(
                                format="%.3f", help="Rechnet die App aus: Ende minus Anfang."),
                        },
                    )
                    p.zaehler = df_als_zaehler(bearbeitet_zae)

                if not p.zaehler:
                    with st.expander("Kein Zähler vorhanden? Mengen direkt eintragen"):
                        d1, d2, d3 = st.columns(3)
                        p.verbrauch_gesamt = d1.number_input(
                            "ganzes Haus", min_value=0.0, step=1.0,
                            value=float(p.verbrauch_gesamt), key=f"zae{i}_v_haus",
                            help="Steht auf der Jahresrechnung des Versorgers.")
                        p.verbrauch_mieter = d2.number_input(
                            "Mieterwohnung", min_value=0.0, step=1.0,
                            value=float(p.verbrauch_mieter), key=f"zae{i}_v_mieter")
                        p.verbrauch_eigen_direkt = d3.number_input(
                            "deine Wohnung", min_value=0.0, step=1.0,
                            value=float(p.verbrauch_eigen_direkt), key=f"zae{i}_v_eigen")

            aufteilung = verbrauchsaufteilung(p, stamm, st.session_state.positionen)
            einheit = aufteilung.einheit
            if aufteilung.basis > 0:
                zeilen = []
                if aufteilung.haus_verbrauch:
                    if aufteilung.grundlage != "unterzaehler":
                        zeilen.append(f"Hauptzähler **{menge(aufteilung.haus_verbrauch)} "
                                      f"{einheit}**")
                    else:
                        zeilen.append("Hauptzähler (nur Information) "
                                      f"**{menge(aufteilung.haus_verbrauch)}**")
                zeilen.append(f"Mieter **{menge(aufteilung.mieter_verbrauch)}**")
                zeilen.append(f"du **{menge(aufteilung.vermieter_verbrauch)}**")
                if aufteilung.mit_gemeinsam:
                    zeilen.append(f"gemeinsam **{menge(aufteilung.gemeinsam_verbrauch)}**, "
                                  f"davon {menge(aufteilung.gemeinsam_anteil)} für den Mieter")
                if aufteilung.mit_differenz:
                    zeilen.append(
                        f"Differenz **{menge(aufteilung.differenz)}**, davon "
                        f"{menge(aufteilung.differenz_mieter)} für den Mieter "
                        f"({aufteilung.differenz_text})")
                st.success(" · ".join(zeilen) + f" → angerechnet für den Mieter "
                           f"**{menge(aufteilung.menge_mieter)} {einheit}** von "
                           f"**{menge(aufteilung.basis)} {einheit}** = "
                           f"**{zahl(aufteilung.quote * 100)} %**")
                if (aufteilung.grundlage != "unterzaehler"
                        and aufteilung.vermieter_verbrauch <= 0
                        and aufteilung.haus_verbrauch > 0):
                    st.caption("Trag auch deine eigenen Zähler ein – sonst trägst du die "
                               "gesamte Differenz zum Hauptzähler allein.")
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
        co2_kg = st.number_input(
            "CO2-Ausstoß im Abrechnungszeitraum (kg)", min_value=0.0, step=10.0,
            value=float(st.session_state.get("co2_kg", 0.0)), key="co2_kg",
            help="Steht seit 2023 auf jeder Gas- und Ölrechnung. Wenn nicht: beim Versorger "
                 "anfordern – er muss die Angabe machen.")
        co2_kosten = st.number_input(
            "darin enthaltene CO2-Kosten (€)", min_value=0.0, step=1.0,
            value=float(st.session_state.get("co2_kosten", 0.0)), key="co2_kosten",
            help="Ebenfalls auf der Rechnung, oft als „CO2-Preis“ oder „BEHG“ ausgewiesen.")
    with c2:
        if co2_kg > 0 and stamm.flaeche_gesamt > 0:
            prozent, erklaerung = co2_vermieteranteil(co2_kg, stamm.flaeche_gesamt)
            dein_anteil = round(co2_kosten * prozent / 100, 2)
            st.success(f"{erklaerung}\n\nDein Anteil: **{eur(dein_anteil)} €** von "
                       f"{eur(co2_kosten)} €")
            if st.button("Diesen Betrag übernehmen", key="co2_uebernehmen"):
                stamm.co2_abzug = dein_anteil
                sichern()
                neu_zeichnen()
        else:
            st.caption("Trag den CO2-Ausstoß ein, dann rechnet die App deinen Pflichtanteil "
                       "nach dem Stufenmodell aus. Je schlechter das Haus gedämmt ist, desto "
                       "mehr trägst du.")
        stamm.co2_abzug = st.number_input(
            "Dein Anteil an den CO2-Kosten (€)", min_value=0.0, step=1.0,
            value=float(stamm.co2_abzug), key="co2",
            help="Wird vom Anteil des Mieters abgezogen.")

    st.divider()
    st.subheader("Vorauszahlung anpassen")
    a1, a2 = st.columns(2)
    with a1:
        if stamm.ist_zwischenabrechnung:
            st.info("Bei einer Zwischenabrechnung steht im PDF nur ein Vorschlag für die "
                    "künftige Vorauszahlung – ändern darfst du sie erst nach der "
                    "regulären Abrechnung.")
        stamm.anpassung_vorschlagen = st.checkbox(
            "Im PDF ankündigen, dass die Vorauszahlung angepasst wird",
            value=stamm.anpassung_vorschlagen, key="anpassung",
            help="Sinnvoll, wenn die bisherige Vorauszahlung deutlich zu niedrig oder "
                 "zu hoch war. Die App schlägt einen Betrag vor.")
    with a2:
        stamm.eigene_abrechnung = st.checkbox(
            "Auch eine Aufstellung für die eigene Wohnung erstellen",
            value=stamm.eigene_abrechnung, key="eigene",
            help="Dieselbe Rechnung aus deiner Sicht – für die Unterlagen und die "
                 "Steuererklärung (Anlage V). Nicht für den Mieter gedacht.")

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
    if stamm.ist_zwischenabrechnung:
        k3.metric("Fehlt noch" if ergebnis.ist_nachzahlung else "Zu viel gezahlt",
                  f"{eur(ergebnis.betrag_absolut)} €")
    else:
        k3.metric("Nachzahlung" if ergebnis.ist_nachzahlung else "Guthaben",
                  f"{eur(ergebnis.betrag_absolut)} €")

    if ergebnis.zeilen:
        if stamm.ist_zwischenabrechnung:
            if ergebnis.ist_nachzahlung:
                st.success(f"Stand jetzt fehlen **{eur(ergebnis.betrag_absolut)} €** – seine "
                           "Vorauszahlung ist zu niedrig.")
            else:
                st.success(f"Stand jetzt hat er **{eur(ergebnis.betrag_absolut)} €** zu viel "
                           "gezahlt – seine Vorauszahlung ist reichlich bemessen.")
            if ergebnis.hochrechnung_jahr:
                st.info(f"Aufs ganze Jahr hochgerechnet: **{eur(ergebnis.hochrechnung_jahr)} €** "
                        f"= **{eur(ergebnis.hochrechnung_jahr / 12)} €** im Monat. "
                        "Nachzahlen muss er aus dieser Zwischenabrechnung nichts.")
        elif ergebnis.betrag_absolut < 0.01:
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
            "📄 Abrechnung für den Mieter als PDF speichern",
            data=erzeuge_pdf(stamm, ergebnis),
            file_name=dateiname(stamm),
            mime="application/pdf",
            type="primary",
            width="stretch",
        ):
            try:
                abgelegt = speicher.archivieren(stamm, st.session_state.positionen)
                st.success(f"Abrechnung abgelegt unter `{speicher.archivname(abgelegt)}` – "
                           "du findest sie in der Seitenleiste wieder.")
            except OSError as fehler:
                st.warning(f"Ablegen nicht möglich: {fehler}")
        st.caption(
            "Vor dem Aushändigen kurz prüfen: Namen, Zeitraum, Beträge, IBAN. "
            "Das PDF ausdrucken, unterschreiben und dem Mieter geben – "
            "am besten mit Kopien der Rechnungen."
        )

        if stamm.eigene_abrechnung:
            eigenes = berechne(stamm, st.session_state.positionen, fuer="vermieter")
            st.divider()
            st.markdown(f"**Deine eigene Wohnung:** {eur(eigenes.summe_anteil)} € von "
                        f"{eur(ergebnis.summe_gesamtkosten)} € Gesamtkosten. "
                        f"Nicht verteilt (Leerstand, Zeiten ohne Mieter): "
                        f"{eur(max(0.0, ergebnis.summe_gesamtkosten - ergebnis.summe_anteil - eigenes.summe_anteil))} €.")
            if not eigenes.fehler:
                st.download_button(
                    "📄 Aufstellung für die eigene Wohnung speichern",
                    data=erzeuge_pdf(stamm, eigenes),
                    file_name=dateiname(stamm, fuer="vermieter"),
                    mime="application/pdf",
                    width="stretch",
                )

# Nach jeder Eingabe alles dauerhaft sichern.
sichern()
