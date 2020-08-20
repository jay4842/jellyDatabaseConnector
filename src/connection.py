import pymysql
import paramiko
import sqlite3
import os
import traceback
from sshtunnel import SSHTunnelForwarder
from os.path import expanduser
# https://stackoverflow.com/questions/21903411/enable-python-to-connect-to-mysql-via-ssh-tunnelling
# https://stackoverflow.com/questions/55617520/unable-to-make-tls-tcp-connection-to-remote-mysql-server-with-pymysql-other-too
# TODO - finish reformatting and commenting
#      - need to remove dotenv
class MySqlConnection():
  """ helps establish a connection with an SQL remote database through SSH tunneling 
      calling execute_query() will establish connections if not called before
  """
  def __init__(self, sql_host, sql_user, sql_pass,
              sql_db_name, ssh_host, ssh_user, ssh_pass,
              ssh_key=None, local_db=False, debug=False, log_func=print):
    """init a MySqlConnection through ssh tunneling by using PyMySQL.

    Args:
        sql_host (str): the mysql servers ip on the remote server (usually localhost(127.0.0.1))
        sql_user (str): the mysql user you wish to connect with
        sql_pass (str): the password for the user you are connecting with
        sql_db_name (str): the database on the server you are connecting to
        ssh_host (str): the server to be used for ssh tunneling. (the ip of the server that is running the mysql server)
        ssh_user (str): the ssh user you are connecting with
        ssh_pass (str): the password for the ssh user.
        ssh_key (str, optional): the path to the keyfile if you are connecting to a server that requires a key. Defaults to None.
        local_db (bool, optional):set to true if you are connecting to a server that is on the machine you are running this with. Defaults to False.
        debug (bool, optional): set to true for additional output. Defaults to False.
        log_func (function, optional): the function you wish to log output with. Defaults to print.
    """
    self.sql_host = sql_host
    self.sql_user = sql_user
    self.sql_pswd = sql_pass
    self.database_name = sql_db_name
    self.ssh_host = ssh_host
    self.ssh_user = ssh_user
    self.ssh_pass = ssh_pass
    self.ssh_key_file = ssh_key
    self.sql_port = 3306
    self.ssh_port = 22
    self.tunnel = None
    self.sql_conn = None
    self.local_db = False
    self.log_func = log_func
    self.local_db = local_db

  def __del__(self):
    self.close_connection()

  def establish_tunnel(self):
    """establishes the ssh tunnel if needed

    Returns:
        int : 1 for connected, 0 for not connected
    """
    self.log_func("Establishing SHH Tunnel...")

    if(not self.local_db):
      if(self.ssh_key_file == 'None'):
        self.tunnel = SSHTunnelForwarder(
                (self.ssh_host, self.ssh_port),
                ssh_username=self.ssh_user,
                ssh_password=self.ssh_pass,
                remote_bind_address=(self.sql_host, self.sql_port))
      else:
        mypkey = paramiko.RSAKey.from_private_key_file(self.ssh_key_file)
        self.tunnel = SSHTunnelForwarder(
                (self.ssh_host, self.ssh_port),
                ssh_username=self.ssh_user,
                ssh_pkey=mypkey,
                remote_bind_address=(self.sql_host, self.sql_port))

    if(self.tunnel is not None):
      self.tunnel.start()
      return 1# if (self.tunnel.is_active) else 0
    return 0

  def establish_connection(self):
    """establish the mysql connection

    Returns:
        int: 1 if connects 0 if fails
    """
    try:
      if((self.tunnel is None and not self.local_db) or (self.sql_conn is None and self.local_db)):
        self.establish_tunnel()
      self.log_func("Establishing MySQL Connection...")
      if(self.local_db):
        self.sql_conn = pymysql.connect(host='localhost',
                        user=self.sql_user,
                        password=self.sql_pswd,
                        db=self.database_name,
                        charset='utf8mb4',
                        cursorclass=pymysql.cursors.DictCursor)
      else:
        self.sql_conn = pymysql.connect(host='localhost', user=self.sql_user,
                        passwd=self.sql_pswd, db=self.database_name,
                        port=self.tunnel.local_bind_port,
                        ssl={"fake_flag_to_enable_tls": True})
    except Exception as ex:
      self.log_func(f'{ex}')
      self.log_func(traceback.format_exc())
    return 1 if (self.sql_conn != None) else 0

  def execute_query(self, query, values=None):
    """execute a single query string.

    Args:
        query (str): the query string you wish to execute
        values (tuple of values, optional): . Defaults to None.

    Returns:
      list of values
    """
    # print(query)
    # print(values)
    # if you want to use ssh password use - ssh_password='your ssh password', bellow
    data = None
    #self.log_func('executing query: {}'.format(query))
    if(self.sql_conn is None):
      self.establish_connection()
    cursor = self.sql_conn.cursor()
    try:
      if(values is None):
        data = cursor.execute(query)
        data = cursor.fetchall()
      else:
        if(type(values) is not tuple):
          raise TypeError(f'Values should be of type tuple, type of {type(values)}')
        data = cursor.execute(query, values)
        data = cursor.fetchall()
        if('INSERT' in query or 'UPDATE' in query):
          self.sql_conn.commit()
    except Exception as ex:
      self.log_func(ex)
      self.log_func('query: {}'.format(query))
      self.log_func(f'values: {values}')
      self.log_func(traceback.format_exc())
      cursor.close()
      self.sql_conn.close()
      return []
    #
    cursor.close()
    self.sql_conn.close()
    return data

  def close_connection(self):
    """close the mysql connection
    """
    try:
      #self.sql_conn.close()
      self.sql_conn = None
      self.tunnel = None
    except AttributeError as ex:
      #self.log_func(ex)
      pass

class SQLiteConnection:
  """ helpers to connect to an sqlite3 database """
  def __init__(self, db_file):
    self.db_file = db_file
    self.conn = None
    self.conn_timeout = 0

  # https://www.sqlitetutorial.net/sqlite-python/
  def establish_connection(self):
    """ creates a sqlite3 db connection """
    conn = None
    try:
      conn = sqlite3.connect(self.db_file)
    except sqlite3.Error as e:
      self.log_func(e)
      self.log_func(traceback.format_exc())

    return conn
    
  def close_connection(self):
    self.conn = None
    
  def execute_query(self, statement, values=None):
    if(self.conn is None):
      self.conn = self.establish_connection()
    try:
      if('select' in statement.lower() or 'PRAGMA' in statement):
        c = self.conn.cursor()
        c.execute(statement)
        rows = c.fetchall()
        #return rows
        c = self.conn.cursor()
        c.execute(statement)
        if('insert' in statement.lower() or 'create' in statement.lower()): 
          self.conn.commit()
    except sqlite3.Error as e:
      self.log_func(e)
      self.log_func(statement)
      self.log_func(traceback.format_exc())
      return 0
    return 1