# 📋 Chantiers — état au 3 septembre 2026, minuit

> Les dix points du 2 septembre sont faits. Le bot et le site se parlent enfin,
> et les rappels de contrat partent. Ce qui reste tient en deux listes.

---

## ⚠️ À savoir avant toute chose : où vit le bot

**Le bot tourne sur un VPS, pas sur le PC.**

| | |
|---|---|
| Machine | `root@bot-oil-roxwood` · `178.104.236.198` |
| Dossier | `/root/Bot/` |
| Service | `botoilroxwood.service` |
| Redémarrer | `systemctl restart botoilroxwood` |
| Lire le journal | `journalctl -u botoilroxwood -n 30 --no-pager` |
| Le `.env` lu par `config.py` | `/root/Bot/.env` (pas celui de `cogs/`) |

`C:\Users\thoma\OneDrive\Bureau\BOT` **n'est pas le bot** — c'est une copie de
travail. Le bot ne l'a jamais lue. Toute modification se transfère :

```
scp "C:\Users\thoma\OneDrive\Bureau\BOT\cogs\fichier.py" root@178.104.236.198:/root/Bot/cogs/
```

puis `systemctl restart botoilroxwood`. Cette confusion a coûté une soirée
entière : on installait des correctifs dans un dossier que rien ne lisait.

**Deux réflexes après un échec de démarrage.** `python3 -m py_compile fichier.py`
avant de redémarrer, et si systemd refuse de repartir en disant *« Start request
repeated too quickly »*, `systemctl reset-failed botoilroxwood` débloque le
compteur.

---

## ✅ Fait

| Sujet | Version |
|---|---|
| Réorganisation des pôles du menu | C-47 |
| Éligibilité — grades de la bonne semaine | C-45 |
| Facture rapide — citoyens vs employés, plafond 50 bidons | C-48 |
| Modifier une facture déjà éditée | C-49 |
| Planning — catégorie « contrat » | C-52 |
| Absences — nettoyage automatique + mémoire | C-46 |
| Quotas et multiplicateurs réglables | C-44 |
| Suppressions (Suggestions, to-do, Ancienneté RH) | C-50 |
| Achats Fer et Quotas commerciaux fusionnés | C-51 |
| Les tables annexes se synchronisent | C-54 |
| **Le bot et le site se parlent de nouveau** | C-55 |
| Contrat : le service commercial par défaut | C-56 · C-57 |
| Fer relevé automatiquement, colonne manuelle retirée | C-57 |
| Rubrique Runs supprimée | C-58 |
| Les six feuilles deviennent six rubriques | C-59 |
| Le logo ouvre la vitrine | C-60 |
| Logs sur 3 jours, filtre par coffre | C-61 · C-62 |
| Le contrat annonce l'heure de son rappel | C-63 |
| **Les rappels de contrat passent au bot Discord** | C-64 |

### Pourquoi les rappels ont changé de mains (C-64)

GitHub met les tâches planifiées des dépôts publics en file d'attente. Le
workflow demandait à passer toutes les 15 minutes ; ses horaires réels étaient
02:10, 06:18, 11:01, 15:32, 19:11, 21:48 — **toutes les 3 à 4 heures**. Un
rappel calé 3 h avant un contrat n'avait aucune chance de tomber au bon moment.

Le bot, lui, est connecté en permanence et relit le dépôt sans arrêt : il
vérifie les contrats **chaque minute**. Il n'attend plus un créneau, il regarde
un état — *« ce contrat commence dans moins de 3 h et n'a pas encore commencé ?
alors j'annonce »*. `scripts/rappels_contrats.py` est en veille pour éviter les
doublons (`ORX_RAPPELS_CONTRATS=1` le réveille).

Contrepartie : **si le bot est éteint, aucun rappel ne part.** Au redémarrage il
rattrape tout contrat encore dans sa fenêtre de 3 h.

---

## 🔧 À faire par Thomas

**Les secrets GitHub Actions.** C'est le dernier vrai blocage.
`data/discord-logs.json` est figé au **31 août** : le workflow tourne bien (runs
verts) mais le script sort aussitôt faute de secrets, et le run reste vert. Donc
la rubrique Logs Discord et le relevé du fer sont morts. Dans **Settings →
Secrets and variables → Actions** :

| Nom | Valeur |
|---|---|
| `DISCORD_BOT_TOKEN` | le token du bot, depuis `/root/Bot/.env` |
| `DISCORD_CHANNEL_ID` | `1245400913066066099,1245400913473179729,1245400913473179732` |
| `DISCORD_GUILD_ID` | `1245400912835510283` |

Puis **Actions → Sync logs Discord → Run workflow**, et vérifier que l'étape
*Récupérer les messages du salon* annonce des messages au lieu de « manquant ».

**Envoyer les dernières versions.** `push.bat` — C-64 attend dans le dossier.

**Faire le ménage.** `git rm tv.html scripts/dm_feedback.py`. Et sur le VPS, le
fichier parasite `~/'ystemctl restart botoilroxwood'`, né d'une commande mal
tapée.

---

## 🛠️ À coder

**Achats de fer — vérifier sur une vraie semaine.** L'interface et le relevé
sont réparés (C-57, C-62), mais rien n'a encore été confronté à de vraies
données : le robot GitHub est à l'arrêt faute de secrets.

**Recrutements automatiques depuis Discord.** Dépendait de la mise à jour du
bot. C'est levé.

**La clôture du lundi.** Le seul point de la liste d'origine jamais traité.
Thomas voulait d'abord voir comment elle fonctionne aujourd'hui, étape par
étape, avant de décider quoi automatiser.

---

## 📌 À surveiller

Le jeton d'écriture GitHub est posé dans le navigateur de Thomas : ce qui est
réglé dans Paramètres part enfin dans le dépôt. **Chaque personne qui doit
modifier quelque chose a besoin de son propre jeton** (clic sur le voyant rond
à côté d'ESPACE MEMBRE). Sans jeton, l'accès reste en lecture seule.

Ne jamais lancer le bot sur deux machines à la fois : deux instances sur le même
token se déconnectent mutuellement en boucle.
