"""
A simple persistence layer implementation;
a few Postgres tables are used
(of course we must use raw SQL here only and nowhere else)
"""
import json
import logging

import numpy as np
import pg8000


NODE_TABLE =    "backend_data_nodes"
LINK_TABLE =    "backend_data_links"
PHASE_TABLE =   "backend_phases"
REFDIS_TABLE =  "backend_refdis"
REFELS_TABLE =  "backend_refels"
REFSTRS_TABLE = "backend_refstrs"


class Data_type:
    structure = 1
    calculation = 2
    property = 3
    workflow = 4
    pattern = 5
    user_input = 6


class Data_storage:

    def __init__(self, user, password, database, host, port=5432):
        self.connection = pg8000.connect(
            user=user, password=password, database=database, host=host, port=int(port)
        )
        self.cursor = self.connection.cursor()

    def put_item(self, metadata, content, type):
        self.cursor.execute(
            """
        INSERT INTO {NODE_TABLE} (metadata, content, type) VALUES ('{metadata}', '{content}', {type}) RETURNING item_id;
        """.format(
                NODE_TABLE=NODE_TABLE,
                metadata=json.dumps(metadata),
                content=json.dumps(content) if isinstance(content, dict) else content,
                type=type,
            )
        )

        self.connection.commit()
        return str(self.cursor.fetchone()[0])

    def put_link(self, source_uuid, target_uuid):
        try:
            self.cursor.execute(
                """
            INSERT INTO {db_table} (source_id, target_id) VALUES ('{source_uuid}', '{target_uuid}');
            """.format(
                    db_table=LINK_TABLE,
                    source_uuid=source_uuid,
                    target_uuid=target_uuid,
                )
            )
        except pg8000.exceptions.Error:
            return False

        self.connection.commit()
        return True

    def get_item(self, uuid, with_links=False):
        self.cursor.execute(
            "SELECT item_id, metadata, content, type FROM {NODE_TABLE} WHERE item_id = '{uuid}';".format(
                NODE_TABLE=NODE_TABLE, uuid=uuid
            )
        )
        row = self.cursor.fetchone()
        if not row:
            return False

        parents, children = [], []
        if with_links:
            self.cursor.execute(
                """
            SELECT NULL, target_id FROM {LINK_TABLE} WHERE source_id = '{uuid}'
            UNION ALL
            SELECT source_id, NULL FROM {LINK_TABLE} WHERE target_id = '{uuid}';""".format(
                    LINK_TABLE=LINK_TABLE, uuid=uuid
                )
            )
            for link in self.cursor.fetchall():
                children.append(str(link[1])) if link[1] else parents.append(str(link[0]))

        return dict(
            uuid=str(row[0]),
            metadata=row[1],
            content=row[2],
            type=row[3],
            parents=parents,
            children=children,
        )

    def get_items(self, uuids, with_links=False):
        placeholder = "item_id IN ({})".format(", ".join(["%s"] * len(uuids)))

        sql_statement = "SELECT item_id, metadata, content, type FROM {NODE_TABLE} WHERE {placeholder};".format(
            NODE_TABLE=NODE_TABLE, placeholder=placeholder
        )
        self.cursor.execute(sql_statement, uuids)

        items = {}
        for row in self.cursor.fetchall():
            items[str(row[0])] = dict(
                uuid=str(row[0]),
                metadata=row[1],
                content=row[2],
                type=row[3],
                parents=[],
                children=[],
            )

        if with_links:
            self.cursor.execute(
                """WITH uuid_rows AS (
            SELECT * from UNNEST(ARRAY['{placeholder}']::uuid[])
            )
            SELECT source_id, NULL, target_id FROM {LINK_TABLE} WHERE source_id IN (SELECT * FROM uuid_rows)
            UNION ALL
            SELECT target_id, source_id, NULL FROM {LINK_TABLE} WHERE target_id IN (SELECT * FROM uuid_rows);
            """.format(
                    LINK_TABLE=LINK_TABLE,
                    placeholder="', '".join([str(uuid) for uuid in uuids]),
                )
            )
            for row in self.cursor.fetchall():
                items[str(row[0])]["children"].append(str(row[2])) if row[2] \
                    else items[str(row[0])]["parents"].append(str(row[1]))

        return list(items.values())

    def get_targets(self, uuid):
        raise NotImplementedError

    def get_sources(self, uuid):
        self.cursor.execute(
            """SELECT item_id, metadata, content, type
        FROM {NODE_TABLE}
        WHERE item_id IN (
            SELECT source_id FROM {LINK_TABLE} WHERE target_id = '{uuid}'
        );""".format(
                NODE_TABLE=NODE_TABLE, LINK_TABLE=LINK_TABLE, uuid=uuid
            )
        )
        return [
            dict(uuid=str(row[0]), metadata=row[1], content=row[2], type=row[3])
            for row in self.cursor.fetchall()
        ]

    def search_item(self, needle, name=False):

        if name:
            query = f"SELECT item_id, metadata, content, type FROM {NODE_TABLE} WHERE metadata->>'oname' LIKE '{needle}%%';"
        else:
            query = f"SELECT item_id, metadata, content, type FROM {NODE_TABLE} WHERE content = '{needle}';"

        self.cursor.execute(query)
        row = self.cursor.fetchone()
        if not row:
            return False

        return dict(uuid=str(row[0]), metadata=row[1], content=row[2], type=row[3])

    def drop_item(self, uuid):
        if self.get_item(uuid):
            self.cursor.execute(
                "DELETE FROM {LINK_TABLE} WHERE source_id = '{uuid}' OR target_id = '{uuid}';".format(
                    LINK_TABLE=LINK_TABLE, uuid=uuid
                )
            )
            self.cursor.execute(
                "DELETE FROM {NODE_TABLE} WHERE item_id = '{uuid}';".format(
                    NODE_TABLE=NODE_TABLE, uuid=uuid
                )
            )
            self.connection.commit()
            return True

        return False

    def get_refdis(self, els, strict=False):

        from metis_backend.phaseid import MAX_PATT_LEN

        pg_arrays, pattern_ids, names = [], [], []
        els.sort()

        if strict:
            query = f"SELECT DISTINCT d.ext_id, d.di, s.name FROM {REFDIS_TABLE} d INNER JOIN {REFSTRS_TABLE} s USING (ext_id) INNER JOIN {REFELS_TABLE} f USING(ext_id) WHERE f.elements = '-" + "--".join(els) + "-' LIMIT 1000;"

        else:
            query = f"SELECT DISTINCT d.ext_id, d.di, s.name FROM {REFDIS_TABLE} d INNER JOIN {REFSTRS_TABLE} s USING (ext_id) INNER JOIN {REFELS_TABLE} f USING(ext_id) WHERE f.elements LIKE '" + "%%-" + "-%%-".join(els) + "-%%" + "' LIMIT 1000;"

        logging.warning(query)
        self.cursor.execute(query)
        for row in self.cursor.fetchall():
            pattern_ids.append(row[0])
            pg_arrays.append(np.array(row[1], dtype=float))
            names.append(row[2])

        if not pattern_ids:
            return [], [], []

        ref_patterns = np.zeros((len(pattern_ids), MAX_PATT_LEN, 2))
        for n, array in enumerate(pg_arrays):
            array = array[:MAX_PATT_LEN, :]
            intensities = array[:, 1]
            array[:, 1] = intensities / np.max(intensities)
            ref_patterns[n, 0 : len(array), :] = array

        return ref_patterns, pattern_ids, names

    def import_item(self, ext_id):

        # FIXME only allow from a certain phase ID session
        # FIXME specify parent node

        from metis_backend.structures.struct_utils import provider_to_ase, ase_serialize

        self.cursor.execute(f"SELECT provider, name, content FROM {REFSTRS_TABLE} WHERE ext_id = '{ext_id}';")
        row = self.cursor.fetchone()
        if not row:
            logging.error("No such structure: %s" % ext_id)
            return False, False

        elif row[0] == 4:

            ase_obj, error = provider_to_ase(row[2]) # FIXME switch to optimade_to_ase
            if error:
                logging.error("Error converting to ASE: %s" % error)
                return False, False

            uuid = self.put_item(dict(name=row[1]), ase_serialize(ase_obj), Data_type.structure)
            return uuid, row[1]

        else:
            logging.error("Unsupported provider found: %s" % row[0])
            return False, False

    def close(self):
        self.connection.close()
