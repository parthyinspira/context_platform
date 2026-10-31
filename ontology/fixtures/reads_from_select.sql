SELECT a.id, b.name
FROM schema.orders a
JOIN schema.customers b ON a.customer_id = b.id;
