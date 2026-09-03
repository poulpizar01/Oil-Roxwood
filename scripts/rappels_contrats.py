#!/usr/bin/env python3
"""Annonce les contrats de l'agenda dans un salon Discord, 3 h avant.

Ce que ça fait, et pourquoi c'est écrit comme ça
------------------------------------------------
Les contrats sont enregistrés dans « Mon agenda » avec le type `contrat`.
Trois heures avant l'heure de début, le robot poste un rappel dans le salon
réglé par la direction (Paramètres → Salon Discord des contrats), en
mentionnant le commercial désigné.

· Le salon vient de l'état partagé, pas d'un secret : la direction doit
  pouvoir le changer sans toucher aux réglages GitHub.
· Un contrat coché « hebdomadaire » se reconduit chaque semaine : on le
  rappelle donc aussi les semaines suivantes, à la même heure et le même
  jour, sans avoir à recréer la ligne.
· Le robot tourne toutes les 15 min. La fenêtre de tir est donc large
  (entre 2 h 45 et 3 h 15 avant), et un marqueur empêche les doublons.
· Il ne modifie jamais data/etat.json — il ne touche qu'à son marqueur.

Nécessite : DISCORD_BOT_TOKEN (secret GitHub).
"""
import json
import os
import sys
import urllib.error
import urllib.request
import unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import etat

BOT = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
SEEN = "data/contrats-seen.json"
UA = "DiscordBot (https://github.com/poulpizar01/Oil-Roxwood, 1.0)"
AVANT = timedelta(hours=3)
MARGE = timedelta(minutes=16)          # le robot passe toutes les 15 min

if not BOT:
    print("DISCORD_BOT_TOKEN manquant — rappels de contrats ignorés")
    sys.exit(0)

E = etat.charger()
salon = str(((E.get("settings") or {}).get("salonContrats")) or "").strip()
if not salon.isdigit():
    print("aucun salon de contrats réglé dans Paramètres — rien à faire")
    sys.exit(0)

users = E.get("users") or []
contrats = [e for e in etat.table("oilroxwood_agenda", E) if e.get("type") == "contrat"]
if not contrats:
    print("aucun contrat à l'agenda")
    sys.exit(0)


def norm(s):
    s = unicodedata.normalize("NFD", str(s or ""))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()


COM_ROLE = "@role"                       # sentinelle posée par le dashboard
ROLE_SERVICE_COM = "1246586673140203601"  # @Service commercial


def role_service_commercial():
    """Le rôle à mentionner pour « Service commercial ».

    Réglable dans l'état partagé (`settings.roleCommercial`) au cas où le rôle
    changerait ; sinon c'est celui du serveur d'aujourd'hui.
    """
    v = str(((E.get("settings") or {}).get("roleCommercial")) or "").strip()
    return v if v.isdigit() else ROLE_SERVICE_COM


def mention(nom):
    """Rend le texte de mention et la liste d'ids à autoriser.

    Trois cas : le service entier (mention de rôle), une personne dont on
    connaît le compte Discord (mention utilisateur), ou un nom qu'on n'a pas su
    relier — écrit en gras, sans notification, plutôt que rien du tout.
    """
    if str(nom) == COM_ROLE:
        rid = role_service_commercial()
        return f"<@&{rid}>", [], [rid]
    n = norm(nom)
    for u in users:
        if norm(u.get("user")) == n and str(u.get("did") or "").isdigit():
            return f"<@{u['did']}>", [str(u["did"])], []
    return (f"**{nom}**" if nom else ""), [], []


JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def en_francais(d):
    """strftime('%A') suit la locale du serveur, qui est en anglais sur GitHub."""
    return f"{JOURS[d.weekday()]} {d.day} {MOIS[d.month - 1]} à {d:%H:%M}"


def poster(contenu, ids, roles=()):
    req = urllib.request.Request(
        f"https://discord.com/api/v10/channels/{salon}/messages",
        data=json.dumps({"content": contenu,
                         "allowed_mentions": {"users": list(ids), "roles": list(roles)}}).encode(),
        headers={"Authorization": f"Bot {BOT}", "Content-Type": "application/json", "User-Agent": UA},
        method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()


maintenant = datetime.now(ZoneInfo("Europe/Paris"))
seen = etat.lire_marqueur(SEEN, {"faits": []})
faits = set(seen.get("faits") or [])

envoyes, ignores = 0, 0
for c in contrats:
    try:
        h, m = map(int, str(c.get("deb") or "0:0").split(":")[:2])
        jour = datetime.strptime(str(c.get("date"))[:10], "%Y-%m-%d").date()
    except Exception:
        continue

    # un contrat hebdomadaire se rejoue chaque semaine : on avance sa date
    # jusqu'à tomber sur l'occurrence à venir.
    if c.get("hebdo"):
        while jour < maintenant.date() - timedelta(days=1):
            jour += timedelta(days=7)

    debut = datetime.combine(jour, datetime.min.time(), ZoneInfo("Europe/Paris")).replace(hour=h, minute=m)
    cible = debut - AVANT
    if not (cible <= maintenant < cible + MARGE):
        continue

    cle = f'{c.get("id")}@{jour.isoformat()}'      # une occurrence = un rappel
    if cle in faits:
        ignores += 1
        continue

    qui = c.get("commercial") or ""
    men, ids, roles = mention(qui)
    corps = (
        f'📜 **Contrat dans 3 heures** — {c.get("titre") or "sans titre"}\n'
        f'🕒 {en_francais(debut)}'
        + (f'\n{"📣" if roles else "👤"} {men}' if men else "")
        + (f'\n📝 {c.get("note")}' if c.get("note") else "")
        + (f'\n🔁 Contrat hebdomadaire' if c.get("hebdo") else "")
    )
    try:
        poster(corps, ids, roles)
        faits.add(cle)
        envoyes += 1
    except urllib.error.HTTPError as e:
        print(f'contrat {c.get("id")} : envoi refusé — {e.code} {e.read().decode(errors="replace")[:150]}')
    except Exception as e:
        print(f'contrat {c.get("id")} : {e}')

# on ne garde que les 300 derniers marqueurs : au-delà, l'occurrence est passée depuis longtemps
etat.ecrire_marqueur(SEEN, {"faits": sorted(faits)[-300:]})
print(f"{envoyes} rappel(s) de contrat posté(s) · {ignores} déjà annoncé(s) · salon {salon}")
