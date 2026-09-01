#!/usr/bin/env python3
"""Lecture de l'état partagé — remplace les appels Supabase des robots.

Depuis la migration, la base EST le dépôt : tout vit dans data/etat.json,
écrit par le dashboard via l'API GitHub. Les robots tournent dans une Action
avec le dépôt déjà cloné : ils lisent donc un simple fichier local.

Les robots ne MODIFIENT jamais data/etat.json — ils suivent ce qu'ils ont
déjà traité dans leurs propres fichiers data/*-seen.json. Sans ça, un robot
et un admin pourraient écrire en même temps et se marcher dessus.
"""
import json
import os

FICHIER = os.environ.get("ORX_ETAT", "data/etat.json")


def charger():
    """Renvoie l'état complet, ou un dictionnaire vide si le fichier manque."""
    try:
        with open(FICHIER, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{FICHIER} introuvable — le dashboard ne s'est pas encore synchronisé")
        return {}
    except json.JSONDecodeError as e:
        print(f"{FICHIER} illisible ({e}) — on ne fait rien plutôt que n'importe quoi")
        return {}


def table(nom, etat=None):
    """Renvoie une des anciennes tables Supabase, désormais rangée sous _tables."""
    e = etat if etat is not None else charger()
    return (e.get("_tables") or {}).get(nom) or []


def lire_marqueur(chemin, defaut=None):
    """Relit un fichier data/*-seen.json (ce que le robot a déjà traité)."""
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defaut if defaut is not None else {}


def ecrire_marqueur(chemin, valeur):
    os.makedirs(os.path.dirname(chemin) or ".", exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(valeur, f, ensure_ascii=False, indent=1)
