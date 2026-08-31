-- ============================================================================
-- BOT ENTREPRISE ↔ SITE — Oil Roxwood
-- ============================================================================
-- Trois tables + un compte technique pour le bot de l'entreprise :
--   • oilroxwood_bot_logs       — chaque événement (vente, récolte…), en direct
--   • oilroxwood_bot_documents  — documents tenus à jour automatiquement
--   • oilroxwood_bot_ordres     — boîte aux lettres site → bot (ex : « poste
--                                 le rapport en image sur Discord »)
--
-- SÉCURITÉ : le bot n'a PAS la clé secrète du projet. Il se connecte avec un
-- compte dédié (bot@oilroxwood.rp) et les règles ci-dessous ne lui ouvrent
-- QUE ces trois tables. Ni les autres tables Oil Roxwood, ni Famille Moni.
--
-- À exécuter dans Supabase → SQL Editor → Run. Réexécutable sans risque.
-- AVANT d'exécuter : crée le compte du bot (Authentication → Users →
-- Add user → email `bot@oilroxwood.rp`, mot de passe fort, "Auto Confirm").
-- ============================================================================

-- ── 1. Qui est le bot ? ──────────────────────────────────────────────────
create or replace function public.est_bot_oilroxwood()
returns boolean
language sql
stable
security definer
set search_path = public, auth, pg_temp
as $$
  select coalesce(auth.jwt() ->> 'email', '') = 'bot@oilroxwood.rp';
$$;
revoke all on function public.est_bot_oilroxwood() from public, anon;
grant execute on function public.est_bot_oilroxwood() to authenticated;

-- ── 2. Les logs, structurés ──────────────────────────────────────────────
create table if not exists public.oilroxwood_bot_logs (
  id       bigint generated always as identity primary key,
  ts       timestamptz not null default now(),
  type     text not null,          -- vente | recolte | raffinage | depot | retrait | paie | autre…
  employe  text,                   -- nom RP concerné
  quantite numeric,                -- barils / litres
  montant  numeric,                -- dollars
  details  text,                   -- texte libre (le message d'origine si utile)
  meta     jsonb not null default '{}'::jsonb   -- tout extra structuré
);
create index if not exists oilroxwood_bot_logs_ts on public.oilroxwood_bot_logs (ts desc);
create index if not exists oilroxwood_bot_logs_type on public.oilroxwood_bot_logs (type);

alter table public.oilroxwood_bot_logs enable row level security;
drop policy if exists "logs_lecture" on public.oilroxwood_bot_logs;
create policy "logs_lecture" on public.oilroxwood_bot_logs
  for select to authenticated using (true);
drop policy if exists "logs_ecriture_bot" on public.oilroxwood_bot_logs;
create policy "logs_ecriture_bot" on public.oilroxwood_bot_logs
  for insert to authenticated with check (public.est_bot_oilroxwood());
-- pas de update/delete : un journal ne se réécrit pas.

-- ── 3. Les documents tenus à jour par le bot ─────────────────────────────
create table if not exists public.oilroxwood_bot_documents (
  id      text primary key,        -- identifiant lisible : 'grille-salaires', 'reglement'…
  titre   text not null,
  contenu text not null,           -- markdown (mise en forme simple : titres, gras, listes, tableaux)
  maj     timestamptz not null default now(),
  auteur  text not null default 'bot'
);
alter table public.oilroxwood_bot_documents enable row level security;
drop policy if exists "docs_lecture" on public.oilroxwood_bot_documents;
create policy "docs_lecture" on public.oilroxwood_bot_documents
  for select to authenticated using (true);
drop policy if exists "docs_ecriture_bot" on public.oilroxwood_bot_documents;
create policy "docs_ecriture_bot" on public.oilroxwood_bot_documents
  for insert to authenticated with check (public.est_bot_oilroxwood());
drop policy if exists "docs_maj_bot" on public.oilroxwood_bot_documents;
create policy "docs_maj_bot" on public.oilroxwood_bot_documents
  for update to authenticated using (public.est_bot_oilroxwood());

-- ── 4. La boîte aux lettres site → bot ───────────────────────────────────
--    Le site dépose un ordre ; le bot (abonné en Realtime) le traite puis
--    écrit son rapport dans la même ligne. Exactement la recette qui a fait
--    ses preuves pour l'import de taxes de la Famille Moni.
create table if not exists public.oilroxwood_bot_ordres (
  id      bigint generated always as identity primary key,
  created timestamptz not null default now(),
  type    text not null,           -- ex : 'rapport_image', 'annonce'…
  payload jsonb not null default '{}'::jsonb,
  statut  text not null default 'en_attente',   -- en_attente | fait | erreur
  rapport text,
  traite  timestamptz
);
alter table public.oilroxwood_bot_ordres enable row level security;
drop policy if exists "ordres_lecture" on public.oilroxwood_bot_ordres;
create policy "ordres_lecture" on public.oilroxwood_bot_ordres
  for select to authenticated using (true);
drop policy if exists "ordres_depot" on public.oilroxwood_bot_ordres;
create policy "ordres_depot" on public.oilroxwood_bot_ordres
  for insert to authenticated with check (not public.est_bot_oilroxwood());
drop policy if exists "ordres_reponse_bot" on public.oilroxwood_bot_ordres;
create policy "ordres_reponse_bot" on public.oilroxwood_bot_ordres
  for update to authenticated using (public.est_bot_oilroxwood());

-- ── 5. Temps réel : le site et le bot sont prévenus instantanément ───────
--    (ajout conditionnel : réexécutable sans l'erreur « already member »)
do $$
begin
  if not exists (select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and tablename = 'oilroxwood_bot_logs') then
    alter publication supabase_realtime add table public.oilroxwood_bot_logs;
  end if;
  if not exists (select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and tablename = 'oilroxwood_bot_documents') then
    alter publication supabase_realtime add table public.oilroxwood_bot_documents;
  end if;
  if not exists (select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and tablename = 'oilroxwood_bot_ordres') then
    alter publication supabase_realtime add table public.oilroxwood_bot_ordres;
  end if;
end $$;
