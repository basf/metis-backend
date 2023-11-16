#!/usr/bin/env python
"""
This script deals with both the backend and BFF tables,
analyzing and updating them. To be run by cron every 5 minutes.
"""
import logging

import spglib

from phase_utils import assign_phase, save_as_phase

import set_path
from metis_backend.helpers import get_data_storage
from metis_backend.datasources import Data_type, NODE_TABLE, PHASE_TABLE
from metis_backend.structures import html_formula
from metis_backend.structures.struct_utils import get_formula, sgn_to_crsystem, crsystem_to_sgn, ase_unserialize


accuracy = 1E-02

main_conn = get_data_storage()
work_conn = get_data_storage()

seen = []

logging.basicConfig(level=logging.WARNING)

main_conn.cursor.execute("SELECT item_id, metadata, content FROM {} WHERE type = {} AND has_phase = FALSE;".format(
    NODE_TABLE, Data_type.structure
))
for row in main_conn.cursor.fetchall():

    ase_obj = ase_unserialize(row[2])
    symmetry = spglib.get_spacegroup(ase_obj, symprec=accuracy)
    try:
        sgn = int( symmetry.split()[1].replace("(", "").replace(")", "") )
    except (ValueError, IndexError, AttributeError):
        logging.error('Symmetry error (coinciding atoms?) in structure')
        continue

    elements = sorted(list( set([atom.symbol for atom in ase_obj]) ))

    logging.info(('WORKING ON', get_formula(ase_obj), sgn))

    work_conn.cursor.execute("SELECT phase_id, formula, spg FROM {} WHERE elements = '-{}-' AND spg = {};".format(
        PHASE_TABLE, "--".join(elements), sgn
    ))
    found = work_conn.cursor.fetchone()
    result = None

    # EXACT MATCHING
    if found:
        phid, label, spg = found
        #label = html_formula(label)
        logging.info(('FOUND', row[1]['name'], phid, label, spg))
        result = (phid, label, spg)

    # FUZZY MATCHING
    else:
        logging.info(('TRYING', sgn_to_crsystem(sgn)))
        sg1, sg2 = crsystem_to_sgn(sgn_to_crsystem(sgn))
        work_conn.cursor.execute("SELECT phase_id, formula, spg FROM {} WHERE elements = '-{}-' AND spg >= {} AND spg <= {};".format(
            PHASE_TABLE, "--".join(elements), sg1, sg2
        ))
        candidates = []
        for candidate in work_conn.cursor.fetchall():
            logging.info(('MAYBE', row[1]['name'], candidate, sgn))
            candidates.append(candidate)

        if candidates:
            result = assign_phase((get_formula(ase_obj), sgn), candidates)
            #if assigned:
            #    result = (assigned[0], html_formula(assigned[1]), assigned[2])
        else:
            logging.error('Cannot determine phase for %s (%s)' % (row[1]['name'], sgn))

    if result:
        logging.info((row[1]['name'], 'will be assigned phase', result))
        save_as_phase(work_conn, row[0], result)

    seen.append(str(row[0]))

work_conn.close()

if seen:
    main_conn.cursor.execute("UPDATE {} SET has_phase = TRUE WHERE item_id IN ('{}');".format(
        NODE_TABLE, "', '".join(seen)
    ))
    main_conn.connection.commit()

main_conn.close()
