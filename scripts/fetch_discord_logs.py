#!/usr/bin/env python3
"""Récupère les messages des salons de logs Discord (compte entreprise Oil Roxwood)
et les écrit dans data/discord-logs.json pour le dashboard admin.

Ce qu'on garde, et pourquoi
---------------------------
On raisonnait en NOMBRE de messages : les 500 derniers, point. Un jour chargé
en effaçait donc trois, et un jour creux gardait la semaine passée — la fenêtre
visible dépendait de l'activité, pas du calendrier. On raisonne maintenant en
JOURS : tout ce qui a moins de FENETRE_JOURS jours est conservé, quel qu'en soit
le nombre. Le plafond MAX_KEPT ne sert plus que de garde-fou contre un fichier
démesuré.

La pagination suit : on remonte le salon jusqu'à sortir de la fenêtre, au lieu
de s'arrêter à trois pages.

On conserve aussi les CHAMPS des embeds tels quels (`champs`). Les logs du
serveur RP sont des fiches structurées, pas des phrases : c'est là que vivent
le nom du coffre, l'objet, l'identifiant du joueur. Les garder permet de filtrer
dessus sans redéployer le robot à chaque nouveau besoin.

Nécessite les variables d'environnement :
  DISCORD_BOT_TOKEN   — token du bot (secret GitHub)
  DISCORD_CHANNEL_ID  — ID du salon de logs, ou plusieurs séparés par des virgules
  ORX_LOGS_JOURS      — facultatif : taille de la fenêtre en jours (3 par défaut)
"""
import datetime
import json, os, re, sys, urllib.error, urllib.request

TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
CHANNELS = [c for c in re.split(r"[,\s;/]+", os.environ.get("DISCORD_CHANNEL_ID", "").strip()) if c.isdigit()]
CHANNEL = CHANNELS[0] if CHANNELS else ""
OUT = "data/discord-logs.json"

try:
    FENETRE_JOURS = max(1, int(os.environ.get("ORX_LOGS_JOURS", "3")))
except ValueError:
    FENETRE_JOURS = 3
MAX_KEPT = 4000          # garde-fou : au-delà, le fichier devient lourd à charger
MAX_PAGES = 40           # 4000 messages par salon au maximum, si la fenêtre l'exige

if not TOKEN or not CHANNEL:
    print("DISCORD_BOT_TOKEN ou DISCORD_CHANNEL_ID manquant — voir SETUP-BOT.md")
    sys.exit(1)

LIMITE = (datetime.datetime.now(datetime.timezone.utc)
          - datetime.timedelta(days=FENETRE_JOURS))


def dans_la_fenetre(iso):
    """Un horodatage ISO de Discord est-il dans les N derniers jours ?"""
    try:
        return datetime.datetime.fromisoformat(str(iso).replace("Z", "+00:00")) >= LIMITE
    except Exception:
        return True      # date illisible : on garde, plutôt que de perdre la ligne



def api(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bot {TOKEN}",
        "User-Agent": "OilRoxwoodLogs (https://github.com/poulpizar01/Oil-Roxwood, 1.0)",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def texte_embed(e, contenu=""):
    """Le texte d'UN embed : titre, description, auteur, champs."""
    parts = [contenu or ""]
    for k in ("title", "description"):
        if e.get(k):
            parts.append(e[k])
    if (e.get("author") or {}).get("name"):
        parts.append(e["author"]["name"])
    for f in e.get("fields", []):
        parts.append(f.get("name", "") + " : " + f.get("value", ""))
    return "\n".join(p for p in parts if p).strip()


def champs_embed(e):
    """Les champs d'UN embed, en minuscules : {'playercharacter': 'John Scoupio', ...}"""
    d = {}
    for f in e.get("fields", []):
        cle = str(f.get("name", "")).strip().lower()
        if cle and cle not in d:
            d[cle] = str(f.get("value", "")).strip()[:120]
    return d


# Le nom du coffre n'est pas dans un champ : il est dans la phrase.
#   « a retire 157x Petrole Raffine du coffre de l'entreprise (Oil RoxWood) »
# On prend donc ce qui suit le mot « coffre ». Si un jour le serveur ajoute un
# champ dedie (stashName, coffre...), il est prioritaire : il sera plus propre.
CLES_COFFRE = ("stashname", "stash", "stashid", "coffre", "coffrename", "nomcoffre",
               "inventory", "inventoryname", "inventoryid", "container",
               "containername", "safe", "chest")
RE_COFFRE_PHRASE = re.compile(
    r"(?:du|dans le|dans un|au|le)\s+coffre\s+(?:de\s+)?(?:la\s+|l'|les\s+|du\s+)?([^\n]{2,60})", re.I)


def coffre_de(e, ch, t):
    for k in CLES_COFFRE:
        if ch.get(k):
            return ch[k]
    m = RE_COFFRE_PHRASE.search(t)
    if m:
        nom = m.group(1).strip(" .,;:-—")
        return nom[:60] if nom else None
    return None


NUM = r"(\d[\d\s., ]*)"
RE_QTY = re.compile(NUM + r"\s*(?:p[ée]troles?|barils?|bidons?|litres?|L\b|u\b|unit[ée]s?)", re.I)
RE_X = re.compile(r"[x×]\s*" + NUM, re.I)
# « 157x Pétrole Raffiné » : le nombre precede le x. C'est la forme utilisee par
# les logs de coffre, et aucune des deux regles precedentes ne l'attrapait —
# d'ou une colonne Quantite vide sur toute la rubrique Coffres.
RE_XPOST = re.compile(NUM + r"\s*[x×]\s*[A-Za-zÀ-ÿ]", re.I)
RE_MONEY = re.compile(NUM + r"\s*\$")
RE_NAME = re.compile(r"\*\*([^*]{2,40})\*\*")


def parse_amount(t):
    """Cherche une quantité de pétrole/barils dans le texte."""
    m = RE_XPOST.search(t) or RE_QTY.search(t) or RE_X.search(t)
    if m:
        try:
            return int(re.sub(r"[^\d]", "", m.group(1)))
        except ValueError:
            pass
    return None


def parse_type(t, ch):
    """Type normalisé, dans le vocabulaire que le dashboard connaît.

    Les anciens noms (« depot », « retrait ») ne correspondaient à aucun filtre :
    la vue attend « coffre_depot » et « coffre_retrait ». Le domaine Coffres était
    donc vide en permanence, quoi qu'il y ait dans le salon.
    """
    low = t.lower()
    item = (ch.get("itemid") or "").lower()
    if re.search(r"achat\s*fer|iron", low) or "iron" in item:
        return "achat_fer"
    if re.search(r"d[ée]p[ôo]t|deposit|d[ée]pos", low):
        return "coffre_depot"
    if re.search(r"retrait|withdraw|retir", low):
        return "coffre_retrait"
    if re.search(r"vente|vendu|sold|achat", low):
        return "vente"
    if re.search(r"v[ée]hicule|vehicle|spawn", low):
        return "vehicule_spawn"
    if re.search(r"facture|invoice", low):
        return "facture"
    if re.search(r"prise de service|on ?duty|embauche", low):
        return "prise_service"
    if re.search(r"fin de service|off ?duty|d[ée]bauche", low):
        return "fin_service"
    if re.search(r"compte entreprise|soci[ée]t[ée]|banque", low):
        return "compte_entreprise"
    if re.search(r"annonce|announce", low):
        return "annonce"
    return "autre"


def parse_name(msg, t):
    m = RE_NAME.search(t)
    if m:
        return m.group(1).strip()
    for u in msg.get("mentions", []):
        return u.get("global_name") or u.get("username")
    a = msg.get("author", {})
    if not a.get("bot"):
        return a.get("global_name") or a.get("username")
    return None


# --- messages existants : on ne garde que ceux encore dans la fenêtre ---
existing = {}
if os.path.exists(OUT):
    try:
        for m in json.load(open(OUT, encoding="utf-8")).get("messages", []):
            if dans_la_fenetre(m.get("t")):
                existing[m["id"]] = m
    except Exception:
        pass

# --- récupération : on remonte chaque salon jusqu'à sortir de la fenêtre ---
# Un salon inaccessible (403) n'interrompt plus la récupération des autres.
fetched = []
ok_salons, ko_salons = [], []
for ch in CHANNELS:
    before, pris = None, 0
    try:
        for _ in range(MAX_PAGES):
            url = f"https://discord.com/api/v10/channels/{ch}/messages?limit=100"
            if before:
                url += f"&before={before}"
            batch = api(url)
            if not batch:
                break
            # on garde ce qui est dans la fenêtre, et on s'arrête dès qu'on en sort :
            # les messages arrivent du plus récent au plus ancien.
            recents = [m for m in batch if dans_la_fenetre(m.get("timestamp"))]
            fetched += recents
            pris += len(recents)
            if len(recents) < len(batch) or len(batch) < 100:
                break
            before = batch[-1]["id"]
        ok_salons.append(f"{ch} ({pris} msg)")
    except urllib.error.HTTPError as e:
        raison = {401: "token invalide", 403: "le bot n'a pas accès à ce salon",
                  404: "salon introuvable"}.get(e.code, f"HTTP {e.code}")
        ko_salons.append(f"{ch} — {raison}")
    except Exception as e:
        ko_salons.append(f"{ch} — {e}")

print(f"Salons lus  : {len(ok_salons)}/{len(CHANNELS)}")
for s in ok_salons:
    print("   OK  ", s)
for s in ko_salons:
    print("   ÉCHEC", s)
if not ok_salons:
    print("Aucun salon accessible — vérifier que le bot est sur le serveur "
          "et qu'il a « Voir le salon » + « Lire l'historique des messages ».")

# --- une ligne par ENCART, pas par message ---
# Un seul message Discord peut porter plusieurs encarts, donc plusieurs
# mouvements de coffre. On les collait bout à bout dans un même « texte » :
# la ligne affichait deux retraits mêlés, avec une seule quantité (celle du
# premier) et un seul nom. Chaque encart devient maintenant sa propre ligne.
for msg in fetched:
    encarts = msg.get("embeds") or []
    contenu = msg.get("content") or ""
    if not encarts:
        encarts = [{}]                      # message sans encart : le contenu suffit
    for i, e in enumerate(encarts):
        t = texte_embed(e, contenu if i == 0 else "")
        if not t:
            continue
        ch = champs_embed(e)
        money_m = RE_MONEY.search(t)
        ident = msg["id"] if len(encarts) == 1 else f'{msg["id"]}-{i}'
        ligne = {
            "id": ident,
            "t": msg["timestamp"],
            "auteur": (msg.get("author") or {}).get("global_name")
                      or (msg.get("author") or {}).get("username") or "?",
            "texte": t[:400],
            # playerCharacter = le nom de la fiche RP, celui de l'effectif.
            # Sans lui on retombait sur l'auteur du message, c'est-à-dire le
            # webhook : toute la colonne « Qui » affichait « Logs - Coffre ».
            "nom": ch.get("playercharacter") or ch.get("playername") or parse_name(msg, t),
            "quantite": parse_amount(t),
            "montant": int(re.sub(r"[^\d]", "", money_m.group(1))) if money_m else None,
            "type": parse_type(t, ch),
            "salon": str(msg.get("channel_id") or ""),
        }
        coffre = coffre_de(e, ch, t)
        if coffre:
            ligne["coffre"] = coffre
        if ch:
            ligne["champs"] = ch
        existing[ident] = ligne

msgs = sorted(existing.values(), key=lambda m: m["t"], reverse=True)[:MAX_KEPT]
coffres = sorted({m["coffre"] for m in msgs if m.get("coffre")})
os.makedirs("data", exist_ok=True)
json.dump(
    {"maj": datetime.datetime.now(datetime.timezone.utc).isoformat(),
     "salon": CHANNEL, "fenetreJours": FENETRE_JOURS, "coffres": coffres, "messages": msgs},
    open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1,
)
print(f"{len(fetched)} messages dans la fenêtre de {FENETRE_JOURS} j · "
      f"{len(msgs)} conservés · {len(coffres)} coffre(s) repéré(s) → {OUT}")
if coffres:
    print("   coffres :", ", ".join(coffres[:12]))
