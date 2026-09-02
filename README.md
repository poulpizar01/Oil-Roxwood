<div align="center">

# ⛽ OIL ROXWOOD

**Compagnie pétrolière RP — serveur FlashbackFA, comté de Roxwood**

Site vitrine public · Poste de contrôle interne · Robots Discord

</div>

---

## Ce que c'est

Deux applications dans un seul dépôt statique, hébergé sur GitHub Pages.

**`index.html` — la vitrine.** Présentation de l'entreprise, organigramme, tarifs,
grille des grades, simulateur de paie et recrutement. Thème jour / nuit au choix
du visiteur. Une section **« Le dépôt en direct »** affiche la semaine en cours —
barils raffinés, effectif, commandes livrées, barre d'objectif et podium des trois
meilleurs — lue dans `data/stats-public.json`. Uniquement des agrégats : les fiches
individuelles, qui contiennent quotas et primes, ne sortent jamais du poste de
contrôle. Tant que rien n'est publié, la section et son lien de menu restent
invisibles. Sous l'organigramme, la bande **« Les visages de l'équipe »** montre les
personnes qui ont coché la case dans « Mon profil » — photo, nom, titre et présentation,
choisis par elles. Personne n'y figure par défaut.

**`admin.html` — le poste de contrôle.** L'espace membre : effectif, runs, feuilles
de production, factures, relances, bilan comptable, quotas, primes, clôture du lundi,
agenda, to-do, comptes-rendus de réunion, fiche de profil personnelle, journal d'audit et logs Discord. Connexion par Discord,
données partagées entre administrateurs, permissions par rôle, factures imprimables.

Deux pages satellites complètent l'ensemble : **`facture.html`** (facture autonome)
et **`reset.html`** (remise à zéro de secours).

**Il n'y a pas de serveur.** Le dépôt lui-même sert de base de données : tout l'état
partagé vit dans `data/etat.json`, lu publiquement et écrit via l'API GitHub. Voir
« Comment la donnée circule » plus bas.

---

## Comment c'est construit

Pas de build, pas de `node_modules`, pas de framework. Du HTML, du CSS et du
JavaScript servis tels quels. On ouvre un fichier, on modifie, on pousse.

```
├── index.html              Vitrine publique
├── admin.html              Poste de contrôle (logique complète, un seul fichier)
├── facture.html            Facture autonome
├── reset.html              Remise à zéro de secours
├── equipe.html             Redirection
│
├── assets/
│   ├── roxwood-core.css    Socle commun : couleurs, typo, textures, torche, rivets
│   ├── roxwood-ui.js       Comportements communs : torche, inclinaison, silhouette
│   ├── roxwood-site.css    Mise en page de la vitrine
│   ├── roxwood-site.js     Thème jour/nuit, hero animé, simulateur, mur de clients
│   ├── roxwood-app.css     Socle du poste de contrôle
│   └── roxwood-github.js   Moteur : identité Discord + stockage dans le dépôt
│   ├── logo.png, favicon.png, banner-og-*.jpg …
│   └── medias/             Photos et captures hors interface
│
├── data/etat.json          LA BASE : tout l'état partagé
├── data/                   Stats publiques, logs Discord, marqueurs des robots
├── backups/                Sauvegardes quotidiennes automatiques
├── scripts/                Robots Python (Discord, sauvegardes, notifications, rappels)
├── sql/                    Schéma d'origine + export de migration
├── .github/workflows/      Automatisations GitHub Actions
└── SETUP-*.md              Guides d'installation détaillés
```

Le style vit entièrement dans `assets/`. Les pages ne contiennent plus de bloc
`<style>` : pour changer une couleur, un espacement ou une police, il n'y a qu'un
seul endroit à toucher.

### Le socle graphique

Direction artistique « raffinerie brute » : noir charbon et ambre, typographie de
signalétique industrielle, plaques d'acier boulonnées, rubans de chantier. Une
lampe torche suit le curseur et révèle la rouille ; les plaques s'inclinent en 3D
sous la souris. Le vert, le rouge et le bleu acier sont **réservés aux états**
(validé, en retard, en attente) et ne servent jamais de décoration.

Le détail de la refonte et la liste complète du vocabulaire de classes sont dans
**[REFONTE.md](REFONTE.md)**.

---

## Mise en route

### 1. Le dépôt et la mise en ligne

```bash
git init -b main
git remote add origin https://github.com/poulpizar01/Oil-Roxwood.git
git add -A
git commit -m "Premier commit"
git push -u origin main
```

Puis dans **Settings → Pages** : source `Deploy from a branch`, branche `main`,
dossier `/ (root)`. Le site est en ligne une minute plus tard.

Ensuite, `push.bat` fait commit + pull + push en un double-clic.

### 2. Comment la donnée circule

Il n'y a rien à installer : **le dépôt est la base**.

| | |
|---|---|
| **Lecture** | `data/etat.json` est public. Le dashboard le lit via `raw.githubusercontent.com` — sans jeton, sans limite de débit. |
| **Écriture** | Via l'API GitHub Contents, avec le jeton personnel de chacun. Chaque enregistrement est un commit. |
| **Conflits** | Le SHA du fichier sert de jeton de version : GitHub refuse l'écriture si quelqu'un a écrit entre-temps, le dashboard refusionne et réessaie. |
| **Fraîcheur** | Relecture toutes les 45 s, au retour sur l'onglet et au retour du réseau. |
| **Historique** | Gratuit : chaque modification est un commit, `git log data/etat.json` est un journal d'audit complet. |

Les anciennes tables annexes (agenda, to-do, factures reçues, médias, suggestions,
notifications) sont rangées dans le même fichier, sous la clé `_tables`.

**Les pièces jointes n'y sont pas.** Une photo de facture pèse 60 à 80 Ko : rangée
dans `etat.json`, elle serait relue par chaque navigateur toutes les 45 secondes.
Les photos sont donc de vrais fichiers — `data/factures-recues/` et
`data/medias-notes/` — et l'état ne garde que leur chemin, ce qu'une balise
`<img src="…">` comprend tel quel. Supprimer une facture supprime sa photo. Si
l'envoi du fichier échoue, la photo est conservée dans la base comme avant plutôt
que perdue, et le journal le note.

**Le jeton d'écriture.** Sans jeton, le dashboard fonctionne en lecture seule : on
voit tout, on ne modifie rien. Chacun crée le sien — clic sur le voyant rond à côté
de « ESPACE MEMBRE » dans la barre latérale, la marche à suivre y est dépliable.
Un jeton *fine-grained*, limité à ce seul dépôt, permission **Contents : Read and write**.
Il reste dans le navigateur et n'est jamais envoyé ailleurs.

### 3. Connexion Discord

Le dashboard utilise le **flux implicite** OAuth2 : aucun secret côté client, aucun
serveur d'échange. Discord renvoie un jeton dans le fragment de l'URL, le dashboard
s'en sert une seule fois pour lire l'identité (identifiant, pseudo, avatar), puis l'oublie.

Dans [le portail Discord](https://discord.com/developers/applications) → ton application :

- **General Information** → copier l'**Application ID** dans le bloc `ROXWOOD_CFG` en haut d'`admin.html`
- **OAuth2 → Redirects** → ajouter l'adresse exacte de `admin.html`

> La première personne qui se connecte devient le compte **Direction**. Les demandes
> suivantes arrivent sur Discord et la direction crée le compte dans Paramètres.

**Ou par rôle Discord, sans validation manuelle.** Dans Paramètres → *Connexion par rôle
Discord* : l'identifiant du serveur, puis la correspondance rôle Discord → rôle dashboard.
Qui porte un rôle listé entre directement. L'ordre de la liste est une priorité — on cumule
souvent plusieurs rôles, c'est le premier qui gagne, donc Direction en haut. Le dashboard
demande alors la permission `guilds.members.read` en plus de `identify`.

> **Entrer n'est pas écrire.** Sans jeton GitHub personnel, un compte ouvert par ce chemin
> voit tout et ne modifie rien. Le rôle Discord ouvre la porte, il ne donne pas les clés du dépôt.

### 4. Les robots (facultatif)

Quatre automatisations tournent sur GitHub Actions :

| Workflow | Quand | Ce qu'il fait |
|---|---|---|
| `backup.yml` | tous les jours à 03 h UTC | copie `data/etat.json` dans `backups/` |
| `discord-logs.yml` | toutes les 15 min | récupère les logs de production et de fer depuis Discord |
| `rappels-quota.yml` | vendredi 18 h UTC | rappelle son quota à chaque retardataire **dans son ticket** |
| `diag-discord.yml` | manuel | diagnostique les accès du bot aux salons |

Ils ont besoin de ces secrets dans **Settings → Secrets and variables → Actions** :

`DISCORD_BOT_TOKEN` · `DISCORD_GUILD_ID` · `DISCORD_CHANNEL_ID` · `DISCORD_FER_CHANNEL_ID`

Les robots **lisent** `data/etat.json` mais ne le modifient jamais : ils retiennent ce
qu'ils ont traité dans leurs propres fichiers `data/*-seen.json`. Sans ça, un robot et
un admin pourraient écrire en même temps et s'écraser mutuellement.

**Comment le rappel de quota trouve un ticket.** Dans un salon de ticket, l'encadrement a
accès *par rôle* et la personne concernée *par membre*. Cette dérogation de type « membre »
est unique dans le salon : c'est elle qui désigne le propriétaire. Le robot ignore les absences
déclarées, n'écrit qu'une fois par personne et par semaine, et liste dans son journal ce qu'il
n'a pas su relier. Il se lance à blanc depuis l'onglet **Actions** (`Rappels de quota` →
*Run workflow*, case « essai à blanc » cochée) pour voir les messages avant qu'ils partent.

Détails dans **[SETUP-BOT.md](SETUP-BOT.md)** et **[SETUP-BOT-ENTREPRISE.md](SETUP-BOT-ENTREPRISE.md)**.

---

## Si tu renommes le dépôt

Le site est écrit en chemins relatifs : il fonctionne sous n'importe quel nom.
Trois choses seulement dépendent de l'adresse :

1. **`index.html`, lignes 20–21** — les deux balises `og:url` et `og:image`.
   Les robots de Discord et des réseaux sociaux n'exécutent pas de JavaScript,
   ces adresses doivent rester absolues. Le bloc est signalé par un commentaire.
2. **Le bloc `ROXWOOD_CFG`** en haut d'`admin.html` — `owner` et `repo`.
3. **Discord → OAuth2 → Redirects** — ajouter la nouvelle adresse de `admin.html`,
   sinon la connexion échoue.
4. **Les guides `SETUP-*.md`** — pour que les exemples restent justes.

Tout le reste suit automatiquement, y compris le lien envoyé en message privé
quand un accès est validé.

---

## Développer en local

Les appels à `version.json` et à GitHub échouent en `file://`. Il faut un serveur :

```bash
python -m http.server 8000
```

Puis `http://localhost:8000/` pour la vitrine et `http://localhost:8000/admin.html`
pour le poste de contrôle.

Pour tester une modification de style sans toucher aux données, ouvrir la console
et forcer l'affichage :

```js
document.getElementById('login').style.display = 'none';
document.getElementById('app').style.display = 'block';
show('overview');
```

---

## Conventions

- **Le numéro de version** vit dans `version.json`. L'incrémenter à chaque
  changement visible : le poste de contrôle affiche un bandeau de rechargement
  aux utilisateurs qui ont encore l'ancienne version en cache.
- **Les couleurs** passent toujours par les variables de `roxwood-core.css`.
  Aucune couleur en dur dans les pages.
- **Les états** (validé / en attente / en retard) portent toujours une icône et un
  libellé, jamais la couleur seule.
- **`data/` et `backups/`** sont écrits par les robots. Ne pas les modifier à la
  main : `push.bat` fait un `pull --rebase` avant chaque envoi pour récupérer leurs
  commits.

---

<div align="center">
<sub>Entreprise RP sur FlashbackFA · Site non officiel, aucun lien avec une entreprise réelle · © 2026</sub>
</div>
