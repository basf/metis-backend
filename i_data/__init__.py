
import json

import pg8000


NODE_TABLE = 'backend_data_nodes'
LINK_TABLE = 'backend_data_links'


class Data_type:
    structure = 1
    calculation = 2
    property = 3


class Data_storage:

    def __init__(self, user, password, database, host, port=5432):

        self.connection = pg8000.connect(
            user=user,
            password=password,
            database=database,
            host=host,
            port=int(port)
        )
        self.cursor = self.connection.cursor()


    def put_item(self, metadata, content, type):
        self.cursor.execute("""
        INSERT INTO {NODE_TABLE} (metadata, content, type) VALUES ('{metadata}', '{content}', {type}) RETURNING item_id;
        """.format(NODE_TABLE=NODE_TABLE, metadata=json.dumps(metadata), content=content, type=type))

        self.connection.commit()
        return str( self.cursor.fetchone()[0] )


    def put_link(self, source_uuid, target_uuid):
        self.cursor.execute("""
        INSERT INTO {db_table} (source_id, target_id) VALUES ('{source_uuid}', '{target_uuid}');
        """.format(db_table=LINK_TABLE, source_uuid=source_uuid, target_uuid=target_uuid))

        self.connection.commit()
        return True


    def get_item(self, uuid):
        self.cursor.execute(
            "SELECT item_id, metadata, content, type FROM {NODE_TABLE} WHERE item_id = '{uuid}';".format(
                NODE_TABLE=NODE_TABLE, uuid=uuid
            )
        )
        row = self.cursor.fetchone()
        if not row:
            return False

        return dict(uuid=str(row[0]), metadata=row[1], content=row[2], type=row[3])


    def get_items(self, uuids):
        query_string = 'item_id IN ({})'.format(', '.join(['%s'] * len(uuids)))

        sql_statement = 'SELECT item_id, metadata, content, type FROM {NODE_TABLE} WHERE {query_string};'.format(
            NODE_TABLE=NODE_TABLE, query_string=query_string
        )
        self.cursor.execute(sql_statement, uuids)

        return [dict(uuid=str(row[0]), metadata=row[1], content=row[2], type=row[3]) for row in self.cursor.fetchall()]


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
        ))
        return [dict(uuid=str(row[0]), metadata=row[1], content=row[2], type=row[3]) for row in self.cursor.fetchall()]


    def search_item(self, content):
        self.cursor.execute(
            "SELECT item_id, metadata, content, type FROM {NODE_TABLE} WHERE content = '{content}';".format(
                NODE_TABLE=NODE_TABLE, content=content
            )
        )
        row = self.cursor.fetchone()
        if not row:
            return False

        return dict(uuid=str(row[0]), metadata=row[1], content=row[2], type=row[3])


    def drop_item(self, uuid):
        if self.get_item(uuid):
            self.cursor.execute("DELETE FROM {LINK_TABLE} WHERE source_id = '{uuid}' OR target_id = '{uuid}';".format(LINK_TABLE=LINK_TABLE, uuid=uuid))
            self.cursor.execute("DELETE FROM {NODE_TABLE} WHERE item_id = '{uuid}';".format(NODE_TABLE=NODE_TABLE, uuid=uuid))
            self.connection.commit()
            return True

        return False


    def close(self):
        self.connection.close()
