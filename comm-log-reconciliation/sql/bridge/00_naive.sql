-- Step 0: the most naive thing you can write.
-- "How many sends?" -> count the rows in the log.
SELECT COUNT(*) AS target_base
FROM communication_log;
