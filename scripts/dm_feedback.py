#!/usr/bin/env python3
"""Envoie un MP Discord à la direction pour chaque nouvelle entrée Suggestions/Bugs.
Nécessite le secret GitHub DISCORD_BOT_TOKEN (bot partageant un serveur avec le destinataire)."""
import json, os, sys, urllib.request

BOT = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
DEST_IDS = ["186397473374208000"]  # IDs Discord des destinataires des MP
SB_URL = "https://prwdtdmdkhzwfyivaepw.supabase.co/rest/v1/oilroxwood_feedback"
SB_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "").strip() or "sb_publishable_qgN4fRX9eVdKn3SWAjtmhw_F00rlqXz"
SEEN = "data/feedback-seen.json"

if not BOT:
    print("DISCORD_BOT_TOKEN manquant — MP feedback ignorés (voir SETUP-BOT.md)")
    sys.exit(0)

last = 0
if os.path.exists(SEEN):
    try:
        last = json.load(open(SEEN)).get("last", 0)
    except Exception:
        pass

req = urllib.request.Request(
    f"{SB_URL}?id=gt.{last}&order=id.asc&select=*",
    headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"})
rows = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())

UA = "DiscordBot (https://github.com/Poloveni/OilRoxwood, 1.0)"

def bot_api(path, payload):
    r = urllib.request.Request(
        f"https://discord.com/api/v10{path}",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bot {BOT}", "Content-Type": "application/json",
                 "User-Agent": UA},
        method="POST")
    try:
        return json.loads(urllib.request.urlopen(r, timeout=30).read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        raise Exception(f"{e.code} sur {path} → {body}")

# Diagnostic : liste les serveurs où le bot est présent
try:
    g = urllib.request.Request("https://discord.com/api/v10/users/@me/guilds",
                               headers={"Authorization": f"Bot {BOT}", "User-Agent": UA})
    guilds = json.loads(urllib.request.urlopen(g, timeout=30).read().decode())
    print("Bot présent sur :", ", ".join(x["name"] for x in guilds) or "AUCUN serveur !")
except Exception as e:
    print(f"Diagnostic serveurs impossible : {e}")

sent = 0
for fb in rows:
    ico = "🐛" if fb.get("type") == "bug" else "💡"
    msg = (f"{ico} **Nouvelle remarque sur le dashboard Oil Roxwood**\n"
           f"De : **{fb.get('auteur') or 'anonyme'}**\n"
           f"> {(fb.get('texte') or '')[:1500]}\n"
           f"→ à traiter dans l'onglet Suggestions / Bugs")
    ok = False
    for uid in DEST_IDS:
        try:
            dm = bot_api("/users/@me/channels", {"recipient_id": uid})
            bot_api(f"/channels/{dm['id']}/messages", {"content": msg})
            sent += 1
            ok = True
        except Exception as e:
            print(f"MP vers {uid} impossible : {e}")
    if not ok:
        break  # échec : on s'arrête ici, cette remarque sera retentée au prochain passage
    last = max(last, fb["id"])

os.makedirs("data", exist_ok=True)
json.dump({"last": last}, open(SEEN, "w"))
print(f"{len(rows)} nouvelle(s) remarque(s) · {sent} MP envoyé(s) · dernier id : {last}")
