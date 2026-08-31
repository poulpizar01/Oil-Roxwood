# 🤖 Connecter les logs Discord au dashboard

Le site ne peut pas lire Discord directement (un webhook ne fait qu'écrire).
Un bot + GitHub Actions s'en chargent : toutes les 15 minutes, le bot lit le
salon de logs et met à jour `data/discord-logs.json`, que le dashboard affiche.

## Étape 1 — Créer le bot (5 min)

1. Va sur https://discord.com/developers/applications → **New Application** → nomme-la `Oil Roxwood Logs`.
2. Menu **Bot** → **Reset Token** → copie le token (garde-le secret !).
3. Toujours dans **Bot**, active **MESSAGE CONTENT INTENT** (obligatoire pour lire le texte des messages).

## Étape 2 — Inviter le bot sur ton serveur

1. Menu **OAuth2 → URL Generator** : coche `bot`, puis les permissions **View Channels** et **Read Message History**.
2. Ouvre l'URL générée, choisis ton serveur Discord, valide.
3. Vérifie que le bot a accès au salon de logs (droits du salon si privé).

## Étape 3 — Récupérer l'ID du salon

1. Discord → Paramètres utilisateur → **Avancés** → active le **Mode développeur**.
2. Clic droit sur le salon de logs → **Copier l'identifiant du salon**.

## Étape 4 — Ajouter les secrets sur GitHub

Sur https://github.com/Poloveni/OilRoxwood/settings/secrets/actions → **New repository secret** :

| Nom | Valeur |
|---|---|
| `DISCORD_BOT_TOKEN` | le token du bot (étape 1) |
| `DISCORD_CHANNEL_ID` | l'ID du salon (étape 3) |

## Étape 5 — Tester

Onglet **Actions** du repo → workflow **Sync logs Discord** → **Run workflow**.
Si tout est vert, `data/discord-logs.json` se remplit et l'onglet
**📡 Logs Discord** du dashboard affiche les messages, avec import des runs en un clic.

Ensuite c'est automatique : le workflow tourne toutes les 15 minutes.
