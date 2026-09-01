# Refonte visuelle Oil Roxwood — « raffinerie brute »

Nouveau socle graphique commun au site vitrine et au poste de contrôle.
**Aucune ligne de logique métier n'a été modifiée.**

## Ce qu'il faut copier dans le repo

| Fichier | État |
|---|---|
| `assets/roxwood-core.css` | **nouveau** — jetons, textures, rivets, lampe torche, plaques inclinables, rubans |
| `assets/roxwood-ui.js` | **nouveau** — comportements communs (torche, tilt, rivets, silhouette de raffinerie) |
| `assets/roxwood-site.css` | **nouveau** — mise en page de la vitrine |
| `assets/roxwood-site.js` | **nouveau** — thème jour/nuit, hero animé, simulateur, mur de clients |
| `assets/roxwood-app.css` | **nouveau** — socle du dashboard (remplace les 377 lignes de `<style>`) |
| `index.html` | **réécrit** — même contenu, même SEO, mêmes liens |
| `admin.html` | **modifié à 3 endroits seulement** (voir plus bas) |

Rien d'autre ne bouge : `facture.html`, `reset.html`, `data/`, `scripts/`,
les workflows GitHub et les tables Supabase sont inchangés.

## Ce qui a changé dans `admin.html`

1. **Ligne 12** — la feuille Google Fonts charge Big Shoulders Display / Archivo /
   IBM Plex Mono à la place d'Oswald / Inter / JetBrains Mono.
2. **Lignes 15 → 392** — le bloc `<style>` de 377 lignes est remplacé par deux
   `<link>` vers `roxwood-core.css` et `roxwood-app.css`.
3. **La carte de connexion** — nouveau balisage (plaque boulonnée, ruban de chantier,
   silhouette de raffinerie). Tous les `id` et le `onclick="loginDiscord()"` sont conservés :
   `#verTag`, `#lg_denied`, `#lg_hint`, `.login-card`.
4. **Ajout de `roxwood-ui.js`** juste avant le script principal, et d'un petit bloc
   d'habillage à la fin du fichier (rivets, inclinaison, reflet). Ce bloc ne lit ni
   n'écrit aucune donnée.

Le script principal — les 5 000 lignes de logique — est **identique au caractère près**.

## Pourquoi ça marche sans toucher au JS

Tout le dashboard génère son HTML avec un vocabulaire de classes fixe :
`panel`, `kpi`, `lbl`, `val`, `delta`, `btn`, `btn-gold`, `btn-ghost`, `btn-red`, `btn-sm`,
`grid g2/g3/g4`, `topbar`, `sub`, `field`, `f-lbl`, `f-row`, `badge`, `bg0`…`bg3`, `bgrole`,
`bgstg`, `em-chip`, `zone-tag`, `zA`…`zD`, `prog`, `pct`, `chip`, `up`, `down`, `gold`,
`empty`, `warn`, `tabs`, `tab`, `sheet`, `calc`, `combo`, `combo-list`, `combo-item`,
`combo-count`, `match`, `podium`, `pod1`…`pod3`, `avat`, `nvb`, `vsep`, `fact-wrap`,
`ag-grid`, `ag-col`, `ag-ev`, `ro-zone`, `tour-hl`, `rip`, `promo-flag`, `inv*`…

`roxwood-app.css` réimplémente **ce contrat à l'identique**, plus les identifiants
(`#login`, `#app`, `#main`, `#toast`, `#modalBg`, `#nfBell`, `#nfPanel`, `#gkOv`, `#gkBox`,
`#verBanner`, `#printZone`, `#tourCard`, `#whoami`, `#logout`, `#bgCanvas`…) et les
variables (`--bg`, `--panel`, `--panel-2`, `--line`, `--ink`, `--muted`, `--accent`,
`--accent-2`, `--or1`…`--or4`, `--green`, `--red`, `--blue`, `--violet`, `--radius`,
`--neon-p`, `--neon-c`, `--neon-v`). Les styles en ligne du JS continuent donc de
fonctionner et adoptent automatiquement la nouvelle palette.

**La facture imprimable (`.inv*` et le bloc `@media print`) est recopiée telle quelle** :
elle doit rester sur fond blanc et lisible à l'impression.

## Le design

- **Palette** — noir charbon `#0D0A08` et ambre `#E8A020`. Vert / rouge / bleu acier
  restent réservés aux états (validé, en retard, en attente) et ne servent jamais de
  couleur décorative.
- **Typographie** — Big Shoulders Display (signalétique industrielle) pour les titres,
  Archivo pour le texte, IBM Plex Mono pour tous les chiffres, en alignement tabulaire.
- **Matière** — plaques d'acier boulonnées aux quatre coins, rubans de chantier,
  grain et rouille en surimpression.
- **Interactions** — une lampe torche suit le curseur et révèle la rouille ; les plaques
  s'inclinent en 3D avec un reflet métallique. Les grands tableaux gardent le reflet mais
  ne pivotent pas, pour que les chiffres restent lisibles.
- **Thèmes** — la vitrine garde son bouton jour / nuit (`localStorage.orx_theme`), avec
  une vraie palette de jour. Le poste de contrôle reste en nuit : c'est une salle de contrôle.
- **Accessibilité** — `prefers-reduced-motion` coupe animations, torche et inclinaison ;
  la torche est désactivée sur écran tactile.

## Pour tester avant de pousser

Ouvrir le dossier avec un serveur local (les `fetch` de `version.json` et de Supabase
échouent en `file://`) :

```
python -m http.server 8000
```

puis `http://localhost:8000/` et `http://localhost:8000/admin.html`.
