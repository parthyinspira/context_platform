#!/bin/sh
# Fixture shell script: reads source_orders, writes a CSV extract.
psql -c "SELECT * FROM source_orders" > orders_extract.csv
