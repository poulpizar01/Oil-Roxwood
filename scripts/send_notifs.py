#!/usr/bin/env python3
"""File d'attente de MP Discord (table oilroxwood_notifs) : le dashboard y dépose des
messages (ex. « accès validé ») et ce script les envoie puis les marque comme faits.
Nécessite : DISCORD_BOT_TOKEN + SUPABASE_SERVICE_KEY (secrets GitHub)."""
import json, os, sys, urllib.request, urllib.error

BOT = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "").strip() or "sb_publishable_qgN4fRX9eVdKn3SWAjtmhw_F00rlqXz"
SB = "https://prwdtdmdkhzwfyivaepw.supabase.co/rest/v1/oilroxwood_notifs"
UA = "DiscordBot (https://github.com/Poloveni/OilRoxwood, 1.0)"

if not BOT:
    print("DISCORD_BOT_TOKEN manquant — notifications ignorées")
    sys.exit(0)

def sb(url, method="GET", payload=None):
    r = urllib.request.Request(url, method=method,
        data=json.dumps(payload).encode() if payload else None,
        headers={"apikey": KEY, "Authorization": f"Bearer {KEY}",
                 "Content-Type": "application/json", "User-Agent": UA, "Prefer": "return=minimal"})
    with urllib.request.urlopen(r, timeout=30) as resp:
        body = resp.read().decode()
        return json.loads(body) if body else None

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

rows = sb(f"{SB}?done=eq.false&order=id.asc&select=*") or []
sent = 0
for nt in rows:
    uid = str(nt.get("did") or "")
    if not uid.isdigit():
        sb(f"{SB}?id=eq.{nt['id']}", "PATCH", {"done": True})  # invalide → on écarte
        continue
    try:
        dm = bot_api("/users/@me/channels", {"recipient_id": uid})
        bot_api(f"/channels/{dm['id']}/messages", {"content": (nt.get("msg") or "")[:1900]})
        sb(f"{SB}?id=eq.{nt['id']}", "PATCH", {"done": True})  # marqué fait UNIQUEMENT si envoyé
        sent += 1
    except Exception as e:
        print(f"MP vers {uid} impossible : {e}")

print(f"{len(rows)} notification(s) en attente · {sent} MP envoyé(s)")
