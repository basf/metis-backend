
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Data graph nodes

CREATE TABLE IF NOT EXISTS backend_data_nodes (
    item_id    UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    metadata   jsonb NOT NULL,
    content    VARCHAR NOT NULL,
    type       SMALLINT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    has_phase  BOOLEAN DEFAULT FALSE -- TODO might want to reference the particular phase instead
);

-- Data graph edges

CREATE TABLE IF NOT EXISTS backend_data_links (
    source_id UUID NOT NULL,
    target_id UUID NOT NULL,
    PRIMARY KEY (source_id, target_id),
    FOREIGN KEY (source_id) REFERENCES backend_data_nodes (item_id),
    FOREIGN KEY (target_id) REFERENCES backend_data_nodes (item_id)
);

-- Pre-defined materials phases (read-only)

CREATE TABLE IF NOT EXISTS backend_phases (
    phase_id INT PRIMARY KEY,
    elements VARCHAR(64) NOT NULL, -- FIXME?
    formula  VARCHAR(128) NOT NULL,
    spg      SMALLINT NOT NULL,
    natcell  SMALLINT NOT NULL
);

CREATE INDEX IF NOT EXISTS i_phid ON backend_phases USING btree( phase_id );
CREATE INDEX IF NOT EXISTS i_lattices ON backend_phases USING btree( spg );
CREATE INDEX IF NOT EXISTS i_elements ON backend_phases USING btree( elements text_pattern_ops );

-- Phase matching dIs

CREATE TABLE IF NOT EXISTS backend_refdis (
    ext_id   VARCHAR(128) NOT NULL,
    phase_id INT NOT NULL,
    provider SMALLINT DEFAULT 0, -- 0 Metis; 1 COD; 2 ICDD PDF4+; 3 CCDC; 4 MPDS;
    elements VARCHAR(64) NOT NULL, -- FIXME?
    di       NUMERIC[][] NOT NULL,
    FOREIGN KEY (phase_id) REFERENCES backend_phases (phase_id)
);

CREATE INDEX IF NOT EXISTS i_elements ON backend_refdis USING btree( elements text_pattern_ops );
