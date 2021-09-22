
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE bscience_data_items (
    item_id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    label VARCHAR(256),
    content VARCHAR,
    type SMALLINT
);
