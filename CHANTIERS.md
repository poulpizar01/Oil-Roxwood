# 📋 Chantiers — état au 4 septembre 2026, 2 h du matin

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
| Coffres nommés dans les logs, filtre par coffre | C-65 · C-66 |
| Recrutements comptés sur la semaine de travail, pas le lundi calendaire | C-67 |
| **La fiche RH se remplit toute seule depuis Discord** | C-68 · C-70 |
| Perdre son rôle Discord ferme la porte | C-71 · C-72 |
| 🚨 Correction du blocage total du dashboard | C-73 |
| Clé du développeur — un compte entre toujours | C-74 |
| **Le rôle Discord est la seule source des accès** | C-75 |
| 🚨 Le jeton d'écriture est enfin vérifié en écriture | C-76 |
| Responsable commercial et Assistant de direction | C-76 |
| Le jeton d'écriture passe dans « Mon profil » | C-76 |
| Saisie fluide : la page ne se redessine plus à chaque case | C-77 |
| Une seule grille de permissions | C-77 |
| Postes : +3 postes, Web Master retiré | C-77 |

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

**Envoyer les dernières versions — c'est la seule urgence.** `push.bat`.
C-73 corrige le blocage qui empêchait *tout le monde* d'ouvrir le dashboard :
tant qu'il n'est pas en ligne, l'équipe reste dehors. C-74 et C-75 partent avec.

**Les secrets GitHub Actions.** ✅ Réglé — les trois salons répondent 3/3. La
première tentative avait échoué parce que la ligne entière `BOT_TOKEN=...`
avait été collée dans le secret au lieu de la valeur seule.

**Vérifier la colonne RH de la grille des permissions.** Il y avait deux
grilles qui se contredisaient : celle des onglets disait « RH voit la Compta »,
celle des feuilles la cachait quand même. Depuis C-77 il n'en reste qu'une, et
c'est la visible qui gagne — donc le RH voit maintenant Compta et Blacklist,
parce que c'est ce qui était coché. Si ce n'est pas voulu, un clic sur la case.

**L'identifiant du rôle « Assistant de direction ».** Sa ligne existe déjà dans
Paramètres → Connexion par rôle Discord, vide. Colle l'identifiant quand le rôle
sera créé sur le serveur.

**Le compte de service GitHub.** Pour que le RH et les commerciaux puissent
écrire sans avoir ton jeton personnel : créer un compte `oilroxwood-saisie`,
l'ajouter en collaborateur du dépôt, et lui faire un jeton **classique** avec la
portée `public_repo`. Un jeton *fine-grained* ne marche pas pour un
collaborateur — il ne donne accès qu'aux dépôts que le compte possède.

**Faire le ménage.** `git rm tv.html scripts/dm_feedback.py`. Sur le VPS, le
fichier parasite `~/'ystemctl restart botoilroxwood'`, né d'une commande mal
tapée. Et dans la fiche RH, les deux lignes de test (« O » et « test »).

---

## 🛠️ À coder

**Achats de fer — vérifier sur une vraie semaine.** L'interface et le relevé
sont réparés (C-57, C-62), mais rien n'a encore été confronté à de vraies
données : le robot GitHub est à l'arrêt faute de secrets.

**La fusion par section peut écraser une saisie.** Quand deux navigateurs
enregistrent, c'est la section *entière* la plus récente qui gagne, pas la ligne.
Les tables du bot sont déjà protégées (`TABLES_BOT`) ; la section `sheets` ne
l'est pas, et c'est la cause probable de la Tablette du RH qui n'apparaissait
pas. À traiter avec la même mécanique, ligne par ligne.

**La clôture du lundi.** Le seul point de la liste d'origine jamais traité.
Thomas voulait d'abord voir comment elle fonctionne aujourd'hui, étape par
étape, avant de décider quoi automatiser.

---

## 📌 À surveiller

Le jeton d'écriture GitHub est posé dans le navigateur de Thomas : ce qui est
réglé dans Paramètres part enfin dans le dépôt. **Chaque personne qui doit
modifier quelque chose a besoin de son propre jeton** (clic sur le voyant rond
à côté d'ESPACE MEMBRE). Sans jeton, l'accès reste en lecture seule.

**Un jeton enregistré n'était pas un jeton qui écrit.** Le contrôle vérifiait la
lecture ; le dépôt étant public, il disait « valide » à des jetons sans aucun
droit. Le RH a saisi dans le vide. Depuis C-76 le contrôle interroge
`permissions.push` sur le dépôt, un bandeau rouge apparaît si les envois ne
passent pas, et le bouton **« Vérifier que j'écris vraiment »** tranche à la
demande. À faire refaire par chaque personne qui a un jeton.

Depuis C-75, **entrer et écrire sont deux choses séparées** : le rôle Discord
ouvre la porte, le jeton donne le stylo. Retirer le rôle ferme la porte à la
visite suivante ; retirer le jeton ne suffit pas, et inversement.

Ne jamais lancer le bot sur deux machines à la fois : deux instances sur le même
token se déconnectent mutuellement en boucle.
