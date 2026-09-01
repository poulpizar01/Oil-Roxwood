#!/usr/bin/env python3
"""Publie les statistiques publiques du dépôt.

Le dashboard prépare un paquet prêt à l'emploi (_statsPub) à chaque
sauvegarde. Ce script l'extrait de data/etat.json et l'écrit dans
data/stats-public.json, que la vitrine peut lire sans authentification.
"""
import json
import os

import etat

e = etat.charger()
stats = e.get("_statsPub")

if not stats:
    print("pas encore de paquet _statsPub — un admin doit ouvrir le dashboard une fois")
    raise SystemExit(0)

os.makedirs("data", exist_ok=True)
with open("data/stats-public.json", "w", encoding="utf-8") as f:
    json.dump(stats, f, ensure_ascii=False, indent=1)

print(f"stats publiées : {stats.get('totalBarils')} barils · semaine {stats.get('semaine')}")
