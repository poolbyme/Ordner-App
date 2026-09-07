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

### Auf dem Handy benutzen

Die App ist eine Webseite – sie läuft überall, wo ein Browser ist. Zwei Wege:

**A · Rechner läuft, Handy im selben WLAN** (nichts einzurichten, Daten bleiben zu Hause)

```bash
streamlit run nebenkosten_app.py --server.address 0.0.0.0
```

Im Terminal erscheint eine „Network URL" wie `http://192.168.1.23:8501` – die am
Handy im Browser öffnen. Der Rechner muss dabei laufen. Über „Zum Startbildschirm
hinzufügen" wird daraus ein Symbol wie bei einer App.

**B · Streamlit Community Cloud** (überall erreichbar, Rechner kann aus bleiben)

Dort ist der Dateispeicher flüchtig. Damit die Daten einen Neustart überleben,
speichert die App in eine Google-Tabelle, sobald in den Streamlit-Secrets steht:

```toml
gcp_json = "{...Zugangsdaten des Google-Dienstkontos als JSON-Text...}"
nebenkosten_sheet_url = "https://docs.google.com/spreadsheets/d/…/edit"
```

Die Tabelle muss für die E-Mail-Adresse des Dienstkontos freigegeben sein
(Freigeben → E-Mail eintragen → Bearbeiter). Die App legt darin ein Blatt
`nebenkosten` an: eine Zeile für den aktuellen Stand, je eine weitere für jede
fertige Abrechnung. Fehlen die Angaben oder ist die Tabelle nicht erreichbar,
schreibt die App wie gehabt in eine Datei und sagt das in der Seitenleiste.

In beiden Fällen hilft der Schalter **📱 Handy-Ansicht** in der Seitenleiste: Statt
breiter Tabellen erscheinen einzelne Eingabefelder untereinander, die sich mit dem
Daumen bedienen lassen. Gerechnet wird in beiden Ansichten gleich.

### Wo liegt was

| Was | Wo |
| --- | --- |
| Alle Eingaben | `daten/abrechnung.json` (oder die Google-Tabelle) |
| Fertige Abrechnungen | `daten/archiv/2025_Mustermann_Jahresabrechnung.json` |
| Sicherungskopie | wohin dein Browser Downloads legt |
| Das fertige PDF | ebenfalls im Download-Ordner, am Handy unter Dateien / Downloads |

Der Ablageort steht in der App selbst: Seitenleiste → „Wo liegen meine Daten?".

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
2. **Diese Abrechnung** – Art auswählen: **Jahresabrechnung**, **Abrechnung zum
   Mietende** (rechnet bis zum Auszugstag, alles ohne Zähler wird tageweise geteilt)
   oder **Zwischenabrechnung** (siehe unten). Dazu Mieter und Personenzahl. Die
   gewählte Art steht auch im Kopf des PDF.
3. **Kosten** – pro Zeile eintragen, was **für das ganze Haus** angefallen ist.
   Die üblichen Kostenarten sind vorbereitet, jede mit dem Hinweis, welcher Beleg
   dazugehört. Pro Zeile wählbar, wie verteilt wird: nach Wohnfläche, nach
   Personenzahl, je Wohnung, nach Zählerstand oder allein auf den Mieter.
4. **Zählerstände** – pro Kostenart eine Tabelle mit allen zugehörigen Zählern:
   Name, wem er gehört, Stand am Anfang und am Ende. Den Verbrauch rechnet die App
   aus. Wo es keinen Zähler gibt, lassen sich die Mengen direkt eintragen.
5. **Vorauszahlungen** – der monatliche Betrag des Mieters; dazu der eigene Anteil
   an den CO2-Kosten, falls mit Gas oder Öl geheizt wird.
6. **Fertige Abrechnung** – Ergebnis prüfen, PDF herunterladen.

Über „Mehr Einstellungen anzeigen" in der Seitenleiste kommen die selteneren
Felder dazu: Lohnkosten für die Steuererklärung des Mieters, unterjähriger Einzug,
Anrede und Datum des Anschreibens.

### Zwischenabrechnung

Für eine Momentaufnahme mitten im Jahr – etwa beim Wechsel des Gasanbieters oder
wenn der Mieter wissen möchte, ob seine Vorauszahlung passt. Zeitraum und Stichtag
sind frei wählbar, der Anlass steht im PDF.

Rechtlich ist das **keine** Abrechnung im Sinne des § 556 Abs. 3 BGB: Sie begründet
keine Nachforderung, setzt keine Fristen in Gang und erlaubt noch keine Änderung der
Vorauszahlung. Das PDF sagt das ausdrücklich und enthält deshalb keine
Zahlungsaufforderung. Stattdessen rechnet die App den Stand auf zwölf Monate hoch und
nennt eine rechnerisch passende monatliche Vorauszahlung – genau die Auskunft, die ein
Mieter mit dieser Frage sucht.

**Anbieterwechsel mitten im Jahr:** Dafür braucht es keine Zwischenabrechnung. Beide
Rechnungen gehören in dieselbe Jahresabrechnung – entweder als eine Summe oder als zwei
Zeilen („Gas 01.01.–14.06. Anbieter A" und „Gas 15.06.–31.12. Anbieter B"). Verteilt
wird nach den Zählerständen des ganzen Jahres; die Ablesung zum Wechseltag braucht nur
der Versorger. Eine Zwischenabrechnung lohnt sich, wenn der Mieter einen Zwischenstand
sehen soll oder du selbst wissen willst, wo ihr steht.

### Zähler

Zu jeder Kostenart gehören beliebig viele Zähler, jeder mit Anfangs- und Endstand und
der Angabe, wem er gehört: **Hauptzähler (ganzes Haus)**, **Wohnung des Mieters** oder
**deine Wohnung**. Mehrere Zähler derselben Partei werden addiert – Kalt- und
Warmwasserzähler einer Wohnung ergeben zusammen ihren Wasserverbrauch.

Pro Kostenart ist einstellbar, woraus sich der Anteil des Mieters ergibt:

* **Anteil am Hauptzähler** – die Rechnung hängt am Hauptzähler (Wasser). Was der
  Hauptzähler mehr anzeigt als die Unterzähler zusammen, wird verteilt (siehe unten).
* **Nur die Unterzähler** – die Zähler messen etwas anderes als die Rechnung:
  Wärmemengenzähler in kWh bei einer Gasrechnung. Dann zählt allein das Verhältnis der
  Unterzähler zueinander; ein Hauptzähler steht nur nachrichtlich dabei.

Eine Kostenart kann die Zähler einer anderen mitbenutzen – **Abwasser** rechnet mit den
Zählerständen von **Wasser**, ohne dass etwas doppelt eingetippt wird.

Voreingestellt ist das übliche Zweifamilienhaus:

| Kostenart | Zähler | Grundlage |
| --- | --- | --- |
| Wasser | Hauptzähler, Kalt- und Warmwasser beider Wohnungen | Anteil am Hauptzähler |
| Abwasser | – (nutzt die Zähler von Wasser) | wie Wasser |
| Heizung (Gas) | Gaszähler (nachrichtlich), Wärmemengenzähler beider Wohnungen | nur Unterzähler |
| Warmwasser (Gas) | Warmwasserzähler beider Wohnungen | nur Unterzähler |

Beim Knopf „Nächstes Jahr vorbereiten" wird der Endstand jedes Zählers zum
Anfangsstand des neuen Jahres.

**Gasrechnung aufteilen:** Messen die Wärmemengenzähler nur die Heizung, steckt im Gas
auch das Warmwasser. Die Faustformel der Heizkostenverordnung trennt beides:
Wärme fürs Warmwasser in kWh = 2,5 × Warmwassermenge in m³ × (Warmwassertemperatur − 10).
Der so errechnete Kostenanteil kommt in die Zeile „Warmwasser (Gas)", der Rest in
„Heizung (Gas)". Der Hinweis steht auch im Tab „Zählerstände".

### Heiz- und Warmwasserkosten

Zwei Werkzeuge, die den üblichen Weg der Abrechnungsdienste nachbilden:

**Grundkosten und Verbrauchskosten trennen.** Je Kostenart lässt sich ein Anteil
angeben (0–50 %), der nach Wohnfläche verteilt wird; der Rest geht nach Verbrauch.
Bei Heizung und Warmwasser sind 30 % Grundkosten üblich. Im PDF erscheinen dann zwei
Zeilen, „Heizung – Grundkosten 30 %" und „Heizung – Verbrauchskosten 70 %", wie in
einer professionellen Abrechnung.

**Gasrechnung aufteilen (Tab Kosten).** Messen die Wärmemengenzähler nur die Heizung,
steckt im Gas auch das Warmwasser. Der Rechner benutzt die Formel des § 9 Abs. 2
HeizkostenV – Q = 2,5 × Warmwassermenge in m³ × (Warmwassertemperatur − 10 °C), plus
Zuschlag für die Anlagenverluste – und teilt die Gaskosten auf beide Zeilen auf. Ohne
gemessene Warmwassertemperatur schreibt die Verordnung 60 °C vor; ein niedrigerer Wert
verschiebt Kosten von der Warmwasser- in die Heizungsposition und ist nur mit
gemessener Temperatur haltbar.

### CO2-Kosten

Bei Gas- oder Ölheizung muss sich der Vermieter seit 2023 an den CO2-Kosten beteiligen
(CO2KostAufG). Der Rechner im Tab „Vorauszahlungen" nimmt den CO2-Ausstoß in kg und die
CO2-Kosten in Euro von der Energierechnung, bezieht die Emissionen auf die Wohnfläche
und liest den Vermieteranteil aus dem gesetzlichen Stufenmodell ab:

| kg CO2 je m² und Jahr | Vermieter | Mieter |
| --- | --- | --- |
| unter 12 | 0 % | 100 % |
| 12 bis unter 22 | 10–20 % | 90–80 % |
| 22 bis unter 32 | 30–40 % | 70–60 % |
| 32 bis unter 42 | 50–60 % | 50–40 % |
| 42 bis unter 52 | 70–80 % | 30–20 % |
| 52 und mehr | 95 % | 5 % |

Der so ermittelte Betrag wird vom Anteil des Mieters abgezogen. Fehlen die Angaben auf
der Rechnung, ist der Versorger verpflichtet, sie zu liefern.

### Aufstellung für die eigene Wohnung

Der Schalter „Auch eine Aufstellung für die eigene Wohnung erstellen" erzeugt ein
zweites PDF: dieselbe Rechnung aus Sicht des Vermieters – eigene Wohnfläche, eigene
Zähler, voller Zeitraum, keine Vorauszahlungen. Gedacht für die eigenen Unterlagen und
die Steuererklärung, nicht zur Weitergabe an den Mieter; das PDF sagt das auch. Der
Ergebnis-Tab zeigt zusätzlich, welcher Teil der Gesamtkosten auf niemanden entfällt –
das ist der Leerstandsanteil, den der Vermieter trägt.

Für Kosten, die nur eine Seite betreffen, gibt es die Verteilungen **„nur der Mieter"**
und **„nur ich selbst"** – etwa für getrennte Mülltonnen.

### Außenzapfstelle und andere gemeinsame Zähler

Ein Zähler kann auch **„gemeinsam genutzt"** sein – typisch die Außenzapfstelle für
den Garten. Seine Menge gehört keiner Wohnung allein und wird nach demselben Maßstab
geteilt wie die Zählerdifferenz. Nutzt den Außenhahn nur eine Seite, wird der Zähler
einfach dieser Wohnung zugeordnet.

Das ist mehr als Kosmetik: Ohne eigenen Zähler steckt das Gartenwasser in der Differenz
zum Hauptzähler und wird stillschweigend mitverteilt – der Mieter zahlt dann für die
Gartenbewässerung mit. Mit Zähler steht im PDF, wie viel gemeinsam verbraucht und wie
viel davon angerechnet wurde.

Ein Hinweis zur Abwassergebühr: Wasser, das in den Garten geht, landet nicht im Kanal.
Viele Gemeinden erlauben deshalb einen **angemeldeten Gartenwasserzähler**, dessen Menge
von der Schmutzwassergebühr abgezogen wird. Ein nicht angemeldeter Zähler taugt für die
interne Verteilung, spart aber keine Gebühren.

### Differenz zwischen Hauptzähler und Wohnungszählern

Der Hauptzähler zeigt fast immer mehr an als die Wohnungszähler zusammen –
Messtoleranz, Außenzapfstelle, Leitungsverluste, und kein Zähler misst exakt. Die App
zieht die Unterzähler vom Hauptzähler ab und verteilt den Rest auf beide Wohnungen:

* **nach gemessenem Verbrauch** – Voreinstellung: Wer mehr verbraucht hat, trägt auch
  mehr von der Differenz
* **nach Wohnfläche** – der gesetzliche Ersatzmaßstab (§ 556a Abs. 1 S. 1 BGB)

Wird kein eigener Zähler eingetragen, bleibt die gesamte Differenz beim Vermieter. Die
Rechnung steht vollständig im PDF: alle Zählerstände, die Summe der Unterzähler, die
Differenz, der Verteilungsmaßstab und die angerechnete Menge.

Übersteigt die Differenz 10 % des Hauptzählers, warnt die App. Das ist dann keine
Messtoleranz mehr, sondern deutet auf Leerstand oder auf Zähler hin, die zu
verschiedenen Zeitpunkten abgelesen wurden – in beiden Fällen darf die Differenz nicht
anteilig auf den Mieter verteilt werden.

**Noch offen:** Rechnungen mit einem eigenen Gültigkeitszeitraum (etwa eine Versicherung
von Juni bis Juni) und Zählerstände zu Zwischenterminen kann die App noch nicht je
Position abbilden. Zieht ein Mieter mitten im Jahr ein, müssen für dieses eine Jahr die
Beträge und Zählerstände des Mietzeitraums von Hand eingetragen werden.

### Was die App prüft

* Zählerstände, die rückwärts laufen; Unterzähler, die zusammen mehr anzeigen als
  der Hauptzähler; eine Mietwohnung, die mehr verbraucht als der Hauptzähler zeigt
* Kostenarten, die auf die Zähler einer Position verweisen, die es nicht mehr gibt
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
nebenkosten/cloud.py      Ablage in einer Google-Tabelle (für den Cloud-Betrieb)
nebenkosten/pdf.py        PDF-Erzeugung (fpdf2)
tests/                    Tests der Berechnung und der PDF-Ausgabe
```

Für ein echtes €-Zeichen im PDF wird eine Unicode-Schrift benutzt, sofern eine
gefunden wird (System-DejaVu/Liberation oder `nebenkosten/fonts/DejaVuSans.ttf`
plus `DejaVuSans-Bold.ttf`). Andernfalls schreibt das PDF „EUR".
