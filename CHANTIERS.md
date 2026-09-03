# 📋 Chantiers à venir — notes de Thomas

> Prises en note le 2 septembre 2026. **Rien n'est codé.** Liste de travail
> pour les prochaines sessions. Les questions en italique sont à trancher
> avant de commencer le point concerné.

---

## 1. ~~Réorganiser les pôles~~ ✅ *fait en C-47 — à valider par Thomas*

Revoir le découpage du menu (Pilotage / Gestion / Commerce / Perso / Système)
pour qu'il suive une logique métier cohérente.

*À préciser : le regroupement voulu. Par métier (RH / Prod / Commerce / Compta) ?
Par fréquence d'usage ? Par rôle ?*

---

## 2. ~~Éligibilité — grades de la bonne semaine~~ ✅ *fait en C-45*

La feuille Éligibilité affiche les grades de la semaine **précédente**. Elle doit
montrer ceux de la **nouvelle** semaine, donc tenir compte des montées et descentes
appliquées à la clôture.

---

## 3. ~~Facture rapide — citoyens vs employés~~ ✅ *fait en C-48*

- **Citoyen** : retirer le champ nom.
- **Employé** : garder le nom, mais en **menu déroulant** (choisi dans l'effectif,
  pas saisi à la main).
- **Plafond hebdomadaire de 50 par employé**, décompté au fil de la semaine :
  20 pris le lundi ⇒ 30 disponibles le jeudi, pas davantage.

**Réponse de Thomas :** 50 **bidons d'essence** par employé et par semaine. Le compteur
repart à la clôture (déjà le cas : elle efface les commandes employés).

---

## 4. ~~Modifier une facture déjà éditée~~ ✅ *fait en C-49*

Une fois la facture émise, pouvoir revenir dessus et la corriger.

**Réponse de Thomas :** tout est modifiable. Aucune mention sur la facture, mais une
trace au journal.

---

## 5. ~~Planning — catégorie « contrat »~~ ✅ *fait en C-52*

Nouvelle catégorie dans le planning pour enregistrer les **contrats hebdomadaires**,
avec un **ping du commercial 3 h avant** l'échéance.

**Réponse de Thomas :** c'est **Mon agenda**. Le ping part **dans un salon**, pas en privé.

---

## 6. ~~Absences — nettoyage automatique + mémoire~~ ✅ *fait en C-46*

- Une absence terminée se supprime toute seule.
- Mais dans **Effectif**, signaler « était absent la semaine dernière » quand c'est
  le cas — pour que la descente de grade ne tombe pas sur quelqu'un qui était en congé.

---

## 7. ~~Quotas et multiplicateurs réglables dans Paramètres~~ ✅ *fait en C-44*

Aujourd'hui le tableau `GRADES` est **écrit en dur dans le code** : quota, multiplicateur
et seuil de montée de chaque grade. Les faire passer dans Paramètres pour qu'ils se
changent sans toucher au code.

*Point d'attention : les semaines déjà closes ont été calculées avec les anciennes
valeurs. Il faudra décider si un changement s'applique rétroactivement à l'historique
(a priori non) et le dire clairement dans l'écran.*

---

## 8. ~~Suppressions~~ ✅ *fait en C-50*

Retirer trois rubriques :

- Suggestions / Bugs
- Ma to-do
- Ancienneté RH

**Réponse de Thomas :** on supprime **aussi les données**.

---

## 9. ~~Achats Fer — fusion~~ ✅ *fait en C-51 · la lecture par le bot reste à revoir avec sa mise à jour*

- Faire en sorte que le **bot lise correctement** les achats de fer.
- **Fusionner Achats Fer et Quotas commerciaux** en une seule rubrique : même domaine.
  **Réponse de Thomas :** un **seul tableau**, pas deux onglets.

---

## 10. Recrutements automatiques depuis Discord

Renseigner automatiquement les recrutements en lisant un message Discord.

> ⚠️ **Dépend d'une mise à jour du bot** — à faire avant. Son code est maintenant
> disponible (`site_bridge.py`, `site_acces.py`), il écrit encore vers Supabase.

---

## Reste des sessions précédentes

- **La clôture du lundi** — jamais traitée. Thomas voulait d'abord voir comment elle
  fonctionne aujourd'hui, étape par étape.
- **Le bot Discord** — diagnostic à faire : ce qui marche encore, ce qui écrit dans le vide.
- **`tv.html`** — toujours dans le dépôt, à supprimer.
- **⚠️ Le rôle RH n'est pas arrivé dans le dépôt.** La table des rôles Discord est
  absente de `data/etat.json` et le `_rev` n'a pas bougé depuis la migration : aucun
  enregistrement du dashboard n'est parti. Vérifier le voyant de synchro (jeton
  d'écriture) avant toute autre chose — sinon tout ce qui sera réglé demain restera
  aussi coincé dans un seul navigateur.
