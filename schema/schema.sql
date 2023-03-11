
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS backend_data_nodes (
    item_id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    metadata jsonb,
    content VARCHAR,
    type SMALLINT,
    created_at TIMESTAMP DEFAULT NOW(),
    seen BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS backend_data_links (
    source_id UUID NOT NULL,
    target_id UUID NOT NULL,
    PRIMARY KEY (source_id, target_id),
    FOREIGN KEY (source_id) REFERENCES backend_data_nodes (item_id),
    FOREIGN KEY (target_id) REFERENCES backend_data_nodes (item_id)
);

CREATE TABLE IF NOT EXISTS distinct_phases (
    phid         INT PRIMARY KEY,
    elements     VARCHAR(64) NOT NULL,
    formula_txt  VARCHAR(128) NOT NULL,
    formula_html VARCHAR(384) NOT NULL,
    spg          INT,
    pearson      VARCHAR(8),
    crsystem     SMALLINT NOT NULL
);
CREATE INDEX IF NOT EXISTS i_phid ON distinct_phases USING btree( phid );
CREATE INDEX IF NOT EXISTS i_elements ON distinct_phases USING btree( elements text_pattern_ops );
