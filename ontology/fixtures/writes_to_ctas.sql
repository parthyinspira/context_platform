CREATE TABLE schema.report AS
SELECT customer_id, count(*)
FROM schema.orders
GROUP BY customer_id;
