#!/usr/bin/env python3
"""Récupère les achats de Fer postés dans le salon Discord
et les écrit dans data/fer-logs.json, que le dashboard relit.

Le format des messages
----------------------
Le serveur RP poste un embed structuré, pas une phrase :

    Achat fer
    a acheté 130x fer pour 650$
    jobId 76 · jobName Oil RoxWood · playerNetId 1637
    playerDiscord 767332887744128512
    playerName JULIO COLLINS · playerCharacter Julio Collins
    playerId 356873 · itemId iron

On lit donc les CHAMPS de l'embed plutôt que d'attraper un nom en gras dans
le texte : il n'y a pas de gras là-dedans. L'ancienne version cherchait
`**Nom**`, ne trouvait rien, et retombait sur l'auteur du message — c'est-à-dire
le webhook. Tout le monde se retrouvait attribué au même « auteur », donc la
colonne « Relevé du bot » restait vide pour chacun.

Le nom qui compte est `playerCharacter` : c'est celui de la fiche RP, donc
celui de l'effectif. `playerName` est le pseudo en majuscules, `playerDiscord`
l'identifiant — on garde les deux en secours, le dashboard sait rattraper par
identifiant si le nom a changé.

Variables d'environnement :
  DISCORD_BOT_TOKEN       — token du bot (secret GitHub) — obligatoire
  DISCORD_FER_CHANNEL_ID  — salon des achats (facultatif : valeur par défaut
                            ci-dessous, un identifiant de salon n'est pas un secret)
"""
import json, os, re, sys, urllib.request, urllib.error, datetime

SALON_DEFAUT = "1247565070423167100"      # #logs-achats-fer

TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
CHANNEL = os.environ.get("DISCORD_FER_CHANNEL_ID", "").strip() or SALON_DEFAUT
OUT = "data/fer-logs.json"
MAX_KEPT = 1000

if not TOKEN:
    print("DISCORD_BOT_TOKEN manquant — étape ignorée")
    sys.exit(0)


def api(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bot {TOKEN}",
        "User-Agent": "OilRoxwoodFer (https://github.com/poulpizar01/Oil-Roxwood, 1.0)",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def text_of(msg):
    parts = [msg.get("content") or ""]
    for e in msg.get("embeds", []):
        for k in ("title", "description"):
            if e.get(k):
                parts.append(e[k])
        for f in e.get("fields", []):
            parts.append(f.get("name", "") + " : " + f.get("value", ""))
    return "\n".join(p for p in parts if p).strip()


def champs(msg):
    """Les champs de tous les embeds, en minuscules : {'playercharacter': 'Julio Collins', …}"""
    d = {}
    for e in msg.get("embeds", []):
        for f in e.get("fields", []):
            cle = str(f.get("name", "")).strip().lower()
            if cle and cle not in d:
                d[cle] = str(f.get("value", "")).strip()
    return d


RE_QTE = re.compile(r"(?:x\s*)?(\d[\d\s]*)\s*(?:x\s*)?fer|fer\s*:?\s*x?\s*(\d[\d\s]*)", re.I)
RE_MONTANT = re.compile(r"(\d[\d\s.,]*)\s*\$")
RE_NOM_GRAS = re.compile(r"\*\*([^*]{2,40})\*\*")


def n(s):
    return int(re.sub(r"[^\d]", "", s or "0") or 0)


def est_du_fer(msg, ch, texte):
    """Le salon peut recevoir d'autres logs. On ne garde que le fer."""
    item = ch.get("itemid", "").lower()
    if item:
        return "iron" in item or "fer" in item
    titres = " ".join(str(e.get("title") or "") for e in msg.get("embeds", [])).lower()
    return "fer" in titres or "iron" in titres or "fer" in texte.lower()


def parse(msg):
    t = text_of(msg)
    if not t:
        return None
    ch = champs(msg)
    if not est_du_fer(msg, ch, t):
        return None

    mq = RE_QTE.search(t)
    qte = n(mq.group(1) or mq.group(2)) if mq else 0
    mm = RE_MONTANT.search(t)
    montant = n(mm.group(1)) if mm else 0

    # Ordre de préférence : le nom de la fiche RP (celui de l'effectif), puis
    # le pseudo en majuscules, puis un nom en gras si le format change un jour,
    # et en tout dernier l'auteur du message — qui n'est qu'un webhook.
    nom = (ch.get("playercharacter") or ch.get("playername") or "").strip()
    if not nom:
        mn = RE_NOM_GRAS.search(t)
        nom = (mn.group(1).strip() if mn
               else (msg.get("author") or {}).get("global_name")
               or (msg.get("author") or {}).get("username") or "?")

    ligne = {
        "id": msg["id"],
        "t": msg["timestamp"][:16].replace("T", " "),
        "nom": nom,
        "quantite": qte,
        "montant": montant,
        "texte": t[:300],
    }
    did = ch.get("playerdiscord", "")
    if did.isdigit():
        ligne["did"] = did          # secours : rattrape si le nom RP a changé
    return ligne


existing = {}
if os.path.exists(OUT):
    try:
        for m in json.load(open(OUT, encoding="utf-8")).get("achats", []):
            existing[m["id"]] = m
    except Exception:
        pass

fetched, before = [], None
try:
    for _ in range(3):
        url = f"https://discord.com/api/v10/channels/{CHANNEL}/messages?limit=100"
        if before:
            url += f"&before={before}"
        batch = api(url)
        if not batch:
            break
        fetched += batch
        before = batch[-1]["id"]
        if len(batch) < 100:
            break
except urllib.error.HTTPError as e:
    raison = {401: "token invalide",
              403: "le bot n'a pas accès à ce salon — il lui faut « Voir le salon » "
                   "et « Lire l'historique des messages »",
              404: "salon introuvable — vérifier DISCORD_FER_CHANNEL_ID ou le salon par défaut"}.get(e.code, f"HTTP {e.code}")
    print(f"Salon {CHANNEL} illisible : {raison}")
    sys.exit(0)   # on n'écrase pas le fichier existant et on n'interrompt pas le workflow

for msg in fetched:
    p = parse(msg)
    if p:
        existing[p["id"]] = p

achats = sorted(existing.values(), key=lambda m: m["t"], reverse=True)[:MAX_KEPT]
os.makedirs("data", exist_ok=True)
json.dump({"maj": datetime.datetime.utcnow().isoformat() + "Z", "achats": achats},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(fetched)} messages lus · {len(achats)} achats conservés → {OUT}")
