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
du visiteur.

**`admin.html` — le poste de contrôle.** L'espace membre : effectif, runs, feuilles
de production, factures, relances, bilan comptable, quotas, primes, clôture du lundi,
agenda, to-do, journal d'audit et logs Discord en direct. Connexion par Discord,
données synchronisées en temps réel entre administrateurs via Supabase, permissions
par rôle, factures imprimables.

Trois pages satellites complètent l'ensemble : **`tv.html`** (affichage plein écran
pour l'écran du dépôt), **`facture.html`** (facture autonome) et **`reset.html`**
(remise à zéro de secours).

---

## Comment c'est construit

Pas de build, pas de `node_modules`, pas de framework. Du HTML, du CSS et du
JavaScript servis tels quels. On ouvre un fichier, on modifie, on pousse.

```
├── index.html              Vitrine publique
├── admin.html              Poste de contrôle (logique complète, un seul fichier)
├── tv.html                 Affichage dépôt
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
│   ├── logo.png, favicon.png, banner-og-*.jpg …
│   └── medias/             Photos et captures hors interface
│
├── data/                   État publié et historiques (écrits par les robots)
├── backups/                Sauvegardes quotidiennes automatiques
├── scripts/                Robots Python (Discord, sauvegardes, notifications)
├── sql/                    Schéma des tables Supabase
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

### 2. Supabase (base de données partagée)

Créer un projet sur [supabase.com](https://supabase.com), puis exécuter le SQL de
**[SETUP-SUPABASE.md](SETUP-SUPABASE.md)** dans l'éditeur SQL. Cela crée les tables :

`oilroxwood_etat` · `oilroxwood_agenda` · `oilroxwood_notifs` · `oilroxwood_frecues`
`oilroxwood_todo` · `oilroxwood_media` · `oilroxwood_demandes` · `oilroxwood_feedback`

Reporter l'URL du projet et la clé publique (`anon`) dans `admin.html`, section
`SYNCHRO SUPABASE`. Cette clé est publique par conception : les droits sont gérés
par les politiques RLS côté Supabase.

### 3. Connexion Discord

Suivre **[SETUP-DISCORD-LOGIN.md](SETUP-DISCORD-LOGIN.md)**. Dans Supabase →
Authentication → Providers → Discord, renseigner l'identifiant et le secret de
l'application Discord, puis ajouter l'adresse de `admin.html` aux **Redirect URLs**
autorisées.

> La première personne qui se connecte devient le compte **Direction**. Les accès
> suivants se valident depuis l'onglet « Demandes d'accès ».

### 4. Les robots (facultatif)

Trois automatisations tournent sur GitHub Actions :

| Workflow | Quand | Ce qu'il fait |
|---|---|---|
| `backup.yml` | tous les jours à 03 h UTC | sauvegarde l'état Supabase dans `backups/` |
| `discord-logs.yml` | toutes les 15 min | récupère les logs de production et de fer depuis Discord |
| `diag-discord.yml` | manuel | diagnostique les accès du bot aux salons |

Ils ont besoin de ces secrets dans **Settings → Secrets and variables → Actions** :

`SUPABASE_SERVICE_KEY` · `DISCORD_BOT_TOKEN` · `DISCORD_GUILD_ID`
`DISCORD_CHANNEL_ID` · `DISCORD_FER_CHANNEL_ID`

Détails dans **[SETUP-BOT.md](SETUP-BOT.md)** et **[SETUP-BOT-ENTREPRISE.md](SETUP-BOT-ENTREPRISE.md)**.

---

## Si tu renommes le dépôt

Le site est écrit en chemins relatifs : il fonctionne sous n'importe quel nom.
Trois choses seulement dépendent de l'adresse :

1. **`index.html`, lignes 20–21** — les deux balises `og:url` et `og:image`.
   Les robots de Discord et des réseaux sociaux n'exécutent pas de JavaScript,
   ces adresses doivent rester absolues. Le bloc est signalé par un commentaire.
2. **Supabase → Authentication → URL Configuration** — ajouter la nouvelle adresse
   de `admin.html` aux Redirect URLs, sinon la connexion Discord échoue.
3. **Les guides `SETUP-*.md`** — pour que les exemples restent justes.

Tout le reste suit automatiquement, y compris le lien envoyé en message privé
quand un accès est validé.

---

## Développer en local

Les appels à `version.json` et à Supabase échouent en `file://`. Il faut un serveur :

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
