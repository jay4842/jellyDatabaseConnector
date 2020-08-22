import platform
import subprocess
from .connection import MySqlConnection, SQLiteConnection
  
def ping_mysql_server(host):
  """
  from: https://stackoverflow.com/a/32684938/4231495
  Returns True if host (str) responds to a ping request.
  Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
  
  Putting this here because the server can be in idle, and this will cause a sql connection to fail.
  """
  # Option for the number of packets as a function of
  param = '-n' if platform.system().lower()=='windows' else '-c'

  # Building the command. Ex: "ping -c 1 google.com"
  command = ['ping', param, '1', host]
  return subprocess.call(command) == 0

class QueryEngine():
  """ How queries will be called. Will overllay the connector types like mysql or sqlite """
    
  def __init__(self, db_type='mysql', sql_host=None, sql_user=None, 
              sql_pass=None, sql_db_name=None, ssh_host=None, ssh_user=None, ssh_pass=None,
              ssh_key=None, local_db=False, db_file=None, debug=False, log_func=print):
    """ the QueryEngine object lets you connect to a mysql server.
        mysql helper is in progress.
    Args:
        db_type (str, optional): set what type of database you wish to connect to. Defaults to 'mysql'.
        local_db (bool, optional): set to true if the server is on your local network. Defaults to False.
        db_file (str, optional): if using an sqlite connection, provdide the file you wish to connect to. Defaults to None.
        debug (bool, optional): set to true if you wish to see debug output statements. Defaults to False.
        log_func (function, optional): set to something other than print if you wish to log output differently. Defaults to print.
    Returns:
        QueryEngine object
    """
    self.db_type = db_type
    self.db = None
    if(db_type == 'mysql'):
      self.db = MySqlConnection(sql_host, sql_user, sql_pass,
                                sql_db_name, ssh_host, ssh_user, ssh_pass,
                                ssh_key, local_db, debug, log_func)
    elif(db_type == 'sqlite'):
      if(db_file is None):
        default_sqlite = './sqlite.db'
        db_file = default_sqlite
      self.db = SQLiteConnection(db_file)
    self.executing = False
    self.idle_timer = 0
    self.debug = debug
    self.idle_timer = 0
    self.timeout = 60 * 5 # 5 mins
    
  def close_connection(self):
    """ Close the connection based on the loaded connection type """
    self.db.close_connection()

  def execute_querys(self, queries, values=None):
    """execute many querys and return a list of query results

    Args:
        queries (list[string]): the list of query strings you wish to execute
        values (list(tuple) or a tuple(tuple), optional): if using placeholder values in any of your queries in the list, 
          this should be a list that matches the lenth of the query string list, use a None value if there are no placeholders for a query. Defaults to None.

    Returns:
        list(list): a list of query results in the form of a list
    """
    if(self.debug):
      self.output_func('creating execution process')

    ping_mysql_server()
    results = []
    if(values != None and len(queries) != len(values)):
      self.output_func('queries and values should be the same length!')
      return results

    for idx,query in enumerate(queries):
      if(values != None):
        results.append(self.db.execute_query(query, values=values[idx]))
      else:
        results.append(self.db.execute_query(query))
    self.db.close_connection()
    return results
    
  def execute_query(self, query, values=None):
    """execute a single query string.

    Args:
        query (str): the query string you wish to execute
        values (tuple of values, optional): . Defaults to None.

    Returns:
      list of values
    """
    result = self.db.execute_query(query, values)
    if (self.db_type == 'sqlite'):
      result = [result]
    self.db.close_connection()
    return result
    
  def update(self):
    if(self.idle_timer > 0):
      self.idle_timer-=1
        
    if(self.idle_timer <= 0):
      self.close_connection()
    
  def get_current_server_timestamp(self):
    if(self.db_type == 'mysql'):
      return self.execute_query('select NOW();')[0]
    else:
      return None

  # TODO - need to finish this feature
  #def select_next_id(self, table_name):
  #  query = 'SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE'

  def create_insert_prepared_statement(self, table_name):
    """return an insert prepared statement for a given table

    Args:
        table_name (str): the table name you wish to insert into

    Returns:
        str: the instert prepared statement
    """
    if(self.db_type == 'mysql'):
      ref_schema = self.execute_query(f'desc {table_name};')
      keys = [] # the keys that are valid for insert
      value_placeholders = []
      for item in ref_schema:
        if('auto_increment' not in item and 'DEFAULT_GENERATED' not in item):
          keys.append(item[0])
          value_placeholders.append('%s')
        keys = tuple(keys)
        value_placeholders = tuple(value_placeholders)
        statement = f'INSERT INTO {table_name}{keys} VALUES{value_placeholders}'.replace('\'', '')
      if(len(keys) == 1):
        statement = statement.replace(',','')
      return statement
    # TODO: Implement sqlite insert generation
    # elif(self.db_type == 'sqlite'):
    #   table_name = 'stockRef'
    #   ref_schema = self.execute_query(f'PRAGMA table_info({table_name});')
    #   auto_increment_schema = self.execute_query(f'SELECT is-autoincrement FROM sqlite_master WHERE tbl_name={table_name} AND sql LIKE %AUTOINCREMENT%')
    #   schema = self.execute_query(f'select sql from sqlite_master where name=\'{table_name}\';')
    #   #ref_schema = conn.execute_query(f'PRAGMA table_info(stockRef);')
    #   print(ref_schema )
    #   print()
    #   print(auto_increment_schema)
    #   print()
    #   print(schema)
    #   input('->')

  def create_update_prepared_statement(self, table_name, condition='id=%s'):
    """create an update statement for a given table

    Args:
        table_name (str): table you wish to create an update statement for
        condition (str, optional): condition for the where statement needed in an update call. Defaults to 'id=%s'.

    Returns:
        str : query string for an update call
    """
    stock_ref_schema = self.execute_query(f'desc {table_name};')
    statement = f'UPDATE {table_name} '
    for idx, item in enumerate(stock_ref_schema):
      if('auto_increment' not in item):
        if('SET' not in statement):
          statement += 'SET ' + f'{item[0]}' + '=%s,'
        else:
          statement += '' + f'{item[0]}' + '=%s,'
    statement = statement[0:len(statement)-1]
    statement += f' WHERE {condition};'
    return statement