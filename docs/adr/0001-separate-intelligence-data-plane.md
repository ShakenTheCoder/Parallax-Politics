# Separate the intelligence data plane from the agent control plane

Parallax keeps authorization, provenance, approvals, and compact canonical records in PostgreSQL while high-volume raw documents, event streams, analytical time series, and search indexes live behind replaceable object-store, Redpanda, ClickHouse, and OpenSearch adapters. LLM agents consume bounded projections instead of scraping or owning bulk data because this preserves replayability, temporal backtesting, and source-policy enforcement while allowing storage services to scale independently.

