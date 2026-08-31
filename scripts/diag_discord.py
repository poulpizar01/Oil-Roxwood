#!/usr/bin/env python3
"""Diagnostic des accès Discord du bot.

Ne modifie rien. Répond à trois questions :
  1. Qui est ce bot et sur quels serveurs se trouve-t-il ?
  2. Pour chaque salon configuré : le bot le voit-il ?
  3. Peut-il en lire l'historique ? (permission distincte, souvent oubliée)

Variables d'environnement :
  DISCORD_BOT_TOKEN
  DISCORD_CHANNEL_ID       — un ou plusieurs identifiants séparés par des virgules
  DISCORD_FER_CHANNEL_ID   — identifiant du salon des achats de fer
"""
import json, os, re, sys, urllib.request, urllib.error

TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
if not TOKEN:
    print("DISCORD_BOT_TOKEN absent — rien à diagnostiquer.")
    sys.exit(0)

BRUT = (os.environ.get("DISCORD_CHANNEL_ID", "") + "," +
        os.environ.get("DISCORD_FER_CHANNEL_ID", ""))
SALONS = [c for c in re.split(r"[,\s;/]+", BRUT) if c.isdigit()]


def appel(chemin):
    """Retourne (code_http, donnees_ou_message)."""
    req = urllib.request.Request(
        "https://discord.com/api/v10" + chemin,
        headers={"Authorization": f"Bot {TOKEN}",
                 "User-Agent": "OilRoxwoodDiag (https://github.com/Poloveni/OilRoxwood, 1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        corps = ""
        try:
            corps = json.loads(e.read().decode()).get("message", "")
        except Exception:
            pass
        return e.code, corps
    except Exception as e:
        return 0, str(e)


print("=" * 64)
print("1. IDENTITÉ DU BOT")
print("=" * 64)
code, moi = appel("/users/@me")
if code != 200:
    print(f"   ÉCHEC ({code}) : {moi}")
    print("   → Le token est invalide ou révoqué. Régénère-le sur le portail Discord Developer.")
    sys.exit(0)
print(f"   Nom        : {moi.get('username')}  (id {moi.get('id')})")
print(f"   Est un bot : {moi.get('bot')}")

print()
print("=" * 64)
print("2. SERVEURS OÙ LE BOT EST PRÉSENT")
print("=" * 64)
code, guildes = appel("/users/@me/guilds")
if code != 200 or not isinstance(guildes, list):
    print(f"   ÉCHEC ({code}) : {guildes}")
    guildes = []
elif not guildes:
    print("   AUCUN SERVEUR. Le bot n'a jamais été invité, ou il en a été retiré.")
    print("   → Portail Discord Developer → OAuth2 → scope « bot » → inviter sur le serveur.")
else:
    for g in guildes:
        print(f"   • {g.get('name')}  (id {g.get('id')})")

print()
print("=" * 64)
print(f"3. ACCÈS AUX {len(SALONS)} SALONS CONFIGURÉS")
print("=" * 64)
ids_guildes = {g.get("id") for g in guildes} if guildes else set()
verdicts = {}
for ch in SALONS:
    code, info = appel(f"/channels/{ch}")
    if code == 200:
        nom = info.get("name", "?")
        gid = info.get("guild_id", "?")
        appartient = " (serveur où le bot est présent)" if gid in ids_guildes else " ⚠️ SERVEUR INCONNU DU BOT"
        # le salon est visible : reste à savoir s'il peut en lire l'historique
        code2, info2 = appel(f"/channels/{ch}/messages?limit=1")
        if code2 == 200:
            verdicts[ch] = "OK"
            print(f"   ✅ {ch}  #{nom}{appartient}")
            print(f"      Visible ET historique lisible.")
        elif code2 == 403:
            verdicts[ch] = "HISTORIQUE"
            print(f"   ⚠️ {ch}  #{nom}{appartient}")
            print(f"      Le bot VOIT le salon mais ne peut PAS lire l'historique.")
            print(f"      → Il lui manque « Lire l'historique des messages » sur ce salon.")
        else:
            verdicts[ch] = f"HTTP{code2}"
            print(f"   ❌ {ch}  #{nom} — lecture des messages : HTTP {code2} · {info2}")
    elif code == 403:
        verdicts[ch] = "VOIR"
        print(f"   ❌ {ch} — 403 : le bot est sur le serveur mais ne voit pas ce salon.")
        print(f"      → Il lui manque « Voir le salon ».")
    elif code == 404:
        verdicts[ch] = "INTROUVABLE"
        print(f"   ❌ {ch} — 404 : salon introuvable.")
        print(f"      → Soit l'identifiant est faux, soit le bot n'est pas sur CE serveur.")
    else:
        verdicts[ch] = f"HTTP{code}"
        print(f"   ❌ {ch} — HTTP {code} · {info}")

print()
print("=" * 64)
print("CONCLUSION")
print("=" * 64)
n_ok = sum(1 for v in verdicts.values() if v == "OK")
print(f"   {n_ok}/{len(SALONS)} salons pleinement exploitables.")
if not guildes:
    print("   ➜ CAUSE : le bot n'est sur aucun serveur. C'est le point à régler en premier.")
elif all(v == "INTROUVABLE" for v in verdicts.values()) and verdicts:
    print("   ➜ CAUSE : aucun salon n'existe sur les serveurs du bot.")
    print("     Les identifiants viennent probablement d'un AUTRE serveur Discord.")
elif all(v == "VOIR" for v in verdicts.values()) and verdicts:
    print("   ➜ CAUSE : permission « Voir le salon » manquante sur toute la catégorie.")
elif all(v == "HISTORIQUE" for v in verdicts.values()) and verdicts:
    print("   ➜ CAUSE : permission « Lire l'historique des messages » manquante.")
    print("     C'est la plus souvent oubliée : voir un salon ne suffit pas à le lire.")
elif n_ok == len(SALONS):
    print("   ➜ Tout est en ordre, la récupération des logs peut fonctionner.")
else:
    print("   ➜ Situation mixte, voir le détail salon par salon ci-dessus.")
