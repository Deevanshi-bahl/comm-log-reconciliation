-- TRAP 2 (the dangerous one): delivered rows + eligible campaigns.
-- This query returns EXACTLY 22 on this dataset -- and it is still wrong.
--
-- Why it coincides: in this data every 1100 (failed) attempt is followed by
-- exactly one later attempt in the same chain that delivers, so "number of
-- 900 rows" happens to equal "distinct customers per chain". The moment a
-- customer fails and is never re-attempted, or delivers twice inside one
-- chain, or a standalone campaign has a failed send, this query drifts from
-- the definition (see tests/test_reconciliation.py for a dataset where it
-- returns 24 while the correct query returns 22).
--
-- A bridge that lands on 22 via this route has no retry-chain step in it,
-- which is precisely the "right number, no real adjustments" red flag.
SELECT COUNT(*) AS target_base
FROM communication_log l
JOIN campaign c ON c.id = l.communication_id
WHERE c.creation_status IN ('approved','aborted','resumed','stopped')
  AND c.processing_status = 'processed'
  AND l.delivery_status = 900;
