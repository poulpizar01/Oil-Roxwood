-- ============================================================================
-- ACCÈS DU BOT — mise à jour (Oil Roxwood)
-- ============================================================================
-- Le développeur du bot se connecte avec thomas.ryspert62@gmail.com au lieu
-- du compte technique prévu. Sans ce correctif, ses écritures (statut des
-- ordres, futurs logs) sont refusées par les règles de sécurité.
--
-- Ce script autorise LES DEUX comptes. Le jour où le bot passe sur le compte
-- technique (recommandé à terme), retire simplement la ligne du gmail et
-- relance ce script.
--
-- Supabase → SQL Editor → Run. Réexécutable sans risque.
-- ============================================================================

create or replace function public.est_bot_oilroxwood()
returns boolean
language sql
stable
security definer
set search_path = public, auth, pg_temp
as $$
  select coalesce(auth.jwt() ->> 'email', '') in (
    'bot@oilroxwood.rp',            -- compte technique dédié (idéal)
    'thomas.ryspert62@gmail.com'    -- compte actuel du développeur du bot
  );
$$;

revoke all on function public.est_bot_oilroxwood() from public, anon;
grant execute on function public.est_bot_oilroxwood() to authenticated;
