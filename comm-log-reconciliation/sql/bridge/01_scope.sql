-- Step 1: apply the stated reporting scope.
-- merchant 501, communication_type '2' (Campaign), sends in October 2026.
-- On this dataset every row already satisfies the scope, so the number does
-- NOT move (30 -> 30). Kept in the query anyway: the definition should be
-- encoded, not assumed, or it silently breaks on the next month's extract.
SELECT COUNT(*) AS target_base
FROM communication_log l
WHERE l.merchant_id = 501
  AND l.communication_type = '2'
  AND l.sent_time >= '2026-10-01'
  AND l.sent_time <  '2026-11-01';
