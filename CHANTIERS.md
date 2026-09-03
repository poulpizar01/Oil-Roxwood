# 📋 Chantiers — état au 3 septembre 2026

> Les dix points notés le 2 septembre sont faits. Ce qui reste tient en deux
> listes : ce qui demande une action de Thomas, et ce qui reste à coder.

---

## ✅ Fait

| # | Sujet | Version |
|---|---|---|
| 1 | Réorganisation des pôles du menu | C-47 |
| 2 | Éligibilité — grades de la bonne semaine | C-45 |
| 3 | Facture rapide — citoyens vs employés, plafond 50 bidons | C-48 |
| 4 | Modifier une facture déjà éditée | C-49 |
| 5 | Planning — catégorie « contrat », ping 3 h avant | C-52 |
| 6 | Absences — nettoyage automatique + mémoire | C-46 |
| 7 | Quotas et multiplicateurs réglables dans Paramètres | C-44 |
| 8 | Suppressions (Suggestions, Ma to-do, Ancienneté RH) | C-50 |
| 9 | Achats Fer et Quotas commerciaux fusionnés | C-51 |
| — | Les tables annexes se synchronisent enfin | C-54 |
| — | **Le bot et le site se parlent de nouveau** | C-55 |
| — | Contrat : le menu ne liste que les commerciaux | C-56 |

Le pont Supabase est mort et enterré. Le bot lit et écrit `data/etat.json`
dans le dépôt, comme le dashboard, avec le SHA du fichier pour arbitrer les
écritures simultanées. Il sonde toutes les 20 secondes.

---

## 🔧 À faire par Thomas

**Envoyer C-56.** `push.bat` dans le dossier du dépôt.

**Régler le salon des contrats.** Paramètres → 📜 *Salon Discord des contrats*.
Tant que c'est vide, un contrat s'enregistre à l'agenda mais aucun rappel ne
part — le formulaire le signale en rouge.

**Faire le ménage.** Trois fichiers qui ne servent plus. En une commande, dans
le dossier du dépôt :

```
git rm tv.html scripts/dm_feedback.py
```

Et à la main dans le dossier du bot : supprimer `cogs\supabase_bridge.py`
(il n'est plus chargé par `main.py`, mais autant ne pas le garder).

**Les images d'éligibilité en double sur Discord.** Postées pendant la mise au
point ; le garde-fou ajouté au bot empêche que ça se reproduise, mais il faut
les effacer à la main.

**Dire si un autre exemplaire du bot tourne ailleurs** (VPS, hébergeur). Deux
instances sur le même token se déconnectent mutuellement en boucle.

---

## 🛠️ À coder

**Achats de fer — vérifier la lecture par le bot.** Le point 9 est fait côté
interface (un seul tableau, colonne « Relevé du bot »). Reste à vérifier sur
une vraie semaine que le relevé colle aux achats réels, maintenant que le pont
est vivant.

**Recrutements automatiques depuis Discord.** Renseigner un recrutement en
lisant le message d'annonce. Dépendait de la mise à jour du bot : c'est levé.

**La clôture du lundi.** Jamais traitée. Thomas voulait d'abord voir comment
elle fonctionne aujourd'hui, étape par étape, avant de décider quoi automatiser.

---

## 📌 À surveiller

Le jeton d'écriture GitHub est désormais posé dans le navigateur de Thomas :
ce qui est réglé dans Paramètres part enfin dans le dépôt. Avant le 3
septembre, rien n'était jamais parti — la table des rôles Discord et le rôle
RH étaient restés coincés dans un seul navigateur. **Chaque personne qui doit
modifier quelque chose a besoin de son propre jeton** (clic sur le voyant rond
à côté d'ESPACE MEMBRE). Sans jeton, l'accès reste en lecture seule : on voit
tout, on ne modifie rien.
