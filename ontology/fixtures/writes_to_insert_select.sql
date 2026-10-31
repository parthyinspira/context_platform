INSERT INTO schema.summary
SELECT customer_id, sum(total)
FROM schema.orders
GROUP BY customer_id;
