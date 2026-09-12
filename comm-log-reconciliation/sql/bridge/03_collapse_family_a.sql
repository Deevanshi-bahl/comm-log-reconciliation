-- Step 3: collapse retry chains into their root ("underlying communication").
-- A retry (parent_id set) is the SAME communication re-attempted, so a
-- customer who needed several attempts inside one chain counts once.
--
-- Chains here can be a TREE, not just a line: 9001 has two children
-- (9002 and 9004) and 9002 has its own child 9003. A recursive CTE walks
-- any depth / any branching and tags every campaign with its root.
--
-- This file applies the collapse to Family A only (root 9001) so the
-- bridge shows the effect one family at a time:
--   Family A rows: 13 (C1 x1, C2 x2, C3 x3, C4..C10 x1) -> 10 distinct customers.
--   26 -> 23.
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
)
SELECT
      (SELECT COUNT(DISTINCT customer_id) FROM eligible WHERE root_id = 9001)
    + (SELECT COUNT(*)                    FROM eligible WHERE root_id <> 9001)
    AS target_base;
