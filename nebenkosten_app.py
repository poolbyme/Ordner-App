"""Nebenkostenabrechnung – Streamlit-App.

Start:  streamlit run nebenkosten_app.py
"""

from __future__ import annotations

import json
from datetime import date

import pandas as pd
import streamlit as st

from nebenkosten.berechnung import berechne, eur, parse_datum, zahl
from nebenkosten.modell import (
    SCHLUESSEL, Position, Stammdaten, as_dict, from_dict, standard_positionen,
)
from nebenkosten.pdf import dateiname, erzeuge_pdf

st.set_page_config(page_title="Nebenkostenabrechnung", page_icon="🏠", layout="wide")

SCHLUESSEL_LABELS = list(SCHLUESSEL.values())
LABEL_ZU_KEY = {v: k for k, v in SCHLUESSEL.items()}

SPALTEN = {
    "aktiv": "Aktiv",
    "bezeichnung": "Kostenart",
    "betrag": "Gesamtkosten (€)",
    "schluessel": "Verteilerschlüssel",
    "verbrauch_gesamt": "Verbrauch Haus",
    "verbrauch_mieter": "Verbrauch Mieter",
    "einheit": "Einheit",
    "arbeitskosten": "davon Arbeitskosten (€)",
    "zeitanteilig": "zeitanteilig",
    "hinweis": "Hinweis",
}


# --------------------------------------------------------------------------
# Zustand
# --------------------------------------------------------------------------
def init_state() -> None:
    if "stamm" in st.session_state:
        return
    jahr = date.today().year - 1
    st.session_state.stamm = Stammdaten(
        zeitraum_von=date(jahr, 1, 1).isoformat(),
        zeitraum_bis=date(jahr, 12, 31).isoformat(),
        nutzung_von=date(jahr, 1, 1).isoformat(),
        nutzung_bis=date(jahr, 12, 31).isoformat(),
    )
    st.session_state.positionen = standard_positionen()


def positionen_als_df(positionen: list[Position]) -> pd.DataFrame:
    return pd.DataFrame([{
        SPALTEN["aktiv"]: p.aktiv,
        SPALTEN["bezeichnung"]: p.bezeichnung,
        SPALTEN["betrag"]: float(p.betrag),
        SPALTEN["schluessel"]: SCHLUESSEL.get(p.schluessel, SCHLUESSEL["flaeche"]),
        SPALTEN["verbrauch_gesamt"]: float(p.verbrauch_gesamt),
        SPALTEN["verbrauch_mieter"]: float(p.verbrauch_mieter),
        SPALTEN["einheit"]: p.einheit,
        SPALTEN["arbeitskosten"]: float(p.arbeitskosten),
        SPALTEN["zeitanteilig"]: p.zeitanteilig,
        SPALTEN["hinweis"]: p.hinweis,
    } for p in positionen])


def df_als_positionen(df: pd.DataFrame) -> list[Position]:
    positionen: list[Position] = []
    for _, r in df.iterrows():
        bezeichnung = str(r.get(SPALTEN["bezeichnung"]) or "").strip()
        if not bezeichnung:
            continue

        def zahlwert(spalte: str) -> float:
            wert = r.get(SPALTEN[spalte])
            try:
                return float(wert) if pd.notna(wert) else 0.0
            except (TypeError, ValueError):
                return 0.0

        positionen.append(Position(
            bezeichnung=bezeichnung,
            betrag=zahlwert("betrag"),
            schluessel=LABEL_ZU_KEY.get(str(r.get(SPALTEN["schluessel"])), "flaeche"),
            verbrauch_gesamt=zahlwert("verbrauch_gesamt"),
            verbrauch_mieter=zahlwert("verbrauch_mieter"),
            einheit=str(r.get(SPALTEN["einheit"]) or ""),
            arbeitskosten=zahlwert("arbeitskosten"),
            zeitanteilig=bool(r.get(SPALTEN["zeitanteilig"], True)),
            aktiv=bool(r.get(SPALTEN["aktiv"], True)),
            hinweis=str(r.get(SPALTEN["hinweis"]) or ""),
        ))
    return positionen


def datum_feld(label: str, wert: str, key: str, hilfe: str | None = None) -> str:
    vorgabe = parse_datum(wert) or date.today()
    return st.date_input(label, value=vorgabe, key=key, format="DD.MM.YYYY",
                         help=hilfe).isoformat()


init_state()
stamm: Stammdaten = st.session_state.stamm

# --------------------------------------------------------------------------
# Seitenleiste: Speichern / Laden
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("Daten sichern")
    st.download_button(
        "💾 Eingaben speichern (JSON)",
        data=json.dumps(as_dict(stamm, st.session_state.positionen),
                        ensure_ascii=False, indent=2).encode("utf-8"),
        file_name=f"nebenkosten_{(parse_datum(stamm.zeitraum_bis) or date.today()).year}.json",
        mime="application/json",
        width="stretch",
    )
    hochgeladen = st.file_uploader("📂 Gespeicherte Daten laden", type="json")
    if hochgeladen is not None and st.button("Geladene Daten übernehmen", width="stretch"):
        try:
            neu_stamm, neu_pos = from_dict(json.load(hochgeladen))
            st.session_state.stamm = neu_stamm
            st.session_state.positionen = neu_pos
            st.success("Daten geladen.")
            st.rerun()
        except Exception as fehler:  # noqa: BLE001 – Nutzerdatei kann alles enthalten
            st.error(f"Datei konnte nicht gelesen werden: {fehler}")

    st.divider()
    if st.button("📅 Für nächstes Jahr vorbereiten", width="stretch",
                 help="Zeitraum um ein Jahr weiterschieben, Beträge und Zählerstände leeren."):
        for feld in ("zeitraum_von", "zeitraum_bis", "nutzung_von", "nutzung_bis"):
            d = parse_datum(getattr(stamm, feld))
            if d:
                try:
                    setattr(stamm, feld, d.replace(year=d.year + 1).isoformat())
                except ValueError:  # 29.02.
                    setattr(stamm, feld, d.replace(year=d.year + 1, day=28).isoformat())
        for p in st.session_state.positionen:
            p.betrag = 0.0
            p.verbrauch_gesamt = p.verbrauch_mieter = p.arbeitskosten = 0.0
        st.rerun()

    if st.button("🗑️ Alles zurücksetzen", width="stretch"):
        for schluessel in ("stamm", "positionen"):
            st.session_state.pop(schluessel, None)
        st.rerun()

    st.divider()
    st.caption(
        "Diese App erstellt ein Abrechnungsdokument, sie ersetzt keine Rechtsberatung. "
        "Prüfe vor dem Versand, ob der Mietvertrag die Umlage der Betriebskosten "
        "tatsächlich vereinbart und welche Verteilerschlüssel dort stehen."
    )

st.title("🏠 Nebenkostenabrechnung")
st.caption("Betriebskostenabrechnung für eine vermietete Wohnung – Eingabe, Berechnung, PDF.")

tab_stamm, tab_kosten, tab_vz, tab_ergebnis = st.tabs(
    ["1 · Stammdaten", "2 · Kosten", "3 · Vorauszahlungen", "4 · Abrechnung & PDF"]
)

# --------------------------------------------------------------------------
# 1 Stammdaten
# --------------------------------------------------------------------------
with tab_stamm:
    links, rechts = st.columns(2)
    with links:
        st.subheader("Vermieter")
        stamm.vermieter_name = st.text_input("Name", stamm.vermieter_name, key="v_name")
        stamm.vermieter_strasse = st.text_input("Straße und Hausnummer", stamm.vermieter_strasse, key="v_str")
        stamm.vermieter_plz_ort = st.text_input("PLZ und Ort", stamm.vermieter_plz_ort, key="v_ort")
        stamm.vermieter_iban = st.text_input("IBAN (für Nachzahlungen)", stamm.vermieter_iban, key="v_iban")
        stamm.vermieter_bank = st.text_input("Bank (optional)", stamm.vermieter_bank, key="v_bank")

    with rechts:
        st.subheader("Mieter und Wohnung")
        stamm.mieter_name = st.text_input("Name des Mieters", stamm.mieter_name, key="m_name")
        stamm.anrede = st.text_input("Anrede im Anschreiben", stamm.anrede, key="m_anrede")
        stamm.mieter_wohnung = st.text_input("Bezeichnung der Wohnung", stamm.mieter_wohnung, key="m_wohnung")
        stamm.objekt_strasse = st.text_input("Objekt: Straße und Hausnummer", stamm.objekt_strasse, key="o_str")
        stamm.objekt_plz_ort = st.text_input("Objekt: PLZ und Ort", stamm.objekt_plz_ort, key="o_ort")

    st.divider()
    st.subheader("Abrechnungszeitraum")
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        stamm.zeitraum_von = datum_feld("Zeitraum von", stamm.zeitraum_von, "z_von")
    with s2:
        stamm.zeitraum_bis = datum_feld("Zeitraum bis", stamm.zeitraum_bis, "z_bis",
                                        "Höchstens 12 Monate (§ 556 Abs. 3 BGB).")
    with s3:
        stamm.nutzung_von = datum_feld("Mietzeit von", stamm.nutzung_von, "n_von",
                                       "Nur ändern, wenn der Mieter unterjährig ein- oder ausgezogen ist.")
    with s4:
        stamm.nutzung_bis = datum_feld("Mietzeit bis", stamm.nutzung_bis, "n_bis")

    st.divider()
    st.subheader("Umlagegrundlagen")
    g1, g2, g3 = st.columns(3)
    with g1:
        stamm.flaeche_gesamt = st.number_input("Gesamtwohnfläche des Hauses (m²)",
                                               min_value=0.0, step=1.0, value=float(stamm.flaeche_gesamt))
        stamm.flaeche_mieter = st.number_input("davon Wohnfläche des Mieters (m²)",
                                               min_value=0.0, step=1.0, value=float(stamm.flaeche_mieter))
    with g2:
        stamm.personen_gesamt = st.number_input("Personen im Haus (gesamt)",
                                                min_value=0.0, step=1.0, value=float(stamm.personen_gesamt))
        stamm.personen_mieter = st.number_input("davon in der Mietwohnung",
                                                min_value=0.0, step=1.0, value=float(stamm.personen_mieter))
    with g3:
        stamm.einheiten_gesamt = st.number_input("Wohneinheiten im Haus",
                                                 min_value=1.0, step=1.0, value=float(stamm.einheiten_gesamt))
        stamm.einheiten_mieter = st.number_input("davon vermietet an diesen Mieter",
                                                 min_value=0.0, step=1.0, value=float(stamm.einheiten_mieter))

    st.divider()
    st.subheader("Anschreiben")
    a1, a2, a3 = st.columns(3)
    with a1:
        stamm.ort = st.text_input("Ort für die Datumszeile", stamm.ort, key="s_ort")
    with a2:
        stamm.datum = datum_feld("Datum der Abrechnung", stamm.datum, "s_datum")
    with a3:
        stamm.zahlungsfrist_tage = int(st.number_input("Zahlungsfrist (Tage)", min_value=0, max_value=90,
                                                       step=1, value=int(stamm.zahlungsfrist_tage)))

# --------------------------------------------------------------------------
# 2 Kosten
# --------------------------------------------------------------------------
with tab_kosten:
    st.subheader("Kostenpositionen des Abrechnungszeitraums")
    st.caption(
        "Trage die **Gesamtkosten des Hauses** ein – die App verteilt sie nach dem gewählten "
        "Schlüssel. Nicht benötigte Zeilen einfach abwählen; neue Zeilen unten anfügen."
    )

    bearbeitet = st.data_editor(
        positionen_als_df(st.session_state.positionen),
        key="kosten_editor",
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        column_config={
            SPALTEN["aktiv"]: st.column_config.CheckboxColumn(width="small", default=True),
            SPALTEN["bezeichnung"]: st.column_config.TextColumn(width="medium", required=True),
            SPALTEN["betrag"]: st.column_config.NumberColumn(format="%.2f", min_value=0.0, step=10.0),
            SPALTEN["schluessel"]: st.column_config.SelectboxColumn(
                options=SCHLUESSEL_LABELS, default=SCHLUESSEL["flaeche"], width="medium"),
            SPALTEN["verbrauch_gesamt"]: st.column_config.NumberColumn(
                format="%.3f", min_value=0.0, help="Nur beim Schlüssel „Verbrauch“: Zählerwert für das ganze Haus."),
            SPALTEN["verbrauch_mieter"]: st.column_config.NumberColumn(
                format="%.3f", min_value=0.0, help="Nur beim Schlüssel „Verbrauch“: Zählerwert der Mietwohnung."),
            SPALTEN["einheit"]: st.column_config.TextColumn(width="small", help="z. B. m³ oder kWh"),
            SPALTEN["arbeitskosten"]: st.column_config.NumberColumn(
                format="%.2f", min_value=0.0,
                help="Im Betrag enthaltene Lohn-/Arbeitskosten – für die Bescheinigung nach § 35a EStG."),
            SPALTEN["zeitanteilig"]: st.column_config.CheckboxColumn(
                width="small", default=True,
                help="Bei unterjähriger Mietzeit anteilig nach Tagen kürzen."),
            SPALTEN["hinweis"]: st.column_config.TextColumn(width="large"),
        },
    )
    st.session_state.positionen = df_als_positionen(bearbeitet)

    with st.expander("Was darf umgelegt werden?"):
        st.markdown(
            """
**Umlagefähig** sind nur die in § 2 BetrKV aufgezählten laufenden Betriebskosten –
und nur, wenn der Mietvertrag ihre Umlage vereinbart.

**Nicht umlagefähig** und deshalb Sache des Vermieters:

* Reparaturen, Instandhaltung und Instandsetzung (auch der Heizung)
* Verwaltungskosten, Kontoführung, Porto, Steuerberatung
* Rücklagen, Mietausfallwagnis, Rechtsschutz- und Reparaturversicherung
* Kabelanschluss / Gemeinschaftsantenne: seit dem 01.07.2024 nicht mehr über die
  Nebenkosten umlegbar (Ende des Nebenkostenprivilegs)
* „Sonstige Betriebskosten“ nur, wenn sie im Mietvertrag konkret benannt sind

Bei einer Wartungsrechnung, die Wartung **und** Reparatur enthält, darf nur der
Wartungsanteil in die Abrechnung.
            """
        )

# --------------------------------------------------------------------------
# 3 Vorauszahlungen
# --------------------------------------------------------------------------
with tab_vz:
    st.subheader("Geleistete Vorauszahlungen")
    v1, v2 = st.columns(2)
    with v1:
        stamm.vorauszahlung_monatlich = st.number_input(
            "Monatliche Vorauszahlung (€)", min_value=0.0, step=10.0,
            value=float(stamm.vorauszahlung_monatlich))
        stamm.vorauszahlung_monate = int(st.number_input(
            "Anzahl der Monate", min_value=0, max_value=12, step=1,
            value=int(stamm.vorauszahlung_monate)))
        st.info(f"Rechnerisch: **{eur(stamm.vorauszahlung_monatlich * stamm.vorauszahlung_monate)} €**")
    with v2:
        abweichend = st.checkbox(
            "Tatsächlich gezahlte Summe abweichend eintragen",
            value=stamm.vorauszahlung_manuell is not None,
            help="Zum Beispiel, wenn der Mieter unterjährig eine andere Vorauszahlung geleistet hat.")
        if abweichend:
            stamm.vorauszahlung_manuell = st.number_input(
                "Tatsächlich gezahlte Vorauszahlungen (€)", min_value=0.0, step=10.0,
                value=float(stamm.vorauszahlung_manuell or 0.0))
        else:
            stamm.vorauszahlung_manuell = None

    st.divider()
    st.subheader("CO2-Kosten und Anpassung")
    c1, c2 = st.columns(2)
    with c1:
        stamm.co2_abzug = st.number_input(
            "CO2-Kostenanteil des Vermieters (€, wird abgezogen)",
            min_value=0.0, step=1.0, value=float(stamm.co2_abzug),
            help="Bei Erdgas- oder Ölheizung muss sich der Vermieter seit 2023 nach dem "
                 "Stufenmodell des CO2KostAufG an den CO2-Kosten beteiligen. Der Anteil steht "
                 "in der Rechnung des Energieversorgers bzw. lässt sich mit dem Rechner des "
                 "Bundeswirtschaftsministeriums ermitteln.")
    with c2:
        stamm.anpassung_vorschlagen = st.checkbox(
            "Anpassung der monatlichen Vorauszahlung im PDF ankündigen",
            value=stamm.anpassung_vorschlagen,
            help="§ 560 Abs. 4 BGB – zulässig nach einer Abrechnung, in angemessener Höhe.")

# --------------------------------------------------------------------------
# 4 Ergebnis
# --------------------------------------------------------------------------
with tab_ergebnis:
    ergebnis = berechne(stamm, st.session_state.positionen)

    for fehler in ergebnis.fehler:
        st.error(fehler)
    for warnung in ergebnis.warnungen:
        st.warning(warnung)

    k1, k2, k3 = st.columns(3)
    k1.metric("Anteil des Mieters", f"{eur(ergebnis.umlage)} €")
    k2.metric("Vorauszahlungen", f"{eur(ergebnis.vorauszahlungen)} €")
    k3.metric("Nachzahlung" if ergebnis.ist_nachzahlung else "Guthaben",
              f"{eur(ergebnis.betrag_absolut)} €",
              delta=("Mieter zahlt" if ergebnis.ist_nachzahlung else "Mieter erhält"),
              delta_color="inverse" if ergebnis.ist_nachzahlung else "normal")

    if ergebnis.zeilen:
        st.dataframe(
            pd.DataFrame([{
                "Kostenart": z.bezeichnung,
                "Gesamtkosten (€)": z.gesamtkosten,
                "Verteilerschlüssel": z.schluessel_text,
                "Anteil Mieter (€)": z.anteil,
            } for z in ergebnis.zeilen]),
            width="stretch", hide_index=True,
            column_config={
                "Gesamtkosten (€)": st.column_config.NumberColumn(format="%.2f"),
                "Anteil Mieter (€)": st.column_config.NumberColumn(format="%.2f"),
            },
        )
    else:
        st.info("Noch keine Kostenpositionen mit Beträgen erfasst.")

    e1, e2 = st.columns(2)
    with e1:
        if ergebnis.arbeitskosten_mieter:
            st.caption(f"Bescheinigung § 35a EStG: **{eur(ergebnis.arbeitskosten_mieter)} €** "
                       "anteilige Lohn- und Arbeitskosten.")
        if ergebnis.tage_nutzung and ergebnis.tage_nutzung < ergebnis.tage_zeitraum:
            st.caption(f"Zeitanteil: {ergebnis.tage_nutzung} von {ergebnis.tage_zeitraum} Tagen "
                       f"({zahl(ergebnis.tage_nutzung / ergebnis.tage_zeitraum * 100)} %).")
    with e2:
        if ergebnis.empfehlung_vorauszahlung:
            st.caption(f"Rechnerisch angemessene neue Vorauszahlung: "
                       f"**{eur(ergebnis.empfehlung_vorauszahlung)} €** im Monat.")

    st.divider()
    if ergebnis.fehler:
        st.error("Bitte zuerst die oben genannten Punkte korrigieren – dann lässt sich das PDF erstellen.")
    elif not ergebnis.zeilen:
        st.info("Ohne Kostenpositionen gibt es nichts abzurechnen.")
    else:
        pdf_bytes = erzeuge_pdf(stamm, ergebnis)
        st.download_button(
            "📄 Abrechnung als PDF herunterladen",
            data=pdf_bytes,
            file_name=dateiname(stamm),
            mime="application/pdf",
            type="primary",
            width="stretch",
        )
        st.caption("Vor dem Aushändigen prüfen: Namen, Zeitraum, Beträge und Kontodaten.")
