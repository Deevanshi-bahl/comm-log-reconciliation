-- Same logic as 04_final.sql but one row per root campaign, so a reviewer
-- can see where the 22 comes from: 9001 -> 10, 9101 -> 7, 9201 -> 5.
WITH RECURSIVE chain(id, root_id) AS (
    SELECT id, id FROM campaign WHERE parent_id IS NULL
    UNION ALL
    SELECT c.id, ch.root_id FROM campaign c JOIN chain ch ON c.parent_id = ch.id
),
eligible AS (
    SELECT l.*, ch.root_id
    FROM communication_log l
    JOIN campaign c  ON c.id  = l.communication_id
    JOIN chain    ch ON ch.id = c.id
    WHERE l.merchant_id = 501 AND l.communication_type = '2'
      AND l.sent_time >= '2026-10-01' AND l.sent_time < '2026-11-01'
      AND c.creation_status IN ('approved','aborted','resumed','stopped')
      AND c.processing_status = 'processed'
)
SELECT
    e.root_id,
    r.name                                   AS root_name,
    EXISTS (SELECT 1 FROM campaign x WHERE x.parent_id = e.root_id) AS has_retries,
    COUNT(*)                                 AS raw_rows,
    COUNT(DISTINCT e.customer_id)            AS distinct_customers,
    CASE WHEN EXISTS (SELECT 1 FROM campaign x WHERE x.parent_id = e.root_id)
         THEN COUNT(DISTINCT e.customer_id) ELSE COUNT(*) END AS qualifying_sends
FROM eligible e
JOIN campaign r ON r.id = e.root_id
GROUP BY e.root_id, r.name
ORDER BY e.root_id;
