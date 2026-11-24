# Hawkeyes LoL-Accounts

Öffentliche Übersichtsseite für meine League-of-Legends-Accounts: Ränge, Allzeit-Bestleistung, letzte 5 Matches und Champion-Mastery.
Die Daten kommen automatisch alle 6 Stunden über die Riot-API, gehostet wird kostenlos mit GitHub Pages.

## Einrichtung (einmalig, ca. 15 Minuten)

### 1. GitHub-Repository anlegen
1. Auf github.com anmelden (oder kostenlos registrieren).
2. Oben rechts **+ → New repository**.
   - Name: `hawkeye` (der Link wird dann `https://airjord4n.github.io/hawkeye/`)
   - **Public** auswählen (GitHub Pages ist nur bei öffentlichen Repos kostenlos)
   - Haken bei „Add a README“ **nicht** setzen
3. **Create repository**, dann auf **uploading an existing file** klicken.
4. Den **Inhalt** dieses Ordners (nicht den Ordner selbst) ins Browserfenster ziehen: `accounts.json`, `README.md`, `.gitignore` und die Ordner `scripts`, `site`, `.github`.
   → **Commit changes**.

> Falls der Ordner `.github` nicht mit hochgeladen wird (Windows blendet ihn manchmal aus):
> **Add file → Create new file**, als Namen `.github/workflows/update.yml` eintippen,
> den Inhalt von `update.yml` hineinkopieren und speichern.

### 2. Riot-API-Key hinterlegen
1. Im Repository: **Settings → Secrets and variables → Actions → New repository secret**.
2. Name: `RIOT_API_KEY`, Wert: dein Key (`RGAPI-…`). Speichern.

Solange der Personal Key noch nicht freigegeben ist, kannst du hier den 24-Stunden-Development-Key eintragen.
Die Seite funktioniert dann einen Tag lang. Danach den Secret einfach durch den dauerhaften Key ersetzen.

### 3. GitHub Pages einschalten
1. **Settings → Pages**.
2. Bei **Source** „**GitHub Actions**“ auswählen.

### 4. Erstes Update starten
1. Reiter **Actions → Seite aktualisieren → Run workflow**.
2. Nach 1–2 Minuten ist die Seite unter `https://airjord4n.github.io/hawkeye/` erreichbar.
   Den Link findest du auch unter **Settings → Pages**.

## Accounts ändern
Datei `accounts.json` auf GitHub öffnen → Stift-Symbol → bearbeiten → **Commit changes**. Die Seite aktualisiert sich danach von selbst.

```json
{
  "title": "Hawkeyes LoL-Accounts",
  "owner": "Hawkeye",
  "region": "euw",
  "accounts": [
    { "riotId": "Hαωkεyε#985", "note": "Main" },
    { "riotId": "Zweitaccount#EUW", "note": "Flex", "peak": { "tier": "DIAMOND", "div": "II", "lp": 40 } }
  ]
}
```

- `riotId`: genau wie im Client, inklusive Sonderzeichen (am besten kopieren).
- `note`: kurzer Text unter dem Namen, optional.
- `peak`: optional, ein früherer Höchstrang, den Riot nicht mehr liefert. Ränge auf Englisch: IRON, BRONZE, SILVER, GOLD, PLATINUM, EMERALD, DIAMOND, MASTER, GRANDMASTER, CHALLENGER.
  Steigt dein Solo/Duo-Rang darüber, wird die Bestleistung automatisch angehoben.

## Wenn etwas nicht klappt
- **Actions** → letzten Lauf anklicken → Schritt „Daten von Riot holen“ zeigt die Fehlermeldung.
- „API-Key ungültig oder abgelaufen“ → neuen Key als Secret `RIOT_API_KEY` eintragen und den Workflow neu starten.
- „wurde nicht gefunden“ → Riot-ID in `accounts.json` prüfen (Groß-/Kleinschreibung und Sonderzeichen).

---
Hawkeyes LoL-Accounts isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
