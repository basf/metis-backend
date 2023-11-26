
import re
import logging
import random # TODO

import set_path
from metis_backend.structures.chemical_formulae import parse_formula
from metis_backend.structures.struct_utils import sgn_to_label


BFF_PREFIX = 'bff_'

USERID = 3 # FIXME Metis Robot
TYPEID = 4 # FIXME slug=phases

PHASE_DESCR = 'https://mpds.io/phase_id/'

BFF_TABLES = {
    'datasources':             BFF_PREFIX + 'user_datasources',
    'collections':             BFF_PREFIX + 'user_collections',
    'collections_datasources': BFF_PREFIX + 'user_collections_datasources',
}

VISIBILITY = {
    'private': 'private',
    'shared': 'shared',
    'community': 'community',
}


def assign_phase(given, candidates):
    # TODO
    return random.choice(candidates)


def clean_formula_tags(string):
    return string.replace('<sub>', '').replace('</sub>', '')


fidx = re.compile(r"(\d)")
def formula_to_chars(string):
    return fidx.sub("&#x208\g<0>;", string)


def create_tag(conn, cursor, user_id, type_id, title, descr, visibility=VISIBILITY['community']):
    cursor.execute("""
    INSERT INTO {tags_table} ("userId", "typeId", title, description, visibility) VALUES
    ({user_id}, {type_id}, '{title}', '{descr}', '{visibility}')
    RETURNING id;
    """.format(
        tags_table=BFF_TABLES['collections'],
        user_id=user_id,
        type_id=type_id,
        title=title,
        descr=descr,
        visibility=visibility
    ))
    conn.commit()
    return cursor.fetchone()[0]


def get_or_create_tag(conn, cursor, user_id, type_id, title, descr):
    cursor.execute("""SELECT id FROM {} WHERE title = '{}';""".format(BFF_TABLES['collections'], title))
    found = cursor.fetchone()
    return found[0] if found else create_tag(conn, cursor, user_id, type_id, title, descr)


def save_as_phase(db, node_uuid, phase):
    """
    Insert the newly found phase collection
    into the database
    """
    logging.warning(f"Assigning phase {phase} to node {node_uuid}")

    db.cursor.execute("""SELECT id FROM {} WHERE uuid = '{}';""".format(
        BFF_TABLES['datasources'], node_uuid
    ))
    found = db.cursor.fetchone()
    if not found:
        logging.critical(f"Node {node_uuid} is orphaned")
        return

    datasrc_id = found[0]

    title = f"{clean_formula_tags(phase[1])} {sgn_to_label(phase[2])} *{phase[2]}"
    #title = f"{formula_to_chars(phase[1])} *{phase[2]}" # FIXME entities are not rendered properly
    descr = f"{PHASE_DESCR}{phase[0]}"

    tag_id = get_or_create_tag(db.connection, db.cursor, USERID, TYPEID, title, descr)

    db.cursor.execute("""INSERT INTO {} ("collectionId", "dataSourceId") VALUES ({}, {}) ON CONFLICT DO NOTHING;""".format(
        BFF_TABLES['collections_datasources'], tag_id, datasrc_id
    ))
    db.connection.commit()


if __name__ == "__main__":
    pass
