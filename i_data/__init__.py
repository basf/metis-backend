
import pg8000


DB_TABLE = 'bscience_data_items'


class Data_Storage(object):

    def __init__(self, user, password, database, host, port=5432):

        self.connection = pg8000.connect(
            user=user,
            password=password,
            database=database,
            host=host,
            port=int(port)
        )
        self.cursor = self.connection.cursor()


    def put_item(self, label, content, type):
        self.cursor.execute("""
        INSERT INTO {db_table} (label, content, type) VALUES ('{label}', '{content}', {type}) RETURNING item_id;
        """.format(db_table=DB_TABLE, label=label, content=content, type=type))

        self.connection.commit()

        return str( self.cursor.fetchone()[0] )


    def get_item(self, uuid):
        self.cursor.execute(
            "SELECT item_id, label, content, type FROM {db_table} WHERE item_id = '{uuid}';".format(
                db_table=DB_TABLE, uuid=uuid
            )
        )
        row = self.cursor.fetchone()
        if not row:
            return False
        return dict(uuid=str(row[0]), label=row[1], content=row[2], type=row[3])


    def get_items(self, uuids):
        query_string = 'item_id IN ({})'.format(', '.join(['%s'] * len(uuids)))

        sql_statement = 'SELECT item_id, label, content, type FROM {db_table} WHERE {query_string};'.format(
            db_table=DB_TABLE, query_string=query_string
        )
        self.cursor.execute(sql_statement, uuids)

        return [dict(uuid=str(row[0]), label=row[1], content=row[2], type=row[3]) for row in self.cursor.fetchall()]


    def drop_item(self, uuid):
        if self.get_item(uuid):
            self.cursor.execute("DELETE FROM {db_table} WHERE item_id = '{uuid}';".format(db_table=DB_TABLE, uuid=uuid))
            self.connection.commit()
            return True

        return False


    def close(self):
        self.connection.close()