CREATE TABLE IF NOT EXISTS dht22_readings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    temperature_c REAL    NOT NULL,
    humidity_pct  REAL    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_timestamp ON dht22_readings(timestamp);
