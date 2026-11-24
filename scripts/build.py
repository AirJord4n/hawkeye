#!/usr/bin/env python3
"""
Holt fuer alle Accounts aus accounts.json Level, Raenge, letzte Matches und
Champion-Mastery ueber die Riot-API und schreibt site/data.json.

Laeuft automatisch per GitHub Actions (siehe .github/workflows/update.yml).
Lokal testen:  set RIOT_API_KEY=RGAPI-...   dann   py scripts/build.py
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "accounts.json")
OUT = os.path.join(ROOT, "site", "data.json")

# Region: (Plattform, Cluster fuer Account-API, Cluster fuer Match-API)
REGIONS = {
    "euw": ("euw1", "europe", "europe"), "eune": ("eun1", "europe", "europe"),
    "tr": ("tr1", "europe", "europe"), "ru": ("ru", "europe", "europe"), "me": ("me1", "europe", "europe"),
    "na": ("na1", "americas", "americas"), "br": ("br1", "americas", "americas"),
    "lan": ("la1", "americas", "americas"), "las": ("la2", "americas", "americas"),
    "kr": ("kr", "asia", "asia"), "jp": ("jp1", "asia", "asia"),
    "oce": ("oc1", "asia", "sea"), "sg": ("sg2", "asia", "sea"), "tw": ("tw2", "asia", "sea"), "vn": ("vn2", "asia", "sea"),
}
QUEUES = {"RANKED_SOLO_5x5": "solo", "RANKED_FLEX_SR": "flex"}
TIERS = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"]
DIVS = ["IV", "III", "II", "I"]


class RiotError(Exception):
    pass


def get(url, key=None, tries=6, quiet404=True):
    headers = {"User-Agent": "lol-uebersicht/1.0"}
    if key:
        headers["X-Riot-Token"] = key
    for _ in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = int(e.headers.get("Retry-After", "5"))
                print(f"  Rate-Limit, warte {wait} s ...")
                time.sleep(wait)
                continue
            if e.code == 404:
                return None
            if e.code in (401, 403):
                raise RiotError("API-Key ungueltig oder abgelaufen.")
            if e.code >= 500:
                time.sleep(3)
                continue
            raise RiotError(f"HTTP {e.code} bei {url.split('?')[0]}")
        except urllib.error.URLError as e:
            time.sleep(3)
            last = e
    raise RiotError(f"Keine Antwort von {url.split('?')[0]}")


def score(r):
    if not r or r.get("tier") not in TIERS:
        return -1
    t = r["tier"]
    div = 0 if t in ("MASTER", "GRANDMASTER", "CHALLENGER") else DIVS.index(r.get("div", "IV")) if r.get("div") in DIVS else 0
    return TIERS.index(t) * 1000 + div * 100 + int(r.get("lp", 0))


def previous_data():
    """Letzte veroeffentlichte data.json holen, damit Bestleistungen erhalten bleiben."""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" in repo:
        owner, name = repo.split("/", 1)
        base = f"https://{owner.lower()}.github.io" + ("" if name.lower() == f"{owner.lower()}.github.io" else f"/{name}")
        try:
            data = get(f"{base}/data.json?nocache={int(time.time())}")
            if data:
                return data
        except Exception:
            pass
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            return json.load(f)
    return {}


MATCH_CACHE = {}
BUDGET = {"left": int(os.environ.get("SEASON_BUDGET", "600"))}  # max. neue Match-Details pro Lauf


def match(mbase, mid, key):
    if mid not in MATCH_CACHE:
        MATCH_CACHE[mid] = get(f"{mbase}/{mid}", key)
    return MATCH_CACHE[mid]


def season_stats(puuid, mbase, key, start, prev_season):
    """Zaehlt alle Spiele seit Saisonstart pro Champion. Bereits gezaehlte Matches
    werden aus dem letzten Lauf uebernommen, damit nur neue Spiele abgefragt werden."""
    start_ts = int(datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp())
    old = prev_season if prev_season and prev_season.get("start") == start else {}
    seen = set(old.get("ids", []))
    champs = {k: list(v) for k, v in (old.get("champs") or {}).items()}
    ids, page = [], 0
    while True:
        batch = get(f"{mbase}/by-puuid/{puuid}/ids?startTime={start_ts}&start={page}&count=100", key) or []
        ids += batch
        if len(batch) < 100:
            break
        page += 100
    pending = [m for m in ids if m not in seen]
    for mid in pending:
        if BUDGET["left"] <= 0 and mid not in MATCH_CACHE:
            break
        if mid not in MATCH_CACHE:
            BUDGET["left"] -= 1
        info = (match(mbase, mid, key) or {}).get("info", {})
        me = next((p for p in info.get("participants", []) if p.get("puuid") == puuid), None)
        seen.add(mid)
        if not me:
            continue
        c = champs.setdefault(str(me.get("championId")), [0, 0])
        c[0] += 1
        c[1] += 1 if me.get("win") else 0
    done = all(m in seen for m in ids)
    return {"start": start, "ids": sorted(seen), "champs": champs, "done": done}


def fetch(acc_cfg, region, key, champs, season_start, prev_acc):
    platform, cluster, mcluster = REGIONS[region]
    rid = acc_cfg["riotId"]
    name, tag = rid.rsplit("#", 1)
    q = lambda s: urllib.parse.quote(s.strip(), safe="")
    acc = get(f"https://{cluster}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{q(name)}/{q(tag)}", key)
    if not acc:
        raise RiotError(f"{rid} wurde nicht gefunden")
    puuid = acc["puuid"]
    base = f"https://{platform}.api.riotgames.com/lol"
    summ = get(f"{base}/summoner/v4/summoners/by-puuid/{puuid}", key) or {}
    leagues = get(f"{base}/league/v4/entries/by-puuid/{puuid}", key) or []
    mastery = get(f"{base}/champion-mastery/v4/champion-masteries/by-puuid/{puuid}", key) or []

    def champ(cid):
        c = champs.get(cid)
        return {"c": c["id"], "n": c["name"]} if c else {"c": "", "n": f"Champion {cid}"}

    out = {
        "riotId": f"{acc.get('gameName') or name}#{acc.get('tagLine') or tag}",
        "region": region,
        "note": acc_cfg.get("note", ""),
        "level": summ.get("summonerLevel"),
        "icon": summ.get("profileIconId"),
        "solo": None,
        "flex": None,
    }
    for e in leagues:
        k = QUEUES.get(e.get("queueType"))
        if k:
            out[k] = {"tier": e["tier"], "div": e.get("rank", ""), "lp": e.get("leaguePoints", 0),
                      "w": e.get("wins", 0), "l": e.get("losses", 0)}
    out["mastery"] = [{**champ(m["championId"]), "lv": m.get("championLevel", 0), "pts": m.get("championPoints", 0),
                       "last": m.get("lastPlayTime", 0)} for m in mastery]

    out["recent"] = []
    mbase = f"https://{mcluster}.api.riotgames.com/lol/match/v5/matches"
    for mid in get(f"{mbase}/by-puuid/{puuid}/ids?start=0&count=5", key) or []:
        info = (match(mbase, mid, key) or {}).get("info", {})
        me = next((p for p in info.get("participants", []) if p.get("puuid") == puuid), None)
        if not me:
            continue
        out["recent"].append({**champ(me.get("championId")), "win": bool(me.get("win")),
                              "k": me.get("kills", 0), "d": me.get("deaths", 0), "a": me.get("assists", 0),
                              "q": info.get("queueId", 0),
                              "t": info.get("gameEndTimestamp") or info.get("gameCreation", 0)})

    # Meistgespielte Champions der aktuellen Season
    s = season_stats(puuid, mbase, key, season_start, (prev_acc or {}).get("season"))
    out["season"] = s
    games = sum(v[0] for v in s["champs"].values())
    top = sorted(s["champs"].items(), key=lambda kv: (-kv[1][0], -kv[1][1]))[:3]
    out["seasonGames"] = games
    out["seasonDone"] = s["done"]
    out["seasonTop"] = [{**champ(int(cid)), "games": g, "wins": w} for cid, (g, w) in top]
    return out


def main():
    key = os.environ.get("RIOT_API_KEY", "").strip()
    if not key:
        sys.exit("RIOT_API_KEY fehlt (bei GitHub: Settings > Secrets and variables > Actions).")
    with open(CONFIG, encoding="utf-8") as f:
        cfg = json.load(f)
    region = cfg.get("region", "euw").lower()
    season_start = cfg.get("seasonStart", "2026-01-08")

    versions = get("https://ddragon.leagueoflegends.com/api/versions.json")
    ver = versions[0]
    raw = get(f"https://ddragon.leagueoflegends.com/cdn/{ver}/data/de_DE/champion.json")["data"]
    champs = {int(c["key"]): {"id": c["id"], "name": c["name"]} for c in raw.values()}

    prev = {a["riotId"].lower(): a for a in previous_data().get("accounts", []) if a.get("riotId")}
    accounts, errors = [], []
    for a in cfg.get("accounts", []):
        rid = a.get("riotId", "")
        reg = a.get("region", region).lower()
        if "#" not in rid or reg not in REGIONS:
            errors.append(f"{rid}: ungueltige Riot-ID oder Region")
            continue
        print(f"Hole {rid} ...")
        try:
            acc = fetch(a, reg, key, champs, season_start, prev.get(rid.lower()))
        except RiotError as e:
            print(f"  Fehler: {e}")
            errors.append(f"{rid}: {e}")
            old = prev.get(rid.lower())
            if old:
                accounts.append(old)  # alte Daten behalten statt Account verlieren
            if "API-Key" in str(e):
                break
            continue
        # Bestleistung: Maximum aus Konfiguration, letzter Veroeffentlichung und aktuellem Solo/Duo-Rang
        candidates = [a.get("peak"), (prev.get(acc["riotId"].lower()) or {}).get("peak"), acc["solo"]]
        best = max((c for c in candidates if c), key=score, default=None)
        acc["peak"] = {"tier": best["tier"], "div": best.get("div", ""), "lp": best.get("lp", 0)} if best else None
        accounts.append(acc)

    if not accounts:
        sys.exit("Keine Daten geholt: " + "; ".join(errors))
    data = {"title": cfg.get("title", "Meine LoL-Accounts"), "owner": cfg.get("owner", ""),
            "ddragon": ver, "seasonStart": season_start, "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "accounts": accounts}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Fertig: {len(accounts)} Account(s) -> site/data.json")
    if errors:
        print("Probleme:", "; ".join(errors))


if __name__ == "__main__":
    main()
