-- TRAP 5: "distinct customers reached" read too literally -> 25.
-- Ignores that the same customer can be reached by different underlying
-- communications, and that standalone re-sends count separately.
SELECT COUNT(DISTINCT customer_id) AS target_base
FROM communication_log;
