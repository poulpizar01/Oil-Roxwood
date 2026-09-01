#!/usr/bin/env python3
"""Récupère les messages du salon de logs Discord (compte entreprise Oil Roxwood)
et les écrit dans data/discord-logs.json pour le dashboard admin.

Nécessite les variables d'environnement :
  DISCORD_BOT_TOKEN   — token du bot (secret GitHub)
  DISCORD_CHANNEL_ID  — ID du salon de logs, ou plusieurs séparés par des virgules
                        (secret GitHub)
"""
import json, os, re, sys, urllib.request

TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
CHANNELS = [c for c in re.split(r"[,\s;/]+", os.environ.get("DISCORD_CHANNEL_ID", "").strip()) if c.isdigit()]
CHANNEL = CHANNELS[0] if CHANNELS else ""
OUT = "data/discord-logs.json"
MAX_KEPT = 500  # nombre max de messages conservés dans le JSON

if not TOKEN or not CHANNEL:
    print("DISCORD_BOT_TOKEN ou DISCORD_CHANNEL_ID manquant — voir SETUP-BOT.md")
    sys.exit(1)


def api(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bot {TOKEN}",
        "User-Agent": "OilRoxwoodLogs (https://github.com/poulpizar01/Oil-Roxwood, 1.0)",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def text_of(msg):
    """Concatène contenu + embeds d'un message."""
    parts = [msg.get("content") or ""]
    for e in msg.get("embeds", []):
        for k in ("title", "description"):
            if e.get(k):
                parts.append(e[k])
        if e.get("author", {}).get("name"):
            parts.append(e["author"]["name"])
        for f in e.get("fields", []):
            parts.append(f.get("name", "") + " : " + f.get("value", ""))
    return "\n".join(p for p in parts if p).strip()


NUM = r"(\d[\d\s., ]*)"
RE_QTY = re.compile(NUM + r"\s*(?:p[ée]troles?|barils?|bidons?|litres?|L\b|u\b|unit[ée]s?)", re.I)
RE_X = re.compile(r"[x×]\s*" + NUM, re.I)
RE_MONEY = re.compile(NUM + r"\s*\$")
RE_NAME = re.compile(r"\*\*([^*]{2,40})\*\*")


def parse_amount(t):
    """Cherche une quantité de pétrole/barils dans le texte."""
    m = RE_QTY.search(t) or RE_X.search(t)
    if m:
        try:
            return int(re.sub(r"[^\d]", "", m.group(1)))
        except ValueError:
            pass
    return None


def parse_type(t):
    low = t.lower()
    if re.search(r"vente|vendu|sold", low):
        return "vente"
    if re.search(r"r[ée]colt|ramass|extract|collect", low):
        return "recolte"
    if re.search(r"raffin|transform", low):
        return "raffinage"
    if re.search(r"d[ée]p[ôo]t|deposit", low):
        return "depot"
    if re.search(r"retrait|withdraw", low):
        return "retrait"
    return "autre"


def parse_name(msg, t):
    m = RE_NAME.search(t)
    if m:
        return m.group(1).strip()
    for u in msg.get("mentions", []):
        return u.get("global_name") or u.get("username")
    a = msg.get("author", {})
    if not a.get("bot"):
        return a.get("global_name") or a.get("username")
    return None


# --- messages existants (pour conserver l'historique) ---
existing = {}
if os.path.exists(OUT):
    try:
        for m in json.load(open(OUT, encoding="utf-8")).get("messages", []):
            existing[m["id"]] = m
    except Exception:
        pass

# --- récupération : jusqu'à 300 messages par salon, du plus récent au plus ancien ---
# Un salon inaccessible (403) n'interrompt plus la récupération des autres.
fetched = []
ok_salons, ko_salons = [], []
for ch in CHANNELS:
    before, pris = None, 0
    try:
        for _ in range(3):
            url = f"https://discord.com/api/v10/channels/{ch}/messages?limit=100"
            if before:
                url += f"&before={before}"
            batch = api(url)
            if not batch:
                break
            fetched += batch
            pris += len(batch)
            before = batch[-1]["id"]
            if len(batch) < 100:
                break
        ok_salons.append(f"{ch} ({pris} msg)")
    except urllib.error.HTTPError as e:
        raison = {401: "token invalide", 403: "le bot n'a pas accès à ce salon",
                  404: "salon introuvable"}.get(e.code, f"HTTP {e.code}")
        ko_salons.append(f"{ch} — {raison}")
    except Exception as e:
        ko_salons.append(f"{ch} — {e}")

print(f"Salons lus  : {len(ok_salons)}/{len(CHANNELS)}")
for s in ok_salons:
    print("   OK  ", s)
for s in ko_salons:
    print("   ÉCHEC", s)
if not ok_salons:
    print("Aucun salon accessible — vérifier que le bot est sur le serveur "
          "et qu'il a « Voir le salon » + « Lire l'historique des messages ».")

for msg in fetched:
    t = text_of(msg)
    if not t:
        continue
    money_m = RE_MONEY.search(t)
    existing[msg["id"]] = {
        "id": msg["id"],
        "t": msg["timestamp"],
        "auteur": (msg.get("author") or {}).get("global_name")
                  or (msg.get("author") or {}).get("username") or "?",
        "texte": t[:600],
        "nom": parse_name(msg, t),
        "quantite": parse_amount(t),
        "montant": int(re.sub(r"[^\d]", "", money_m.group(1))) if money_m else None,
        "type": parse_type(t),
    }

msgs = sorted(existing.values(), key=lambda m: m["t"], reverse=True)[:MAX_KEPT]
os.makedirs("data", exist_ok=True)
json.dump(
    {"maj": __import__("datetime").datetime.utcnow().isoformat() + "Z",
     "salon": CHANNEL, "messages": msgs},
    open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1,
)
print(f"{len(fetched)} messages récupérés · {len(msgs)} conservés → {OUT}")
