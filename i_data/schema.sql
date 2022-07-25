
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE backend_data_nodes (
    item_id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    metadata jsonb,
    content VARCHAR,
    type SMALLINT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE backend_data_links (
    source_id UUID NOT NULL,
    target_id UUID NOT NULL,
    PRIMARY KEY(source_id, target_id),
    FOREIGN KEY (source_id) REFERENCES backend_data_nodes (item_id),
    FOREIGN KEY (target_id) REFERENCES backend_data_nodes (item_id)
);
