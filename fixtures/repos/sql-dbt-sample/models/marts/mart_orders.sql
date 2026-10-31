-- Mart model: aggregates stg_orders for the orders dashboard (fixture: lineage leaf)
SELECT
    customer_id,
    order_status,
    COUNT(*) AS order_count,
    SUM(order_amount) AS total_amount
FROM stg_orders
GROUP BY customer_id, order_status
