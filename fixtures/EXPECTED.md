# Expected entities and edges per fixture

Reference for harvester and MCP tests asserting against `fixtures/`. Types per the Ontology v0 in `CLAUDE.md`.

## repos/sql-dbt-sample
- Entities: Repository(sample_orders), Module(stg_orders), Module(mart_orders), Table(source_orders)
- Edges: DERIVED_FROM(mart_orders -> stg_orders), DERIVED_FROM(stg_orders -> source_orders), DOCUMENTS(schema.yml -> stg_orders)

## repos/java-sample
- Entities: Repository(orders-service), Module(OrdersRepository), Table(source_orders)
- Edges: READS_FROM(OrdersRepository -> source_orders)
- `target/` must be excluded from the plan (compiled output).

## repos/dotnet-sample
- Entities: Repository(SampleApp), Module(OrdersService), Table(source_orders)
- Edges: READS_FROM(OrdersService -> source_orders)
- `bin/`, `obj/` must be excluded from the plan (build output).

## repos/talend-sample
- Entities: Repository(sample_orders_etl), Job(load_orders), Table(source_orders), Table(stg_orders)
- Edges: READS_FROM(load_orders -> source_orders), WRITES_TO(load_orders -> stg_orders)
- `screenshots/`, `lib/` must be excluded from the plan (over the 1 MB size cap / binaries).
- `load_orders.item` contains one deliberately fake secret for redaction tests; it must be redacted before storage and flagged with a non-default `sensitivity`.

## db/init.sql
- Entities: Table(source_orders), Table(stg_orders), Dashboard(mart_orders), Job(refresh_stg_orders)
- Edges: DERIVED_FROM(stg_orders -> source_orders), READS_FROM(mart_orders -> stg_orders), WRITES_TO(refresh_stg_orders -> stg_orders)
- `job_runs.refresh_stg_orders.is_stale = true` simulates a broken upstream job.

## docs
- Entities: Document(data-retention-policy.md, sensitivity=restricted), Document(orders-faq.md, sensitivity=internal), Document(sample_report.xlsx)
- Edges: DOCUMENTS(orders-faq.md -> source_orders)
