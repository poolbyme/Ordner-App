# Ordner-App

Dieses Repository enthält zwei eigenständige Streamlit-Apps:

| App | Startdatei | Zweck |
| --- | --- | --- |
| FECG-Ordner | `app.py` | Dienstplan, Mitglieder, Chat |
| Nebenkostenabrechnung | `nebenkosten_app.py` | Betriebskostenabrechnung für Mieter, Ausgabe als PDF |

---

## Nebenkostenabrechnung

Eingeben, was im Abrechnungsjahr angefallen ist – die App verteilt die Kosten auf
den Mieter, zieht die Vorauszahlungen ab und erzeugt daraus ein fertiges PDF zum
Aushändigen.

### Starten

```bash
pip install -r requirements.txt
streamlit run nebenkosten_app.py
```

Für den Betrieb in der Streamlit Community Cloud dieselbe Datei als „Main file
path" eintragen. Die App braucht weder Google-Zugang noch Secrets; alle Eingaben
bleiben in der Sitzung und lassen sich über die Seitenleiste als JSON-Datei
sichern und wieder laden.

### Ablauf

1. **Stammdaten** – Vermieter, Mieter, Objekt, Abrechnungszeitraum, Wohnflächen,
   Personenzahl. Bei unterjährigem Ein- oder Auszug zusätzlich die Mietzeit
   eintragen, dann wird zeitanteilig nach Tagen umgelegt.
2. **Kosten** – die Positionen nach § 2 BetrKV sind vorbereitet. Eingetragen
   werden immer die **Gesamtkosten des Hauses**; die Verteilung übernimmt die App.
   Pro Zeile wählbar: Wohnfläche, Personenzahl, Wohneinheiten, Verbrauch
   (Zählerstände) oder direkte Zuordnung. In der Spalte „davon Arbeitskosten"
   den Lohnanteil erfassen – daraus entsteht die Bescheinigung nach § 35a EStG.
3. **Vorauszahlungen** – monatlicher Betrag × Monate oder die tatsächlich
   gezahlte Summe; optional der CO2-Kostenanteil des Vermieters.
4. **Abrechnung & PDF** – Ergebnis prüfen, PDF herunterladen.

### Was die App prüft

* Abrechnungszeitraum länger als 12 Monate (§ 556 Abs. 3 S. 1 BGB)
* Abrechnungsfrist: Zugang beim Mieter innerhalb von 12 Monaten nach Ende des
  Zeitraums, sonst ist die Nachforderung in der Regel ausgeschlossen
  (§ 556 Abs. 3 S. 3 BGB) – ein Guthaben bleibt trotzdem auszuzahlen
* Mieteranteile über 100 % (Fläche, Personen, Verbrauch)
* Positionen, deren Bezeichnung nach nicht umlagefähigen Kosten klingt
  (Reparatur, Instandhaltung, Verwaltung)
* Heiz-/Warmwasserkosten nach Fläche bei mehr als zwei Wohneinheiten

### Rechtliche Hinweise für das selbst bewohnte Zweifamilienhaus

* **Umlage muss vereinbart sein.** Ohne Klausel im Mietvertrag, die die
  Betriebskosten auf den Mieter überträgt, gibt es nichts umzulegen. Steht dort
  ein bestimmter Verteilerschlüssel, geht er dem gesetzlichen Flächenschlüssel
  des § 556a BGB vor.
* **Heizkosten.** Die Heizkostenverordnung verlangt sonst 50–70 % verbrauchs­-
  abhängige Abrechnung. Nach § 2 HeizkostenV gilt sie **nicht** in Gebäuden mit
  höchstens zwei Wohnungen, von denen der Vermieter eine selbst bewohnt – dort
  ist die Verteilung nach Wohnfläche zulässig, sofern der Mietvertrag nichts
  anderes vorschreibt.
* **CO2-Kosten.** Bei Erdgas- oder Ölheizung trägt der Vermieter seit 2023 nach
  dem Stufenmodell des CO2KostAufG einen Teil der CO2-Abgabe. Der Betrag lässt
  sich aus der Rechnung des Energieversorgers ermitteln und wird im Feld
  „CO2-Kostenanteil des Vermieters" abgezogen.
* **Kabelanschluss.** Seit dem 01.07.2024 sind Kabel-/Antennengebühren nicht
  mehr über die Nebenkosten umlagefähig (Ende des Nebenkostenprivilegs).
* **Nicht umlagefähig** bleiben Instandhaltung und Reparaturen, Verwaltungs- und
  Kontoführungskosten, Rücklagen sowie Rechtsschutz- und Mietausfallversicherung.

Die App erstellt ein Abrechnungsdokument, keine Rechtsberatung.

### Tests

```bash
python tests/test_nebenkosten.py     # oder: python -m pytest tests/
```

### Aufbau

```
nebenkosten_app.py        Streamlit-Oberfläche
nebenkosten/modell.py     Datenmodell, Katalog der Betriebskosten nach § 2 BetrKV
nebenkosten/berechnung.py Umlage, Zeitanteil, Saldo, Plausibilitätsprüfungen
nebenkosten/pdf.py        PDF-Erzeugung (fpdf2)
tests/                    Tests der Berechnung und der PDF-Ausgabe
```

Für ein echtes €-Zeichen im PDF wird eine Unicode-Schrift benutzt, sofern eine
gefunden wird (System-DejaVu/Liberation oder `nebenkosten/fonts/DejaVuSans.ttf`
plus `DejaVuSans-Bold.ttf`). Andernfalls schreibt das PDF „EUR".
