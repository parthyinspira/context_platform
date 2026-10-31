-- Fixture: SQL resource bundled with the Java service
SELECT order_id, customer_id FROM source_orders WHERE order_status = 'open';
