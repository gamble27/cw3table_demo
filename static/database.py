import sqlite3


class SQLiteDatabase:
    def __init__(self, filename):
        self.BDname = str(filename)

        self._connection = None
        self._cursor = None

        self.__connect()

    def __connect(self):
        self._connection = sqlite3.connect(self.BDname)
        self._cursor = self._connection.cursor()

    def create_table(self, name, columns):
        '''
        creates table if it does not exist
        :param name:STRING table name
        :param columns: DICTIONARY of STRING columns NAME:TYPE
        :return: None
        '''
        self.__connect()

        buf = []
        for key in columns.keys():
            buf.append(key+' '+columns[key])
        str_params = ', '.join(buf)
        del(buf)

        try:
            self._cursor.execute("""CREATE TABLE IF NOT EXISTS {nom} 
                        ({params})""".format(nom=name,params=str_params))
            # del(str_params)
        except Exception as e:
            print(e)

        self._connection.commit()
        self._connection.close()

    def join(self, tablename, columns):
        """

        :param tablename: STRING
        :param columns: DICTIONARY string col_name:val
        :return: None
        """
        self.__connect()

        values = []
        for key in columns:
            if isinstance(columns[key], str):
                values.append("""'{}'""".format(columns[key]))
            else:
                values.append(str(columns[key]))
        val_str = ','.join(values)

        self._cursor.execute("""INSERT INTO {table} ({keys}) VALUES ({vals})""".format(
            table=tablename, keys=','.join(columns.keys()), vals=val_str
        ))

        self._connection.commit()
        self._connection.close()

    def set(self, tablename, id_field, id, columns):
        '''

        :param tablename: string tablename
        :param id: string chat_id
        :param columns: DICTIONARY 'field':value
        :return: None
        '''

        self.__connect()
        for key in columns:
            if isinstance(columns[key],str):
                self._cursor.execute("""UPDATE {table} SET {field}='{val}' WHERE {id_field} LIKE {id}""".format(
                    table = tablename, field = key, val = columns[key],id_field = id_field, id = id
                ))
            else:
                self._cursor.execute("""UPDATE {table} SET {field}={val} WHERE {id_field} LIKE {id}""".format(
                    table=tablename, field=key, val=columns[key],id_field = id_field, id = id
                ))
        self._connection.commit()
        self._connection.close()

    def find(self, tablename, id_field, id_value, fields='*'):
        self.__connect()
        self._cursor.execute("""SELECT {fieldss} FROM {table} WHERE {id_f}={id_val}""".format(
            fieldss=fields, table=tablename, id_f=id_field, id_val=id_value
        ))
        res = self._cursor.fetchone()
        self._connection.close()
        return res

    def fetchall(self, tablename, condition, fetch_fields='*'):
        """
        fetching the values, dude ;)
        :param tablename: STRING table name
        :param condition: DICTIONARY of STRING fields NAME: VALUE
                == OR ==  condition STRING
        :param fetch_fields: LIST of STRING fields to fetch
        :return: LIST of rows as TUPLES fetched from the table
        """
        self.__connect()
        # DICTIONARY CONDITION
        if type(condition) == dict:
            if len(condition) == 1:
                key = list(condition.keys())[0]
                self._cursor.execute("""SELECT {field} FROM {table} WHERE {id_field}={id}""".format(
                field=','.join(fetch_fields), table=tablename, id_field=key, id=condition[key]
            ))
            else:
                insertion = ' AND '.join(
                    ["{k}={v}".format(k=key, v=condition[key]) for key in condition]
                )
                self._cursor.execute("""SELECT {field} FROM {table} WHERE {cond}""".format(
                    field=','.join(fetch_fields), table=tablename, cond=insertion
                ))
        # STRING CONDITION
        elif type(condition) == str:
            self._cursor.execute("""SELECT {field} FROM {table} WHERE {cond}""".format(
                    field=','.join(fetch_fields), table=tablename, cond=condition
                ))
        res = self._cursor.fetchall()
        self._connection.close()
        return res

    def execute_query(self, query, commit=False):
        self.__connect()
        self._cursor.execute(query)
        if commit:
            self._connection.commit()
        self._connection.close()

    def show_table(self, tablename, fields="*"):
        self.__connect()
        self._cursor.execute("""SELECT {fields} FROM {table}""".format(
            table=tablename, fields=','.join(fields)
        ))
        res = self._cursor.fetchall()
        self._connection.close()
        return res
