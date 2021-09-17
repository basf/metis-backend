
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE data_items (
    item_id UUID NOT NULL DEFAULT uuid_generate_v1() PRIMARY KEY,
    label VARCHAR(256),
    content VARCHAR,
    type SMALLINT
);