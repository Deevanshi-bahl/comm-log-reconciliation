-- Step 2: only campaigns that have cleared the reporting gate count.
--   creation_status IN ('approved','aborted','resumed','stopped')
--   AND processing_status = 'processed'
-- Campaign 9004 ("Retry C (pending)") is approval_awaiting but already
-- processed: the send pipeline ran ahead of approval. Its 4 rows (C11..C14)
-- exist in the log but are not reportable.  30 -> 26.
SELECT COUNT(*) AS target_base
FROM communication_log l
JOIN campaign c ON c.id = l.communication_id
WHERE l.merchant_id = 501
  AND l.communication_type = '2'
  AND l.sent_time >= '2026-10-01'
  AND l.sent_time <  '2026-11-01'
  AND c.creation_status IN ('approved', 'aborted', 'resumed', 'stopped')
  AND c.processing_status = 'processed';
