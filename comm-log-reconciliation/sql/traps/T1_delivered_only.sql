-- TRAP 1: "just count delivered rows" (delivery_status = 900).
-- Gives 26 here. Wrong on principle: target_base is about customers reached
-- per underlying communication, not about delivery outcomes per row.
SELECT COUNT(*) AS target_base
FROM communication_log
WHERE delivery_status = 900;
