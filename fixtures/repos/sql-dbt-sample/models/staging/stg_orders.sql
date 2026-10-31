-- Staging model: cleans source_orders (fixture: lineage middle)
SELECT
    order_id,
    customer_id,
    LOWER(order_status) AS order_status,
    order_amount,
    created_at
FROM source_orders
WHERE order_amount > 0
