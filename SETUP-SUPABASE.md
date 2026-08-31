# ☁️ Synchro multi-admin avec Supabase

Une base de données gratuite partagée : toutes les modifications du dashboard
(runners, feuilles, factures, paramètres) sont visibles par tous les admins,
en temps réel.

## Étape 1 — Utiliser ton projet existant

Pas besoin d'un nouveau projet : on ajoute simplement une table dédiée
(`oilroxwood_etat`) dans ton projet Supabase actuel. Elle n'interfère pas
avec tes autres tables.

## Étape 2 — Créer la table

Ouvre ton projet → **SQL Editor** → **New query** → colle ce bloc → **Run** :

```sql
create table if not exists oilroxwood_etat (
  id int primary key,
  data jsonb not null,
  maj timestamptz default now()
);

alter table oilroxwood_etat enable row level security;

create policy "acces_dashboard_oilroxwood" on oilroxwood_etat
  for all using (true) with check (true);

alter publication supabase_realtime add table oilroxwood_etat;
```

## Étape 2 bis — Table de l'agenda personnel

Pour la vue « Mon agenda » (RDV / commandes / entretiens privés par membre),
exécute aussi ce bloc dans le **SQL Editor** :

```sql
create table if not exists oilroxwood_agenda (
  id bigint generated always as identity primary key,
  uid text not null,
  titre text not null,
  type text default 'rdv',
  date date not null,
  deb text, fin text, note text
);

create index if not exists oilroxwood_agenda_uid on oilroxwood_agenda(uid);

alter table oilroxwood_agenda enable row level security;

create policy "agenda_oilroxwood" on oilroxwood_agenda
  for all using (true) with check (true);
```

## Étape 2 ter — Table des notifications (MP automatiques)

Pour les MP automatiques (accès validé, etc.), exécute aussi :

```sql
create table if not exists oilroxwood_notifs (
  id bigint generated always as identity primary key,
  did text not null,
  msg text not null,
  done boolean default false,
  date timestamptz default now()
);

alter table oilroxwood_notifs enable row level security;

create policy "notifs_auth" on oilroxwood_notifs
  for all to authenticated using (true) with check (true);
```

## Étape 2 quater — Table des factures reçues (archives Direction)

```sql
create table if not exists oilroxwood_frecues (
  id bigint generated always as identity primary key,
  entreprise text not null,
  date date,
  montant numeric default 0,
  lien text, note text,
  img text,          -- capture compressée (JPEG base64)
  auteur text,
  created timestamptz default now()
);

alter table oilroxwood_frecues enable row level security;

create policy "frecues_auth" on oilroxwood_frecues
  for all to authenticated using (true) with check (true);
```

## Étape 2 quinquies — Table des to-do personnelles

```sql
create table if not exists oilroxwood_todo (
  id bigint generated always as identity primary key,
  uid text not null,
  txt text not null,
  fait boolean default false,
  date timestamptz default now()
);

create index if not exists oilroxwood_todo_uid on oilroxwood_todo(uid);

alter table oilroxwood_todo enable row level security;

create policy "todo_auth" on oilroxwood_todo
  for all to authenticated using (true) with check (true);
```

## Étape 2 sexies — Table des médias clients (lieu de livraison, captures des notes)

```sql
create table if not exists oilroxwood_media (
  id bigint generated always as identity primary key,
  client text not null,
  type text default 'note',   -- 'lieu' ou 'note'
  note_t bigint,              -- horodatage de la note liée (pour type='note')
  img text,                   -- image compressée (JPEG base64)
  date timestamptz default now()
);

create index if not exists oilroxwood_media_cli on oilroxwood_media(client);

alter table oilroxwood_media enable row level security;

create policy "media_auth" on oilroxwood_media
  for all to authenticated using (true) with check (true);
```

## Étape 3 — Récupérer les clés

Menu **Settings → API** (ou Project Settings → Data API) :

- **Project URL** — ressemble à `https://xxxxxxxx.supabase.co`
- **anon public** key — longue chaîne commençant par `eyJ…`

## Étape 4 — Me donner les deux valeurs

Colle-les moi dans le chat : j'insère les deux constantes dans `admin.html`
(`SB_URL` et `SB_KEY` tout en haut du script) et on pousse.

⚠️ La clé « anon public » est conçue pour être visible côté client, c'est normal.
Par contre ne partage JAMAIS la clé « service_role ».

## Comment ça marche ensuite

- À la connexion au dashboard, l'état est chargé depuis Supabase
- Chaque modification est envoyée automatiquement (~1 s après)
- Les autres admins connectés voient la mise à jour instantanément
- La pastille à côté du logo dans la barre latérale indique l'état de la synchro
  (vert = connecté, rouge = problème, gris = non configuré)
- En cas de modifications simultanées, la dernière sauvegarde gagne

## 🔒 Verrouillage des tables (recommandé)

Par défaut les tables sont accessibles avec la clé publique visible dans le code.
Ce verrouillage réserve la lecture/écriture aux personnes **connectées via Discord** :

### 1. SQL à exécuter (SQL Editor → Run)

```sql
-- supprime toutes les anciennes policies ouvertes
do $$
declare p record;
begin
  for p in select policyname, tablename from pg_policies
    where schemaname='public'
      and tablename in ('oilroxwood_etat','oilroxwood_demandes','oilroxwood_feedback','oilroxwood_agenda')
  loop
    execute format('drop policy %I on %I', p.policyname, p.tablename);
  end loop;
end $$;

-- accès réservé aux utilisateurs connectés (OAuth Discord)
create policy "etat_auth"     on oilroxwood_etat     for all to authenticated using (true) with check (true);
create policy "demandes_auth" on oilroxwood_demandes for all to authenticated using (true) with check (true);
create policy "feedback_auth" on oilroxwood_feedback for all to authenticated using (true) with check (true);
create policy "agenda_auth"   on oilroxwood_agenda   for all to authenticated using (true) with check (true);
```

### 2. Donner la clé secrète aux robots GitHub

Les robots (stats auto, sauvegarde, MP suggestions) ne sont pas « connectés Discord »,
ils ont besoin de la clé secrète :

1. Supabase → **Settings → API** → copie la clé **service_role** (⚠️ à ne JAMAIS mettre dans le code ou le chat)
2. GitHub → dépôt OilRoxwood → **Settings → Secrets and variables → Actions → New repository secret**
3. Nom : `SUPABASE_SERVICE_KEY` — valeur : la clé copiée

### Notes

- Les demandes d'accès continuent de fonctionner : un inconnu qui se connecte via
  Discord est « authentifié » côté Supabase même s'il n'est pas encore approuvé.
- L'accès de secours (`#secours-…`) ne pourra plus lire/écrire la base (pas de
  session Discord) : il n'ouvre le dashboard qu'avec les données locales du navigateur.
