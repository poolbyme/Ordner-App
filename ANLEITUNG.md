# Nebenkosten-App einrichten – Schritt für Schritt

Diese Anleitung ist für jemanden geschrieben, der so etwas noch nie gemacht hat.
Alles passiert im Browser, es muss nichts installiert werden. Rechne mit einer
knappen Stunde beim ersten Mal. Danach nie wieder.

Am Ende hast du:

* eine Internetadresse, unter der die App läuft
* ein Passwort davor
* einen Speicher, der die Daten dauerhaft behält
* ein App-Symbol auf deinem Handy **und** auf dem deiner Frau

---

## Teil 1 – App ins Internet stellen (etwa 15 Minuten)

Du brauchst dein GitHub-Konto (**poolbyme**) mit Passwort.

1. Öffne im Browser **share.streamlit.io**
2. Klicke **„Continue with GitHub"** und melde dich mit deinem GitHub-Konto an.
3. GitHub fragt, ob Streamlit auf deine Projekte zugreifen darf → **„Authorize"**.
4. Oben rechts auf **„Create app"** klicken.
5. Wenn gefragt wird, woher die App kommt: die Auswahl mit **GitHub** nehmen
   („Deploy a public app from GitHub" oder ähnlich).
6. Jetzt kommt ein Formular mit drei Feldern. Trag genau das ein:

   | Feld | Was eintragen |
   | --- | --- |
   | Repository | `poolbyme/Ordner-App` |
   | Branch | `claude/nebenkostenabrechnung-app-g92wfm` |
   | Main file path | `nebenkosten_app.py` |

   **Das mittlere Feld ist wichtig.** Steht dort `main`, findet Streamlit die App
   nicht. Klick auf das Feld, dann erscheint eine Liste – such den langen Namen
   mit „nebenkostenabrechnung" darin aus.

7. Darunter kannst du die Adresse wählen, unter der die App läuft, zum Beispiel
   `nebenkosten-komjagin`. Daraus wird
   `https://nebenkosten-komjagin.streamlit.app`.
8. **Noch nicht auf Deploy klicken.** Erst Teil 2.

---

## Teil 2 – Passwort setzen (5 Minuten)

Ohne Passwort kann jeder, der die Adresse errät, die Namen, die Anschrift, deine
IBAN und die Zählerstände lesen. Das willst du nicht.

1. Im selben Formular unten auf **„Advanced settings"** klicken.
2. Es öffnet sich ein Kasten mit der Überschrift **„Secrets"**.
3. Dort hinein schreiben (Passwort natürlich selbst ausdenken):

   ```toml
   passwort = "MeinGeheimesWort2025"
   ```

   Die Anführungszeichen müssen stehen bleiben.
4. **Save** klicken.
5. Jetzt auf **„Deploy"**.
6. Es läuft ein paar Minuten Text durch – das ist normal, die App wird
   aufgebaut. Wenn oben „Your app is live" steht oder die Anmeldemaske
   erscheint, ist es fertig.
7. Passwort eingeben → die App erscheint.

**Notier dir jetzt die Adresse und das Passwort.** Beides brauchst du gleich noch.

---

## Teil 3 – Damit die Daten nicht verschwinden (etwa 20 Minuten)

Wichtig zu verstehen: Streamlit schaltet die App ab, wenn sie länger nicht
benutzt wird, und startet sie beim nächsten Aufruf neu. **Bei jedem Neustart ist
alles gelöscht, was du eingetragen hast** – es sei denn, die App schreibt in eine
Google-Tabelle. Das richten wir jetzt ein.

Du hast so etwas schon: deine andere App (FECG) benutzt bereits eine
Google-Tabelle. Die Zugangsdaten dafür kannst du wiederverwenden.

### 3a – Zugangsdaten heraussuchen

1. Gehe auf **share.streamlit.io**. Dort stehen jetzt deine Apps.
2. Klicke bei der **FECG-App** rechts auf die drei Punkte → **„Settings"**.
3. Auf den Reiter **„Secrets"**.
4. Dort steht ein langer Block, der mit `gcp_json = ` beginnt. **Markiere den
   ganzen Block und kopiere ihn** (Strg+C).
5. Füge ihn erst mal in ein leeres Textdokument ein, damit er nicht verloren geht.

### 3b – Die E-Mail-Adresse des Zugangs finden

In dem kopierten Text steht irgendwo:

```
"client_email": "irgendwas@irgendwas.iam.gserviceaccount.com"
```

**Kopier dir diese E-Mail-Adresse heraus.** Sie sieht komisch aus, ist aber
richtig – das ist der „technische Benutzer", der für die App auf die Tabelle
zugreift.

### 3c – Neue Tabelle anlegen

1. Öffne im Browser **sheets.new** – es entsteht eine leere Google-Tabelle.
2. Gib ihr oben links einen Namen, zum Beispiel **Nebenkosten Daten**.
3. Oben rechts auf **„Freigeben"** klicken.
4. Die E-Mail-Adresse aus Schritt 3b einfügen.
5. Rechts daneben **„Bearbeiter"** auswählen (nicht „Betrachter"!).
6. Das Häkchen bei „Personen benachrichtigen" wegnehmen, dann **„Senden"**.
7. Jetzt oben die **Adresse aus der Adresszeile des Browsers kopieren**. Sie
   sieht so aus:
   `https://docs.google.com/spreadsheets/d/1AbCdEf.../edit`

### 3d – Beides in die App eintragen

1. Zurück auf **share.streamlit.io**, bei der **Nebenkosten-App** die drei Punkte
   → **„Settings"** → **„Secrets"**.
2. Der Kasten enthält bisher nur die Passwortzeile. Ergänze ihn so, dass am Ende
   drei Dinge drinstehen:

   ```toml
   passwort = "MeinGeheimesWort2025"

   nebenkosten_sheet_url = "https://docs.google.com/spreadsheets/d/1AbCdEf.../edit"

   gcp_json = '''
   {
     "type": "service_account",
     ... hier der ganze Block aus Schritt 3a ...
   }
   '''
   ```

   Achte auf die **drei einfachen Anführungszeichen** vor und nach dem
   JSON-Block – die gehören dazu.
3. **Save** klicken. Die App startet von selbst neu.
4. Öffne die App und schau in die **Seitenleiste** (auf dem Handy über das Symbol
   mit den drei Strichen oben links). Unter „Wo liegen meine Daten?" muss jetzt
   **Google-Tabelle** stehen. Steht dort „Datei auf diesem Gerät", stimmt etwas
   an den Secrets nicht – dann Teil 3d noch einmal in Ruhe prüfen.

---

## Teil 4 – Aufs Handy holen (5 Minuten pro Handy)

### iPhone

1. **Safari** öffnen. Wichtig: Safari, nicht Chrome – nur Safari kann das.
2. Die Adresse der App eintippen und aufrufen.
3. Passwort eingeben.
4. Unten in der Mitte auf das **Teilen-Symbol** (Quadrat mit Pfeil nach oben).
5. In der Liste nach unten wischen bis **„Zum Home-Bildschirm"**.
6. Oben rechts **„Hinzufügen"**.
7. Fertig – das Haus-Symbol liegt jetzt auf dem Startbildschirm.

### Android

1. **Chrome** öffnen.
2. Die Adresse der App aufrufen, Passwort eingeben.
3. Oben rechts auf die **drei Punkte**.
4. **„App installieren"** oder **„Zum Startbildschirm hinzufügen"** wählen.
5. Bestätigen – fertig.

### Für deine Frau

Schick ihr per WhatsApp:

* die Adresse der App
* das Passwort

Sie macht dann genau die Schritte oben auf ihrem Handy.

**Wichtig:** Ihr arbeitet beide mit **denselben Daten**. Was sie einträgt, siehst
du und umgekehrt. Deshalb: nicht gleichzeitig eintragen, sonst überschreibt der
letzte Stand den anderen.

---

## Teil 5 – Das erste Mal ausfüllen

1. **Bereich „1 · Haus (bleibt gleich)"** – Namen, Adresse, IBAN, Wohnflächen.
   Das machst du **einmal**, danach nie wieder.
2. **„2 · Diese Abrechnung"** – Jahr auswählen, Name des Mieters, Personenzahl.
3. **„3 · Kosten"** – die Beträge von deinen Rechnungen eintragen.
4. **„4 · Zählerstände"** – Anfangs- und Endstände aller Zähler.
5. **„5 · Vorauszahlungen"** – was dein Mieter monatlich gezahlt hat.
6. **„6 · Fertige Abrechnung"** – auf **„Abrechnung abschließen und prüfen"**
   klicken. Die App sagt dir, was noch fehlt. Wenn alles grün ist: PDF
   herunterladen, ausdrucken, unterschreiben, aushändigen.

Bei jedem Bereich sitzt oben rechts ein rundes **?** – da steht, was auf der
Seite hineingehört. Und ganz oben ist eine **Suchleiste**: Tipp ein, was du
gerade in der Hand hast („Gas", „Wasser", „Grundsteuer"), dann zeigt dir die App,
wo es hingehört.

---

## Wenn etwas nicht klappt

**Die App zeigt eine Fehlermeldung statt der Anmeldemaske**
Auf share.streamlit.io bei der App die drei Punkte → „Manage app" → unten
erscheint ein schwarzes Fenster mit Text. Mach davon ein Bild und schick es mir.

**„Main file does not exist"**
Der Dateiname stimmt nicht. Drei Punkte → Settings → prüfen, dass dort
`nebenkosten_app.py` steht (klein geschrieben, mit Unterstrich).

**Nach ein paar Tagen sind die Daten weg**
Dann ist die Google-Tabelle nicht richtig verbunden. Seitenleiste → „Wo liegen
meine Daten?" – dort muss **Google-Tabelle** stehen.

**Die App braucht beim Öffnen lange oder zeigt „Zzzz"**
Normal. Streamlit legt ungenutzte Apps schlafen. Einmal auf den Knopf klicken,
nach etwa einer halben Minute ist sie wieder da.

**Passwort vergessen**
share.streamlit.io → drei Punkte → Settings → Secrets. Dort steht es im Klartext
und lässt sich ändern.

---

## Der einfache Weg ohne Internet

Wenn dir das alles zu viel ist: Die App läuft auch nur auf deinem Rechner. Dann
brauchst du kein Konto, kein Passwort und keine Google-Tabelle, und die Daten
liegen als Datei bei dir. Dafür muss der Rechner laufen, wenn du oder deine Frau
vom Handy aus draufschauen wollt, und beide Handys müssen im selben WLAN sein.
Sag Bescheid, dann schreibe ich dir dafür eine eigene Anleitung.
