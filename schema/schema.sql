
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- Data graph nodes

CREATE TABLE IF NOT EXISTS backend_data_nodes (
    item_id    UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    metadata   jsonb NOT NULL, -- TODO metadata["name"] contains HTML
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


-- Pre-defined materials phases

CREATE TABLE IF NOT EXISTS backend_phases (
    phase_id INT PRIMARY KEY,
    elements VARCHAR(128) NOT NULL,
    formula  VARCHAR(128) NOT NULL,
    spg      SMALLINT NOT NULL,
    natcell  SMALLINT NOT NULL
);

CREATE INDEX IF NOT EXISTS backend_phases_phase_id ON backend_phases USING btree( phase_id );
CREATE INDEX IF NOT EXISTS backend_phases_spg ON backend_phases USING btree( spg );
CREATE INDEX IF NOT EXISTS backend_phases_elements ON backend_phases USING btree( elements text_pattern_ops );


-- PHASE MATCHING crystal structures

CREATE TABLE IF NOT EXISTS backend_refstrs (
    ext_id   VARCHAR(128) PRIMARY KEY,
    phase_id INT,
    provider SMALLINT DEFAULT 0, -- TODO enum 0 Metis; 1 COD; 2 ICDD PDF4+; 3 CCDC; 4 MPDS;
    name VARCHAR(384) NOT NULL, -- TODO contains HTML
    content JSONB NOT NULL,
    FOREIGN KEY (phase_id) REFERENCES backend_phases (phase_id)
);

CREATE INDEX IF NOT EXISTS backend_refstrs_ext_id ON backend_refstrs USING btree( ext_id );
CREATE INDEX IF NOT EXISTS backend_refstrs_phase_id ON backend_refstrs USING btree( phase_id );


-- PHASE MATCHING dIs

CREATE TABLE IF NOT EXISTS backend_refdis (
    ext_id   VARCHAR(128) PRIMARY KEY,
    phase_id INT,
    di       NUMERIC[][] NOT NULL,
    FOREIGN KEY (ext_id) REFERENCES backend_refstrs (ext_id),
    FOREIGN KEY (phase_id) REFERENCES backend_phases (phase_id)
);

CREATE INDEX IF NOT EXISTS backend_refdis_ext_id ON backend_refdis USING btree( ext_id );


-- PHASE MATCHING elements

CREATE TABLE IF NOT EXISTS backend_refels (
    ext_id   VARCHAR(128) NOT NULL,
    elements VARCHAR(128) NOT NULL,
    FOREIGN KEY (ext_id) REFERENCES backend_refstrs (ext_id)
);

CREATE INDEX IF NOT EXISTS backend_refels_ext_id ON backend_refels USING btree( ext_id );
CREATE INDEX IF NOT EXISTS backend_refels_elements ON backend_refels USING btree( elements text_pattern_ops );
