
import pg8000


DB_USER = 'postgres'
DB_PASS = 'postgres'
DB_HOST = 'localhost'
DB_PORT = 5432
DB_BASE = 'basf-science'


class Data_Storage(object):

    def __init__(self):

        self.connection = pg8000.connect(
            user=DB_USER,
            password=DB_PASS,
            database=DB_BASE,
            host=DB_HOST,
            port=DB_PORT
        )
        self.cursor = self.connection.cursor()


    def put_item(self, label, content, type):
        self.cursor.execute("""
        INSERT INTO data_items (label, content, type) VALUES ('{label}', '{content}', {type}) RETURNING item_id;
        """.format(label=label, content=content, type=type))

        self.connection.commit()

        return str( self.cursor.fetchone()[0] )


    def get_item(self, uuid):
        self.cursor.execute("SELECT item_id, label, content, type FROM data_items WHERE item_id = '%s';" % uuid)
        row = self.cursor.fetchone()
        if not row:
            return False
        return dict(uuid=str(row[0]), label=row[1], content=row[2], type=row[3])


    def get_items(self, uuids):
        query_string = 'item_id IN ({})'.format(', '.join(['%s'] * len(uuids)))

        sql_statement = 'SELECT item_id, label, content, type FROM data_items WHERE {};'.format(query_string)
        self.cursor.execute(sql_statement, uuids)

        return [dict(uuid=str(row[0]), label=row[1], content=row[2], type=row[3]) for row in self.cursor.fetchall()]


    def drop_item(self, uuid):
        if self.get_item(uuid):
            self.cursor.execute("DELETE FROM data_items WHERE item_id = '%s';" % uuid)
            self.connection.commit()
            return True

        return False


    def close(self):
        self.connection.close()