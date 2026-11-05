CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS equipment (
    tag TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    aliases JSONB NOT NULL DEFAULT '[]',
    kind TEXT NOT NULL,
    alarm_min DOUBLE PRECISION,
    alarm_max DOUBLE PRECISION,
    normal_state TEXT,
    reserve_available BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE IF NOT EXISTS parts (
    id UUID PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS sensor_readings (
    id UUID PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    equipment_tag TEXT NOT NULL REFERENCES equipment(tag),
    variable TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    origin TEXT NOT NULL,
    source_id TEXT NOT NULL,
    status TEXT NOT NULL,
    equipment_tag TEXT NOT NULL,
    variable TEXT,
    value DOUBLE PRECISION,
    context JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS safety_alerts (
    id UUID PRIMARY KEY,
    code TEXT NOT NULL,
    source_id TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS safety_alert_source_idx
    ON safety_alerts (source_id);
CREATE TABLE IF NOT EXISTS work_orders (
    id UUID PRIMARY KEY,
    event_id UUID NOT NULL UNIQUE REFERENCES events(id),
    equipment_tag TEXT NOT NULL,
    status TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS sync_queue (
    id UUID PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    operation TEXT NOT NULL,
    payload JSONB NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    synced BOOLEAN NOT NULL DEFAULT FALSE,
    last_error TEXT
);
CREATE INDEX IF NOT EXISTS sensor_history_idx
    ON sensor_readings (equipment_tag, variable, observed_at);
CREATE INDEX IF NOT EXISTS event_status_idx
    ON events (status, created_at);
CREATE INDEX IF NOT EXISTS work_order_status_idx
    ON work_orders (status, created_at);
