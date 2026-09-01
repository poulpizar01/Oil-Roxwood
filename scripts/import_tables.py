#!/usr/bin/env python3
"""Injecte les tables annexes exportées de Supabase dans data/etat.json.

Usage :
    python scripts/import_tables.py export-tables.json

Le fichier attendu est le résultat de sql/export-tables.sql : un objet
JSON dont chaque clé est un nom de table et chaque valeur la liste de
ses lignes.

Le script ne remplace jamais une table déjà remplie sans le dire, et
écrit une copie de sécurité avant de toucher à quoi que ce soit.
"""
import json
import shutil
import sys
from datetime import datetime

CIBLE = "data/etat.json"

if len(sys.argv) < 2:
    print(__doc__)
    raise SystemExit(1)

source = sys.argv[1]

with open(source, encoding="utf-8") as f:
    brut = json.load(f)

# Supabase renvoie parfois [{"tables": {...}}] au lieu de l'objet directement
if isinstance(brut, list) and brut:
    brut = brut[0]
if isinstance(brut, dict) and "tables" in brut and isinstance(brut["tables"], dict):
    brut = brut["tables"]
if isinstance(brut, str):
    brut = json.loads(brut)

with open(CIBLE, encoding="utf-8") as f:
    etat = json.load(f)

secours = f"{CIBLE}.avant-import-{datetime.now():%Y%m%d-%H%M%S}"
shutil.copy(CIBLE, secours)
print(f"copie de sécurité : {secours}")

etat.setdefault("_tables", {})
for nom, lignes in brut.items():
    lignes = lignes or []
    if not isinstance(lignes, list):
        print(f"  {nom} : ignorée (format inattendu)")
        continue
    existant = etat["_tables"].get(nom) or []
    if existant:
        print(f"  {nom} : {len(existant)} ligne(s) déjà présente(s), {len(lignes)} importée(s) — remplacées")
    else:
        print(f"  {nom} : {len(lignes)} ligne(s) importée(s)")
    etat["_tables"][nom] = lignes

with open(CIBLE, "w", encoding="utf-8") as f:
    json.dump(etat, f, ensure_ascii=False, indent=1)

total = sum(len(v) for v in etat["_tables"].values())
print(f"\n{CIBLE} mis à jour — {total} ligne(s) au total dans _tables")
print("Vérifie le dashboard, puis commit + push.")
