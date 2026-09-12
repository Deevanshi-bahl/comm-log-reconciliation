-- Step 4 (FINAL): generalise the collapse to every retry family.
--
-- Rule, per root campaign:
--   * root HAS retries chained off it  -> COUNT(DISTINCT customer_id) across
--     the whole chain (one underlying communication, count each customer once)
--   * root is STANDALONE (no children, no parent) -> COUNT(*) (every send is
--     its own event; the same customer appearing twice legitimately counts twice)
--
-- Family B (9201 -> 9202): D1 failed on 9201, delivered on 9202 -> 6 rows, 5 customers.
--   23 -> 22.
-- Standalone 9101: 7 rows incl. C20 twice, kept as 7 (NOT deduped).
--
-- Result: 10 (Family A) + 7 (Standalone 9101) + 5 (Family B) = 22.
WITH RECURSIVE chain(id, root_id) AS (
    SELECT id, id FROM campaign WHERE parent_id IS NULL
    UNION ALL
    SELECT c.id, ch.root_id
    FROM campaign c
    JOIN chain ch ON c.parent_id = ch.id
),
eligible AS (
    SELECT l.*, ch.root_id
    FROM communication_log l
    JOIN campaign c  ON c.id  = l.communication_id
    JOIN chain    ch ON ch.id = c.id
    WHERE l.merchant_id = 501
      AND l.communication_type = '2'
      AND l.sent_time >= '2026-10-01'
      AND l.sent_time <  '2026-11-01'
      AND c.creation_status IN ('approved', 'aborted', 'resumed', 'stopped')
      AND c.processing_status = 'processed'
),
per_root AS (
    SELECT
        e.root_id,
        CASE
            WHEN EXISTS (SELECT 1 FROM campaign x WHERE x.parent_id = e.root_id)
                THEN COUNT(DISTINCT e.customer_id)   -- retry family: customer once
            ELSE COUNT(*)                            -- standalone: every send
        END AS qualifying_sends
    FROM eligible e
    GROUP BY e.root_id
)
SELECT SUM(qualifying_sends) AS target_base
FROM per_root;
