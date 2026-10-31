#!/bin/sh
# Fixture shell script: refreshes mart_orders from stg_orders.
psql -c "REFRESH MATERIALIZED VIEW mart_orders"
