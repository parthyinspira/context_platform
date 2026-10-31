-- Fixture sample Postgres database for harvester tests (KAN-88).
-- Synthetic data only. Mirrors the sql-dbt-sample lineage chain.

CREATE SCHEMA IF NOT EXISTS sample_orders;

CREATE TABLE sample_orders.source_orders (
    order_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    order_status TEXT NOT NULL,
    order_amount NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL
);
COMMENT ON TABLE sample_orders.source_orders IS 'Fixture: raw orders ingested from the upstream order system.';

CREATE TABLE sample_orders.stg_orders (
    order_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    order_status TEXT NOT NULL,
    order_amount NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL
);
COMMENT ON TABLE sample_orders.stg_orders IS 'Fixture: cleaned orders, derived from source_orders.';

CREATE VIEW sample_orders.mart_orders AS
SELECT
    customer_id,
    order_status,
    COUNT(*) AS order_count,
    SUM(order_amount) AS total_amount
FROM sample_orders.stg_orders
GROUP BY customer_id, order_status;
COMMENT ON VIEW sample_orders.mart_orders IS 'Fixture: orders dashboard aggregate, derived from stg_orders.';

CREATE OR REPLACE PROCEDURE sample_orders.refresh_stg_orders()
LANGUAGE SQL
AS $$
    DELETE FROM sample_orders.stg_orders;
    INSERT INTO sample_orders.stg_orders
    SELECT order_id, customer_id, LOWER(order_status), order_amount, created_at
    FROM sample_orders.source_orders
    WHERE order_amount > 0;
$$;
COMMENT ON PROCEDURE sample_orders.refresh_stg_orders() IS 'Fixture: refresh job, mirrors the dbt staging model.';

-- A table deliberately marked stale, for prod-support / broken-job test scenarios.
CREATE TABLE sample_orders.job_runs (
    job_name TEXT PRIMARY KEY,
    last_success_at TIMESTAMP NOT NULL,
    is_stale BOOLEAN NOT NULL DEFAULT FALSE
);
COMMENT ON TABLE sample_orders.job_runs IS 'Fixture: job run log; refresh_stg_orders is marked is_stale=true to simulate a broken job.';

INSERT INTO sample_orders.source_orders (order_id, customer_id, order_status, order_amount, created_at) VALUES
    (1, 100, 'open', 42.50, '2026-01-01 00:00:00'),
    (2, 100, 'closed', 15.00, '2026-01-02 00:00:00'),
    (3, 101, 'open', 99.99, '2026-01-03 00:00:00');

INSERT INTO sample_orders.stg_orders (order_id, customer_id, order_status, order_amount, created_at) VALUES
    (1, 100, 'open', 42.50, '2026-01-01 00:00:00'),
    (2, 100, 'closed', 15.00, '2026-01-02 00:00:00'),
    (3, 101, 'open', 99.99, '2026-01-03 00:00:00');

INSERT INTO sample_orders.job_runs (job_name, last_success_at, is_stale) VALUES
    ('refresh_stg_orders', '2025-01-01 00:00:00', TRUE);
