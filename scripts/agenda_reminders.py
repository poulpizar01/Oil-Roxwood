#!/usr/bin/env python3
"""Rappels d'agenda : envoie un MP Discord à chaque membre ~1h avant ses événements
(RDV, commandes, entretiens) enregistrés dans l'onglet « Mon agenda ».
Nécessite : DISCORD_BOT_TOKEN + SUPABASE_SERVICE_KEY (secrets GitHub)."""
import json, os, sys, urllib.request, urllib.error
from datetime import datetime
from zoneinfo import ZoneInfo

BOT = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "").strip() or "sb_publishable_qgN4fRX9eVdKn3SWAjtmhw_F00rlqXz"
SB = "https://prwdtdmdkhzwfyivaepw.supabase.co/rest/v1/oilroxwood_agenda"
SEEN = "data/agenda-seen.json"
UA = "DiscordBot (https://github.com/Poloveni/OilRoxwood, 1.0)"
TYPES = {"rdv": "📌 RDV", "commande": "🛒 Commande", "entretien": "🤝 Entretien", "autre": "📅 Événement"}

if not BOT:
    print("DISCORD_BOT_TOKEN manquant — rappels d'agenda ignorés")
    sys.exit(0)

now = datetime.now(ZoneInfo("Europe/Paris"))
today = now.strftime("%Y-%m-%d")

# anti-doublon : ids déjà rappelés aujourd'hui
seen = {"date": today, "ids": []}
if os.path.exists(SEEN):
    try:
        old = json.load(open(SEEN))
        if old.get("date") == today:
            seen = old
    except Exception:
        pass

req = urllib.request.Request(
    f"{SB}?date=eq.{today}&select=*",
    headers={"apikey": KEY, "Authorization": f"Bearer {KEY}", "User-Agent": UA})
rows = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())

def bot_api(path, payload):
    r = urllib.request.Request(
        f"https://discord.com/api/v10{path}",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bot {BOT}", "Content-Type": "application/json", "User-Agent": UA},
        method="POST")
    try:
        return json.loads(urllib.request.urlopen(r, timeout=30).read().decode())
    except urllib.error.HTTPError as e:
        raise Exception(f"{e.code} → {e.read().decode(errors='replace')[:200]}")

sent = 0
for ev in rows:
    if ev["id"] in seen["ids"]:
        continue
    uid = str(ev.get("uid") or "")
    if not uid.isdigit():          # pas un ID Discord (ex. accès de secours) → pas de MP possible
        continue
    try:
        h, m = map(int, str(ev.get("deb") or "0:0").split(":")[:2])
        start = now.replace(hour=h, minute=m, second=0, microsecond=0)
    except Exception:
        continue
    delta = (start - now).total_seconds() / 60
    if not (0 <= delta <= 65):     # rappel dans la fenêtre « moins d'une heure avant »
        continue
    lbl = TYPES.get(ev.get("type"), TYPES["autre"])
    msg = (f"⏰ **Rappel — dans {int(delta)} min** ({ev.get('deb')})\n"
           f"{lbl} : **{ev.get('titre') or 'événement'}**"
           + (f"\n📝 {ev['note'][:300]}" if ev.get("note") else "")
           + "\n_(depuis ton agenda Oil Roxwood)_")
    try:
        dm = bot_api("/users/@me/channels", {"recipient_id": uid})
        bot_api(f"/channels/{dm['id']}/messages", {"content": msg})
        sent += 1
        seen["ids"].append(ev["id"])
    except Exception as e:
        print(f"Rappel vers {uid} impossible : {e}")

os.makedirs("data", exist_ok=True)
json.dump(seen, open(SEEN, "w"))
print(f"{len(rows)} événement(s) aujourd'hui · {sent} rappel(s) envoyé(s)")
