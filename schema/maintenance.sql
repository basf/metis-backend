
REINDEX TABLE backend_refstrs;
CLUSTER backend_refstrs USING backend_refstrs_ext_id;
ANALYZE backend_refstrs;

REINDEX TABLE backend_refdis;
CLUSTER backend_refdis USING backend_refdis_ext_id;
ANALYZE backend_refdis;

REINDEX TABLE backend_refels;
CLUSTER backend_refels USING backend_refels_elements;
ANALYZE backend_refels;
