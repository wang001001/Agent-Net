# create_table.sql

-- SQL script to create necessary tables
-- Example:
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    product TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS train_tickets (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    issue TEXT NOT NULL,
    priority TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weather (
    id INTEGER PRIMARY KEY,
    location TEXT NOT NULL,
    temperature REAL,
    description TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
