#!/usr/bin/env python3
"""Rappel de quota du vendredi soir — DANS LE TICKET de chacun, pas en MP.

Comment on retrouve le ticket de quelqu'un
------------------------------------------
Dans un salon de ticket, les autorisations sont posées de deux façons :
par RÔLE pour l'encadrement (direction, RH…), et par MEMBRE pour la seule
personne concernée. C'est cette dérogation de type « membre » qui identifie
le propriétaire du ticket — il n'y en a qu'une par salon.

On liste donc les salons du serveur, on garde ceux qui ont exactement une
dérogation de type membre, et on obtient une table  identifiant → salon.

Relier ce salon à un runner
---------------------------
Trois chemins, du plus sûr au plus approximatif :
  1. l'identifiant Discord enregistré sur le compte d'espace membre (users[].did)
  2. le pseudo Discord noté sur la fiche du runner (runners[].discord)
  3. le nom RP, comparé au pseudo ou au surnom sur le serveur

Ce qui n'a pas pu être relié est écrit noir sur blanc dans le journal de
l'Action : mieux vaut un runner signalé comme non trouvé qu'un rappel posté
dans le mauvais salon.

Nécessite : DISCORD_BOT_TOKEN et DISCORD_GUILD_ID (secrets GitHub).
Variables facultatives :
  ORX_RAPPELS_SEUIL   pourcentage en dessous duquel on rappelle (défaut 100)
  ORX_RAPPELS_TEST    « 1 » = on affiche sans rien envoyer
"""
import json
import os
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

import etat

BOT = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
GUILD = os.environ.get("DISCORD_GUILD_ID", "").strip()
SEUIL = float(os.environ.get("ORX_RAPPELS_SEUIL", "100"))
TEST = os.environ.get("ORX_RAPPELS_TEST", "") == "1"
SEEN = "data/rappels-seen.json"
API = "https://discord.com/api/v10"
UA = "DiscordBot (https://github.com/poulpizar01/Oil-Roxwood, 1.0)"

# Doit rester identique au tableau GRADES d'admin.html.
GRADES = [
    {"nom": "Intérimaire", "quota": 3000},
    {"nom": "Raffineur", "quota": 3000},
    {"nom": "Raffineur Confirmé", "quota": 5000},
    {"nom": "Raffineur Expert", "quota": 6500},
    {"nom": "Responsable Runner", "quota": 5000},
]

if not BOT or not GUILD:
    print("DISCORD_BOT_TOKEN ou DISCORD_GUILD_ID manquant — rappels de quota ignorés")
    sys.exit(0)


def fmt(n):
    """12345 → « 12 345 » (espace insécable fine, comme dans le dashboard)."""
    return f"{int(n):,}".replace(",", " ")


def norm(s):
    s = unicodedata.normalize("NFD", str(s or ""))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()


def api(path, payload=None):
    req = urllib.request.Request(
        API + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": f"Bot {BOT}", "Content-Type": "application/json", "User-Agent": UA},
        method="POST" if payload is not None else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
            return json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:200]
        if e.code == 429:  # limite de débit : on souffle et on retente une fois
            time.sleep(3)
            return api(path, payload)
        raise RuntimeError(f"{e.code} sur {path} → {detail}")


# ── 1. l'état du dépôt ────────────────────────────────────────────────────
E = etat.charger()
runners = E.get("runners") or []
users = E.get("users") or []
absences = E.get("absences") or []
semaine = ((E.get("settings") or {}).get("semaine")) or 0
if not runners:
    print("aucun runner dans data/etat.json — rien à faire")
    sys.exit(0)

aujourdhui = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d")
absents = {norm(a.get("nom")) for a in absences
           if str(a.get("du") or "") <= aujourdhui <= str(a.get("au") or "")}

# ── 2. qui est en retard ─────────────────────────────────────────────────
retard = []
for r in runners:
    if r.get("poste") or r.get("_ghost"):
        continue                                   # direction et fiches fantômes : pas de quota runner
    if r.get("absent") or norm(r.get("nom")) in absents:
        continue                                   # absence déclarée : on ne relance pas
    if r.get("stagiaire"):
        quota = 3000
    else:
        g = GRADES[r["grade"]] if isinstance(r.get("grade"), int) and 0 <= r["grade"] < len(GRADES) else GRADES[0]
        quota = g["quota"]
    if quota <= 0:
        continue
    barils = int(r.get("barils") or 0)
    pct = barils / quota * 100
    if pct < SEUIL:
        retard.append({"nom": r.get("nom") or "?", "discord": r.get("discord") or "",
                       "barils": barils, "quota": quota, "pct": pct,
                       "grade": (GRADES[r["grade"]]["nom"] if isinstance(r.get("grade"), int)
                                 and 0 <= r["grade"] < len(GRADES) else "")})

print(f"{len(retard)} runner(s) sous les {SEUIL:.0f} % de leur quota")
if not retard:
    sys.exit(0)

# ── 3. la carte des tickets ──────────────────────────────────────────────
try:
    salons = api(f"/guilds/{GUILD}/channels")
except RuntimeError as e:
    print(f"impossible de lire les salons : {e}")
    sys.exit(0)

tickets = {}          # identifiant Discord du propriétaire → identifiant du salon
for c in salons:
    if c.get("type") not in (0, 11, 12):           # texte, fil public, fil privé
        continue
    membres = [o for o in (c.get("permission_overwrites") or []) if str(o.get("type")) in ("1", "member")]
    if len(membres) != 1:                          # 0 = salon commun · 2+ = ce n'est pas un ticket
        continue
    tickets[str(membres[0]["id"])] = c["id"]
print(f"{len(tickets)} salon(s) ressemblant à un ticket")

# ── 4. relier chaque runner à un identifiant Discord ─────────────────────
par_pseudo = {}       # pseudo/nom connu → identifiant Discord
for u in users:
    did = str(u.get("did") or "")
    if did.isdigit():
        par_pseudo.setdefault(norm(u.get("user")), did)

# ce que Discord sait des propriétaires de tickets (pseudo + surnom sur le serveur)
noms_discord = {}
for did in tickets:
    try:
        m = api(f"/guilds/{GUILD}/members/{did}")
    except RuntimeError:
        continue
    user = m.get("user") or {}
    for n in (m.get("nick"), user.get("global_name"), user.get("username")):
        if n:
            noms_discord.setdefault(norm(n), did)


def trouver_did(r):
    for cle in (norm(r["nom"]), norm(r["discord"])):
        if cle and cle in par_pseudo:
            return par_pseudo[cle]
    for cle in (norm(r["discord"]), norm(r["nom"])):
        if cle and cle in noms_discord:
            return noms_discord[cle]
    return None


# ── 5. anti-doublon : un rappel par personne et par semaine ──────────────
seen = etat.lire_marqueur(SEEN, {"semaine": semaine, "faits": []})
if seen.get("semaine") != semaine:
    seen = {"semaine": semaine, "faits": []}
faits = set(seen.get("faits") or [])

envoyes, introuvables = 0, []
for r in retard:
    did = trouver_did(r)
    if not did:
        introuvables.append(f'{r["nom"]} (aucun identifiant Discord)')
        continue
    salon = tickets.get(did)
    if not salon:
        introuvables.append(f'{r["nom"]} (pas de ticket trouvé pour {did})')
        continue
    if did in faits:
        continue

    manque = r["quota"] - r["barils"]
    corps = (
        f'<@{did}> — **rappel de quota, semaine {semaine}**\n\n'
        f'Tu es à **{fmt(r["barils"])} barils** sur les **{fmt(r["quota"])}** attendus '
        f'({r["pct"]:.0f} %){" pour ton grade de " + r["grade"] if r["grade"] else ""}.\n'
        f'Il te manque **{fmt(manque)} barils** avant la clôture de lundi.\n\n'
        "Si tu es empêché cette semaine, dis-le ici : une absence déclarée met la descente de grade en pause."
    )

    if TEST:
        print(f'[test] {r["nom"]} → salon {salon}\n{corps}\n')
        envoyes += 1
        continue
    try:
        api(f"/channels/{salon}/messages", {"content": corps, "allowed_mentions": {"users": [did]}})
        faits.add(did)
        envoyes += 1
        time.sleep(0.6)                            # on reste poli avec la limite de débit
    except RuntimeError as e:
        introuvables.append(f'{r["nom"]} (envoi refusé : {e})')

if not TEST:
    etat.ecrire_marqueur(SEEN, {"semaine": semaine, "faits": sorted(faits)})

print(f"{envoyes} rappel(s) posté(s)")
if introuvables:
    print("non traités :")
    for x in introuvables:
        print("  ·", x)
