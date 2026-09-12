-- TRAP 4: order of operations. Collapsing retry chains BEFORE dropping the
-- ineligible campaign gives 26, not 22: 9004 is a child of 9001, so its
-- 4 customers (C11..C14) get absorbed into Family A's distinct-customer
-- count. Eligibility must be applied at the campaign level first, then the
-- chain is collapsed over what remains.
WITH RECURSIVE chain(id, root_id) AS (
    SELECT id, id FROM campaign WHERE parent_id IS NULL
    UNION ALL
    SELECT c.id, ch.root_id FROM campaign c JOIN chain ch ON c.parent_id = ch.id
),
per_root AS (
    SELECT ch.root_id,
           CASE WHEN EXISTS (SELECT 1 FROM campaign x WHERE x.parent_id = ch.root_id)
                THEN COUNT(DISTINCT l.customer_id) ELSE COUNT(*) END AS n
    FROM communication_log l
    JOIN chain ch ON ch.id = l.communication_id
    GROUP BY ch.root_id
)
SELECT SUM(n) AS target_base FROM per_root;
