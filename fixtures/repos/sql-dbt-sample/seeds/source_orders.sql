-- Raw source table loaded by the upstream ingestion job (fixture: lineage root)
CREATE TABLE source_orders (
    order_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    order_status TEXT NOT NULL,
    order_amount NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL
);
