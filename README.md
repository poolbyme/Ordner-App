# Ordner-App

Dieses Repository enthält zwei eigenständige Streamlit-Apps:

| App | Startdatei | Zweck |
| --- | --- | --- |
| FECG-Ordner | `app.py` | Dienstplan, Mitglieder, Chat |
| Nebenkostenabrechnung | `nebenkosten_app.py` | Betriebskostenabrechnung für Mieter, Ausgabe als PDF |

---

## Nebenkostenabrechnung

Zählerstände und Rechnungsbeträge eintragen – die App verteilt die Kosten auf den
Mieter, zieht seine Vorauszahlungen ab und erzeugt daraus ein fertiges PDF zum
Ausdrucken und Aushändigen.

### Starten

```bash
pip install -r requirements.txt
streamlit run nebenkosten_app.py
```

Für die Streamlit Community Cloud dieselbe Datei als „Main file path" eintragen.
Die App braucht weder Google-Zugang noch Secrets. Alle Eingaben bleiben in der
Sitzung und lassen sich über die Seitenleiste als Datei sichern und wieder laden.

### Ablauf

1. **Angaben** – Vermieter, Mieter, Haus, Abrechnungsjahr, Wohnflächen und
   Personenzahl. Danach werden die meisten Kosten verteilt.
2. **Kosten** – pro Zeile eintragen, was **für das ganze Haus** angefallen ist.
   Die üblichen Kostenarten sind vorbereitet, jede mit dem Hinweis, welcher Beleg
   dazugehört. Pro Zeile wählbar, wie verteilt wird: nach Wohnfläche, nach
   Personenzahl, je Wohnung, nach Zählerstand oder allein auf den Mieter.
3. **Zählerstände** – für jede Zeile, die auf „nach Zählerstand" steht: Stand am
   Jahresanfang und am Jahresende, jeweils für den Hauszähler und den
   Wohnungszähler. Den Verbrauch rechnet die App aus. Wo es keinen eigenen Zähler
   gibt, lässt sich der Verbrauch auch direkt eintragen.
4. **Vorauszahlungen** – der monatliche Betrag des Mieters; dazu der eigene Anteil
   an den CO2-Kosten, falls mit Gas oder Öl geheizt wird.
5. **Abrechnung & PDF** – Ergebnis prüfen, PDF herunterladen.

Über „Mehr Einstellungen anzeigen" in der Seitenleiste kommen die selteneren
Felder dazu: Lohnkosten für die Steuererklärung des Mieters, anteilige Abrechnung
bei Ein- oder Auszug mitten im Jahr, Anrede und Datum des Anschreibens.

### Was die App prüft

* Zählerstände, die rückwärts laufen, und Wohnungen, die mehr verbrauchen als das
  ganze Haus
* Anteile über 100 % bei Fläche und Personenzahl
* Abrechnungszeitraum länger als 12 Monate
* Abrechnungsfrist: Die Abrechnung muss den Mieter innerhalb von 12 Monaten nach
  Ende des Zeitraums erreichen, sonst ist eine Nachforderung in der Regel
  ausgeschlossen – ein Guthaben bleibt trotzdem auszuzahlen
* Kostenarten, deren Bezeichnung nach Reparatur, Instandhaltung oder Verwaltung
  klingt – das darf nicht auf den Mieter umgelegt werden
* Heiz- und Warmwasserkosten nach Fläche bei mehr als zwei Wohnungen

### Worauf es rechtlich ankommt

* **Umlage muss im Mietvertrag stehen.** Ohne eine Klausel, die die Betriebskosten
  auf den Mieter überträgt, gibt es nichts abzurechnen. Nennt der Vertrag einen
  bestimmten Verteilerschlüssel, gilt dieser vor dem gesetzlichen Flächenschlüssel
  (§ 556a BGB).
* **Heizkosten.** Normalerweise müssen 50–70 % verbrauchsabhängig abgerechnet
  werden. Im Gebäude mit höchstens zwei Wohnungen, von denen der Vermieter eine
  selbst bewohnt, gilt diese Pflicht nicht (§ 2 HeizkostenV) – dort ist die
  Verteilung nach Wohnfläche zulässig, sofern der Mietvertrag nichts anderes sagt.
* **CO2-Kosten.** Bei Gas- oder Ölheizung trägt der Vermieter seit 2023 einen Teil
  der CO2-Abgabe selbst (CO2KostAufG). Der Betrag steht in der Jahresrechnung des
  Versorgers und wird in der App abgezogen.
* **Kabelanschluss** ist seit dem 01.07.2024 nicht mehr umlagefähig.
* **Nicht umlagefähig** sind außerdem Reparaturen und Instandhaltung,
  Verwaltungs- und Kontoführungskosten, Rücklagen sowie Rechtsschutz- und
  Mietausfallversicherung.
* **Eigenleistung** des Vermieters (Rasen mähen, Schnee räumen) darf mit dem
  ortsüblichen Preis einer Firma ohne Mehrwertsteuer angesetzt werden
  (§ 1 Abs. 1 S. 2 BetrKV).

Die App erstellt ein Abrechnungsschreiben, keine Rechtsberatung.

### Tests

```bash
python tests/test_nebenkosten.py     # oder: python -m pytest tests/
```

### Aufbau

```
nebenkosten_app.py        Streamlit-Oberfläche
nebenkosten/modell.py     Datenmodell, Katalog der Betriebskosten nach § 2 BetrKV
nebenkosten/berechnung.py Verteilung, Zählerstände, Zeitanteil, Saldo, Prüfungen
nebenkosten/pdf.py        PDF-Erzeugung (fpdf2)
tests/                    Tests der Berechnung und der PDF-Ausgabe
```

Für ein echtes €-Zeichen im PDF wird eine Unicode-Schrift benutzt, sofern eine
gefunden wird (System-DejaVu/Liberation oder `nebenkosten/fonts/DejaVuSans.ttf`
plus `DejaVuSans-Bold.ttf`). Andernfalls schreibt das PDF „EUR".
