# 🔌 Brancher le bot de l'entreprise au site Oil Roxwood

Document pour le·la développeur·se du bot. Trois fonctions, trois tables,
une connexion. Tout le code est prêt à copier.

## La connexion (une fois, au démarrage du bot)

Pas de clé `service_role` — le bot a son **propre compte**, qui n'ouvre que
ses trois tables. Installe la bibliothèque puis connecte-toi :

```bash
npm install @supabase/supabase-js
```

```js
const { createClient } = require('@supabase/supabase-js');

const sb = createClient(
  'https://prwdtdmdkhzwfyivaepw.supabase.co',
  'sb_publishable_qgN4fRX9eVdKn3SWAjtmhw_F00rlqXz'   // clé publique, normale dans le code
);

// Les identifiants du compte bot : à garder en variables d'environnement.
await sb.auth.signInWithPassword({
  email: process.env.ORX_BOT_EMAIL,       // bot@oilroxwood.rp
  password: process.env.ORX_BOT_PASSWORD, // fourni par Oil Roxwood en privé
});
```

La session se rafraîchit toute seule tant que le processus tourne. Si le bot
redémarre, il se reconnecte pareil.

## 1. Envoyer les logs (à chaque événement)

À chaque vente / récolte / raffinage / dépôt / retrait — au moment où le bot
poste déjà son message Discord — ajoute une ligne :

```js
await sb.from('oilroxwood_bot_logs').insert({
  type: 'vente',              // vente | recolte | raffinage | depot | retrait | paie | autre
  employe: 'Ashley Cooper',   // le nom RP concerné
  quantite: 120,              // barils / litres (nombre, pas de texte)
  montant: 4800,              // dollars (optionnel)
  details: 'Vente au terminal sud',   // texte libre (optionnel)
  meta: { salon: 'ventes', run_id: 42 }  // tout extra utile, format libre (optionnel)
});
```

C'est tout. Le site l'affiche **instantanément** (temps réel). Les logs sont
en ajout seul : personne — pas même le bot — ne peut modifier ou effacer une
ligne écrite.

## 2. Tenir un document à jour

Un « document » = un identifiant + un titre + un contenu en **Markdown**
(titres `#`, gras `**`, listes `-`, tableaux `|`). Le site l'affiche mis en
forme, avec la date de dernière mise à jour.

```js
await sb.from('oilroxwood_bot_documents').upsert({
  id: 'grille-salaires',        // identifiant stable, en minuscules-avec-tirets
  titre: 'Grille des salaires',
  contenu: '| Poste | Salaire |\n|---|---|\n| Commercial | 25 000 $ |',
  maj: new Date().toISOString(),
});
```

`upsert` = crée le document s'il n'existe pas, le remplace sinon. Mets à jour
aussi souvent que tu veux.

## 3. Recevoir les ordres du site (ex : poster un rapport en image)

Le site dépose des « ordres » dans `oilroxwood_bot_ordres`. Abonne-toi au
temps réel pour les recevoir dès qu'ils arrivent :

```js
sb.channel('ordres')
  .on('postgres_changes',
    { event: 'INSERT', schema: 'public', table: 'oilroxwood_bot_ordres' },
    async ({ new: ordre }) => {
      try {
        if (ordre.type === 'rapport_image') {
          await posterRapportImage(ordre.payload);   // voir ci-dessous
        }
        await sb.from('oilroxwood_bot_ordres')
          .update({ statut: 'fait', rapport: 'Posté sur Discord', traite: new Date().toISOString() })
          .eq('id', ordre.id);
      } catch (e) {
        await sb.from('oilroxwood_bot_ordres')
          .update({ statut: 'erreur', rapport: String(e).slice(0, 500), traite: new Date().toISOString() })
          .eq('id', ordre.id);
      }
    })
  .subscribe();
```

Filet de sécurité recommandé (si le bot était éteint quand l'ordre est arrivé) :
au démarrage, traite les ordres en retard :

```js
const { data: enRetard } = await sb.from('oilroxwood_bot_ordres')
  .select('*').eq('statut', 'en_attente').order('id');
```

## 4. Poster une page du site « en image » sur Discord

Le site fournit des pages-rapports propres, faites pour la photo (fond
sombre, cadrage fixe, pas de menu). Capture avec Puppeteer, poste le PNG :

```bash
npm install puppeteer
```

```js
const puppeteer = require('puppeteer');

async function posterRapportImage(payload) {
  const url = 'https://poulpizar01.github.io/Oil-Roxwood/' + (payload.page || 'tv.html');
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 675, deviceScaleFactor: 2 });
  await page.goto(url, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 1500));       // le temps que les données arrivent
  const png = await page.screenshot({ type: 'png' });
  await browser.close();

  // Poste dans le salon voulu avec ta bibliothèque Discord habituelle, ex. discord.js :
  const salon = await client.channels.fetch(payload.salon_id || SALON_RAPPORTS);
  await salon.send({ files: [{ attachment: png, name: 'rapport-oilroxwood.png' }] });
}
```

## Récapitulatif des règles de sécurité (pour info)

| Table | Le bot | Les membres du site |
|---|---|---|
| `oilroxwood_bot_logs` | ajoute (jamais modifier/effacer) | lisent |
| `oilroxwood_bot_documents` | crée + met à jour | lisent |
| `oilroxwood_bot_ordres` | lit + répond (statut/rapport) | déposent + lisent |

Le compte `bot@oilroxwood.rp` n'a **aucun** droit sur les autres tables du
projet. Si le mot de passe fuite : le changer dans Supabase (Authentication →
Users) et dans les variables d'environnement du bot — rien d'autre à faire.

Question technique ? Passe par Oil Roxwood, qui transmettra.
