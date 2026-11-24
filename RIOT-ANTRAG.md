# Riot Personal API Key beantragen

Am besten erst die Seite einrichten (README, Schritte 1–4, mit dem 24-Stunden-Key).
Dann hast du einen funktionierenden Link, den du im Antrag angeben kannst.

1. developer.riotgames.com → anmelden → **Register Product**.
2. **Personal API Key** auswählen (nicht Production).
3. Felder so ausfüllen (Riot prüft auf Englisch):

**Product Name**
```
Hawkeye LoL Account Overview
```

**Product Description**
```
A small personal website that shows my own League of Legends accounts (all on EUW) in one place: current and peak rank, win rate, my last 5 matches and champion mastery. I share the link with a few friends.

How it works: a GitHub Actions job runs every 6 hours, calls account-v1, summoner-v4, league-v4, champion-mastery-v4 and match-v5 (5 recent match IDs + details per account) for my own accounts only, and writes a static JSON file that is published with GitHub Pages. The API key is stored as a GitHub secret and is never exposed in the website. There are no user logins, no lookups of other players, no monetization and no real-time or in-game information. Total usage is roughly 50 requests every 6 hours.
```

**Product URL**
```
https://airjord4n.github.io/hawkeye/
```

**Product Game Focus**: League of Legends

4. Absenden. Die Antwort kommt als Nachricht im Developer Portal, bei deinem Produkt unter „Messages“.
5. Nach der Freigabe steht der dauerhafte Key auf der Seite des Produkts.
   Trag ihn im GitHub-Repo unter **Settings → Secrets and variables → Actions** als `RIOT_API_KEY` ein (Secret aktualisieren), fertig.

Hinweis: Der Key für deinen Chatbot gehört zu einem anderen Produkt. Riot möchte einen Key pro Produkt,
deshalb bekommt die Seite einen eigenen Antrag.
