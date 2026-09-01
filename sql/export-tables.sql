-- ============================================================
--  MIGRATION SUPABASE → GITHUB : export des tables annexes
-- ============================================================
--  La sauvegarde quotidienne ne contenait que oilroxwood_etat.
--  Les sept tables ci-dessous vivaient à côté et ne sont donc PAS
--  encore dans data/etat.json : agenda, to-do, factures reçues,
--  médias, suggestions, demandes d'accès et file de notifications.
--
--  À FAIRE, avant d'éteindre Supabase :
--   1. Supabase → SQL Editor → coller cette requête → Run
--   2. Cliquer sur le résultat, tout copier
--   3. Le coller dans un fichier export-tables.json à la racine du dépôt
--   4. Lancer :  python scripts/import_tables.py export-tables.json
--
--  Si une table n'existe pas chez toi, supprime simplement sa ligne
--  (la requête échouerait sinon).
-- ============================================================

select jsonb_pretty(jsonb_build_object(
  'oilroxwood_agenda',   coalesce((select jsonb_agg(to_jsonb(t)) from oilroxwood_agenda   t), '[]'::jsonb),
  'oilroxwood_notifs',   coalesce((select jsonb_agg(to_jsonb(t)) from oilroxwood_notifs   t), '[]'::jsonb),
  'oilroxwood_frecues',  coalesce((select jsonb_agg(to_jsonb(t)) from oilroxwood_frecues  t), '[]'::jsonb),
  'oilroxwood_todo',     coalesce((select jsonb_agg(to_jsonb(t)) from oilroxwood_todo     t), '[]'::jsonb),
  'oilroxwood_media',    coalesce((select jsonb_agg(to_jsonb(t)) from oilroxwood_media    t), '[]'::jsonb),
  'oilroxwood_demandes', coalesce((select jsonb_agg(to_jsonb(t)) from oilroxwood_demandes t), '[]'::jsonb),
  'oilroxwood_feedback', coalesce((select jsonb_agg(to_jsonb(t)) from oilroxwood_feedback t), '[]'::jsonb)
)) as tables;
