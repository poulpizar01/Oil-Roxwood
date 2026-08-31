#!/usr/bin/env python3
"""Récupère les messages du salon Discord des achats de Fer
et les écrit dans data/fer-logs.json pour le dashboard (vue Direction).

Variables d'environnement requises :
  DISCORD_BOT_TOKEN       — token du bot (secret GitHub)
  DISCORD_FER_CHANNEL_ID  — ID du salon des achats de Fer (secret GitHub)
"""
import json, os, re, sys, urllib.request, datetime

TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
CHANNEL = os.environ.get("DISCORD_FER_CHANNEL_ID", "").strip()
OUT = "data/fer-logs.json"
MAX_KEPT = 1000

if not TOKEN or not CHANNEL:
    print("DISCORD_BOT_TOKEN ou DISCORD_FER_CHANNEL_ID manquant — étape ignorée")
    sys.exit(0)


def api(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bot {TOKEN}",
        "User-Agent": "OilRoxwoodFer (https://github.com/Poloveni/OilRoxwood, 1.0)",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def text_of(msg):
    parts = [msg.get("content") or ""]
    for e in msg.get("embeds", []):
        for k in ("title", "description"):
            if e.get(k):
                parts.append(e[k])
        for f in e.get("fields", []):
            parts.append(f.get("name", "") + " : " + f.get("value", ""))
    return "\n".join(p for p in parts if p).strip()


RE_QTE = re.compile(r"(?:x\s*)?(\d[\d\s]*)\s*(?:x\s*)?fer|fer\s*:?\s*x?\s*(\d[\d\s]*)", re.I)
RE_MONTANT = re.compile(r"(\d[\d\s.,]*)\s*\$")
RE_NOM = re.compile(r"\*\*([^*]{2,40})\*\*")


def n(s):
    return int(re.sub(r"[^\d]", "", s or "0") or 0)


def parse(msg):
    t = text_of(msg)
    if not t:
        return None
    mq = RE_QTE.search(t)
    qte = n(mq.group(1) or mq.group(2)) if mq else 0
    mm = RE_MONTANT.search(t)
    montant = n(mm.group(1)) if mm else 0
    mn = RE_NOM.search(t)
    nom = (mn.group(1).strip() if mn
           else (msg.get("author") or {}).get("global_name")
           or (msg.get("author") or {}).get("username") or "?")
    return {
        "id": msg["id"],
        "t": msg["timestamp"][:16].replace("T", " "),
        "nom": nom,
        "quantite": qte,
        "montant": montant,
        "texte": t[:300],
    }


existing = {}
if os.path.exists(OUT):
    try:
        for m in json.load(open(OUT, encoding="utf-8")).get("achats", []):
            existing[m["id"]] = m
    except Exception:
        pass

fetched, before = [], None
try:
    for _ in range(3):
        url = f"https://discord.com/api/v10/channels/{CHANNEL}/messages?limit=100"
        if before:
            url += f"&before={before}"
        batch = api(url)
        if not batch:
            break
        fetched += batch
        before = batch[-1]["id"]
        if len(batch) < 100:
            break
except urllib.error.HTTPError as e:
    raison = {401: "token invalide",
              403: "le bot n'a pas accès à ce salon — il lui faut « Voir le salon » "
                   "et « Lire l'historique des messages »",
              404: "salon introuvable — vérifier DISCORD_FER_CHANNEL_ID"}.get(e.code, f"HTTP {e.code}")
    print(f"Salon {CHANNEL} illisible : {raison}")
    sys.exit(0)   # on n'écrase pas le fichier existant et on n'interrompt pas le workflow

for msg in fetched:
    p = parse(msg)
    if p:
        existing[p["id"]] = p

achats = sorted(existing.values(), key=lambda m: m["t"], reverse=True)[:MAX_KEPT]
os.makedirs("data", exist_ok=True)
json.dump({"maj": datetime.datetime.utcnow().isoformat() + "Z", "achats": achats},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(fetched)} messages lus · {len(achats)} achats conservés → {OUT}")
