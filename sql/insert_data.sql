# insert_data.sql

-- SQL script to insert initial data into tables
INSERT INTO orders (user_id, product, quantity, status) VALUES
    (1, 'Widget A', 2, 'pending'),
    (2, 'Widget B', 1, 'shipped');

INSERT INTO tickets (user_id, issue, priority, status) VALUES
    (1, 'Login failure', 'high', 'open'),
    (2, 'Payment error', 'medium', 'open');

INSERT INTO weather (location, temperature, description) VALUES
    ('New York', 22.5, 'Sunny'),
    ('London', 15.0, 'Cloudy');
