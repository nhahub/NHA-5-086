-- PostgreSQL schema generated from the Parquet files in this directory.
-- temp.parquet is intentionally excluded.

CREATE TABLE customer_activity (
    user_id TEXT,
    first_order_date TIMESTAMPTZ,
    last_order_date TIMESTAMPTZ,
    days_since_last_order BIGINT
);

CREATE TABLE distribution_centers (
    id TEXT,
    name TEXT
);

CREATE TABLE events (
    id TEXT,
    user_id TEXT,
    sequence_number BIGINT,
    session_id TEXT,
    created_at TIMESTAMPTZ,
    ip_address TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    browser TEXT,
    traffic_source TEXT,
    uri TEXT,
    event_type TEXT,
    user_type TEXT
);

CREATE TABLE inventory_items (
    id TEXT,
    product_id TEXT,
    created_at TIMESTAMPTZ,
    sold_at TIMESTAMPTZ,
    cost DOUBLE PRECISION,
    product_category TEXT,
    product_name TEXT,
    product_brand TEXT,
    product_retail_price DOUBLE PRECISION,
    product_department TEXT,
    product_distribution_center_id TEXT,
    available BIGINT
);

CREATE TABLE order_items (
    id TEXT,
    order_id TEXT,
    user_id TEXT,
    product_id TEXT,
    inventory_item_id TEXT,
    status TEXT,
    sale_price DOUBLE PRECISION
);

CREATE TABLE orders (
    order_id TEXT,
    user_id TEXT,
    status TEXT,
    created_at TIMESTAMPTZ,
    returned_at TIMESTAMPTZ,
    shipped_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    num_of_item BIGINT
);

CREATE TABLE products (
    id TEXT,
    cost DOUBLE PRECISION,
    category TEXT,
    name TEXT,
    brand TEXT,
    retail_price DOUBLE PRECISION,
    department TEXT,
    distribution_center_id TEXT
);

CREATE TABLE users (
    id TEXT,
    full_name TEXT,
    email TEXT,
    age BIGINT,
    gender TEXT,
    state TEXT,
    street_address TEXT,
    postal_code TEXT,
    city TEXT,
    country TEXT,
    traffic_source TEXT,
    created_at TIMESTAMPTZ
);
