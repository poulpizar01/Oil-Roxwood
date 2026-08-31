#!/usr/bin/env python3
"""Récupère le paquet de stats préparé par le dashboard (_statsPub dans l'état Supabase)
et l'écrit dans data/stats-public.json — publication automatique, sans token GitHub côté admin."""
import json, os, urllib.request

URL = "https://prwdtdmdkhzwfyivaepw.supabase.co/rest/v1/oilroxwood_etat?id=eq.2&select=data"
# clé secrète (secret GitHub SUPABASE_SERVICE_KEY) requise depuis le verrouillage des tables ;
# repli sur la clé publique tant que le verrouillage n'est pas appliqué
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "").strip() or "sb_publishable_qgN4fRX9eVdKn3SWAjtmhw_F00rlqXz"

req = urllib.request.Request(URL, headers={"apikey": KEY, "Authorization": f"Bearer {KEY}"})
with urllib.request.urlopen(req, timeout=30) as r:
    rows = json.loads(r.read().decode())

stats = rows[0]["data"].get("_statsPub") if rows else None
if stats:
    os.makedirs("data", exist_ok=True)
    json.dump(stats, open("data/stats-public.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"stats publiées : {stats.get('totalBarils')} barils · semaine {stats.get('semaine')}")
else:
    print("pas encore de paquet _statsPub — un admin doit ouvrir le dashboard une fois avec la nouvelle version")
