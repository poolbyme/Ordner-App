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

### Was einmal eingetragen wird und was jedes Jahr neu

| Bleibt gleich (Tab 1) | Ändert sich (Tabs 2–5) |
| --- | --- |
| Name und Anschrift des Vermieters, IBAN | Art der Abrechnung und Zeitraum |
| Adresse des Hauses, vermietete Wohnung | Mieter, Personenzahl |
| Wohnfläche gesamt und der Mietwohnung | Rechnungsbeträge |
| Grundstück, Anzahl der Wohnungen | Zählerstände |
|  | Vorauszahlungen, CO2-Anteil |

Die App speichert **automatisch nach jeder Eingabe** in `daten/abrechnung.json`.
Beim nächsten Start steht alles wieder da; die Datei ist im Klartext lesbar und
lässt sich kopieren. Ein anderer Ordner geht über die Umgebungsvariable
`NEBENKOSTEN_DATEN` (z. B. ein Ordner, der in die Cloud synchronisiert wird):

```bash
NEBENKOSTEN_DATEN=~/Dropbox/nebenkosten streamlit run nebenkosten_app.py
```

Jede fertige Abrechnung wird beim PDF-Download zusätzlich unter Jahr und
Mietername in `daten/archiv/` abgelegt und lässt sich in der Seitenleiste wieder
öffnen. Der Knopf „Nächstes Jahr vorbereiten" schiebt den Zeitraum weiter und
leert nur die Beträge und Zählerstände.

**Wichtig beim Betrieb in der Cloud:** In der Streamlit Community Cloud ist das
Dateisystem flüchtig – nach einem Neustart der App sind die Daten weg. Dauerhaft
gespeichert wird nur, wenn die App auf dem eigenen Rechner läuft. In der Cloud
hilft die Sicherungskopie aus der Seitenleiste.

### Ablauf

1. **Haus (bleibt gleich)** – Vermieter, Adresse, Wohnflächen, Grundstück,
   Anzahl der Wohnungen. Einmal ausfüllen, danach nie wieder.
2. **Diese Abrechnung** – **Jahresabrechnung** oder **Abrechnung zum Mietende**
   auswählen; bei einem Auszug wird bis zum Auszugstag gerechnet und alles, was
   nicht über einen Zähler läuft, tageweise geteilt. Dazu Mieter und Personenzahl.
   Die gewählte Art steht auch im Kopf des PDF.
3. **Kosten** – pro Zeile eintragen, was **für das ganze Haus** angefallen ist.
   Die üblichen Kostenarten sind vorbereitet, jede mit dem Hinweis, welcher Beleg
   dazugehört. Pro Zeile wählbar, wie verteilt wird: nach Wohnfläche, nach
   Personenzahl, je Wohnung, nach Zählerstand oder allein auf den Mieter.
4. **Zählerstände** – Stand am Anfang und am Ende, für den Hauptzähler und für
   beide Wohnungen. Den Verbrauch rechnet die App aus. Wo es keinen Zähler gibt,
   lässt sich der Verbrauch direkt eintragen.
5. **Vorauszahlungen** – der monatliche Betrag des Mieters; dazu der eigene Anteil
   an den CO2-Kosten, falls mit Gas oder Öl geheizt wird.
6. **Fertige Abrechnung** – Ergebnis prüfen, PDF herunterladen.

Über „Mehr Einstellungen anzeigen" in der Seitenleiste kommen die selteneren
Felder dazu: Lohnkosten für die Steuererklärung des Mieters, unterjähriger Einzug,
Anrede und Datum des Anschreibens.

### Differenz zwischen Hauptzähler und Wohnungszählern

Der Hauptzähler zeigt fast immer mehr als die Wohnungszähler zusammen –
Messtoleranz, Außenzapfstelle, Leitungsverluste. Diese Differenz darf nicht allein
dem Mieter angelastet werden. Die App zieht die beiden Wohnungszähler vom
Hauptzähler ab und verteilt den Rest:

* **nach Wohnfläche** – der gesetzliche Maßstab, wenn der Mietvertrag nichts
  anderes vorsieht (§ 556a Abs. 1 S. 1 BGB); Voreinstellung
* **nach gemessenem Verbrauch** – ebenfalls üblich, wer mehr verbraucht, trägt mehr

Wird der eigene Zähler nicht eingetragen, bleibt die gesamte Differenz beim
Vermieter. Die Rechnung steht vollständig im PDF, damit der Mieter sie
nachvollziehen kann.

### Was die App prüft

* Zählerstände, die rückwärts laufen; Wohnungszähler, die zusammen mehr anzeigen
  als der Hauptzähler
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
nebenkosten/berechnung.py Verteilung, Zählerdifferenz, Zeitanteil, Saldo, Prüfungen
nebenkosten/speicher.py   dauerhaftes Speichern und Archiv
nebenkosten/pdf.py        PDF-Erzeugung (fpdf2)
tests/                    Tests der Berechnung und der PDF-Ausgabe
```

Für ein echtes €-Zeichen im PDF wird eine Unicode-Schrift benutzt, sofern eine
gefunden wird (System-DejaVu/Liberation oder `nebenkosten/fonts/DejaVuSans.ttf`
plus `DejaVuSans-Bold.ttf`). Andernfalls schreibt das PDF „EUR".
