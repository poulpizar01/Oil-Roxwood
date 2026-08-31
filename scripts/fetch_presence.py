#!/usr/bin/env python3
"""Relève qui est en ligne sur le Discord d'Oil Roxwood via le WIDGET du serveur
(Paramètres serveur → Widget → activé). Aucun bot requis, le widget est public.
Nécessite : DISCORD_GUILD_ID (secret GitHub) — l'ID du serveur."""
import json, os, sys, urllib.request

GUILD = os.environ.get("DISCORD_GUILD_ID", "").strip()
OUT = "data/presence.json"
UA = "OilRoxwoodPresence (https://github.com/Poloveni/OilRoxwood, 1.0)"

if not GUILD:
    print("DISCORD_GUILD_ID manquant — présence Discord ignorée (voir SETUP-BOT.md)")
    sys.exit(0)

try:
    req = urllib.request.Request(
        f"https://discord.com/api/guilds/{GUILD}/widget.json",
        headers={"User-Agent": UA})
    d = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
except Exception as e:
    print(f"Widget inaccessible ({e}) — vérifie que le widget est ACTIVÉ dans les paramètres du serveur")
    sys.exit(0)

membres = d.get("members") or []
en_ligne = sorted({m.get("username", "") for m in membres if m.get("username")})
os.makedirs("data", exist_ok=True)
import datetime
json.dump({"maj": datetime.datetime.utcnow().isoformat() + "Z", "en_ligne": en_ligne},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(en_ligne)} membre(s) en ligne → {OUT}")
