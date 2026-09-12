-- Exploration queries I ran before writing the bridge (kept for the record).

-- 1. What is actually in scope? (all 30 rows: one merchant, one type, one month, one channel)
SELECT merchant_id, communication_type, channel,
       MIN(sent_time), MAX(sent_time), COUNT(*)
FROM communication_log GROUP BY 1,2,3;

-- 2. Campaign tree: who is a retry of whom, and who is reportable?
SELECT c.id, c.parent_id, c.name, c.creation_status, c.processing_status,
       (SELECT COUNT(*) FROM communication_log l WHERE l.communication_id = c.id) AS log_rows
FROM campaign c ORDER BY c.id;

-- 3. Delivery status mix per campaign.
SELECT communication_id, delivery_status, COUNT(*)
FROM communication_log GROUP BY 1,2 ORDER BY 1,2;

-- 4. Customers appearing more than once anywhere (the candidates for collapsing).
SELECT customer_id, COUNT(*) AS n, GROUP_CONCAT(communication_id || '@' || delivery_status, ', ') AS attempts
FROM communication_log GROUP BY customer_id HAVING n > 1 ORDER BY customer_id;

-- 5. Does scheduled_time ever differ from sent_time? (No.)
SELECT COUNT(*) FROM communication_log WHERE scheduled_time <> sent_time;

-- 6. Credits billed vs. reportable sends (30 vs 22 -- a finance question in itself).
SELECT SUM(credit_used) FROM communication_log;
