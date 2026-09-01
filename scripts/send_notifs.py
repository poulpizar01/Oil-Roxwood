#!/usr/bin/env python3
"""File d'attente de MP Discord.

Le dashboard dépose des messages (« accès validé », etc.) dans la table
oilroxwood_notifs, désormais rangée dans data/etat.json sous _tables.
Ce script les envoie et retient ce qu'il a déjà expédié dans son propre
fichier data/notifs-seen.json — il ne touche jamais à data/etat.json,
pour ne pas entrer en collision avec un admin en train de saisir.

Nécessite : DISCORD_BOT_TOKEN (secret GitHub).
"""
import json
import os
import sys
import urllib.error
import urllib.request

import etat

BOT = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
SEEN = "data/notifs-seen.json"
UA = "DiscordBot (https://github.com/poulpizar01/Oil-Roxwood, 2.0)"

if not BOT:
    print("DISCORD_BOT_TOKEN manquant — notifications ignorées")
    sys.exit(0)


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


envoyes = set(etat.lire_marqueur(SEEN, {}).get("ids", []))
notifs = etat.table("oilroxwood_notifs")

en_attente = [n for n in notifs
              if str(n.get("id")) not in envoyes and not n.get("done")]

envoi = 0
for nt in en_attente:
    nid = str(nt.get("id"))
    uid = str(nt.get("did") or "")
    if not uid.isdigit():
        envoyes.add(nid)          # destinataire invalide : on écarte définitivement
        continue
    try:
        dm = bot_api("/users/@me/channels", {"recipient_id": uid})
        bot_api(f"/channels/{dm['id']}/messages", {"content": (nt.get("msg") or "")[:1900]})
        envoyes.add(nid)          # marqué fait UNIQUEMENT si le MP est parti
        envoi += 1
    except Exception as e:
        print(f"MP vers {uid} impossible : {e}")

# on ne garde que les 500 derniers identifiants : le fichier ne gonfle pas
etat.ecrire_marqueur(SEEN, {"ids": sorted(envoyes)[-500:]})
print(f"{len(en_attente)} notification(s) en attente · {envoi} MP envoyé(s)")
