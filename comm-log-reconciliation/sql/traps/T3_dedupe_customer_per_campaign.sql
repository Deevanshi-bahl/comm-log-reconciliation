-- TRAP 3: dedupe (communication_id, customer_id) on eligible rows -> 25.
-- Over-counts retries (C2 appears under 9001 AND 9002 = 2 "customers") and
-- under-counts the standalone campaign (C20's two legitimate sends -> 1).
-- Two errors in opposite directions; still lands in the wrong place.
SELECT COUNT(*) AS target_base
FROM (
    SELECT DISTINCT l.communication_id, l.customer_id
    FROM communication_log l
    JOIN campaign c ON c.id = l.communication_id
    WHERE c.creation_status IN ('approved','aborted','resumed','stopped')
      AND c.processing_status = 'processed'
);
