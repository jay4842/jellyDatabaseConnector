# mysqlConnectionHelper
A simple wrapper for mysql to support connecting to remote or local databases. Currently mysql support is complete and partial sqlite support.

## Dependencies
- sshtunnel
- paramiko
- PyMySQL

## Installing
```
pip install ...
```

## Usage

The main use of this connector is to connect to a remote database and simplify execution of queries. The below example is how the connector is setup for a remote server connection.
```python
from jellyConnect import queryEngine
# mysql example with remote server
queryEngine = QueryEngine(
                sql_host=SQL_HOST,
                sql_user=SQL_USER, 
                sql_pass=SQL_PASS, 
                sql_db_name=SQL_DB_NAME, 
                ssh_host=SSH_HOST, 
                ssh_user=SSH_USER, 
                ssh_pass=SSH_PASS, 
                ssh_key=SSH_KEY
              )
result = queryEngine.execute_query('select * from testTable;')
print(result)

# passing paramaters
result = queryEngine.execute_query('select * from testTable where id=%s;', values=(id,))
```

If you wish to connect to a database that is hosted on a local network:
```python
# only require database paramaters
queryEngine = QueryEngine(
                sql_host=SQL_HOST,
                sql_user=SQL_USER, 
                sql_pass=SQL_PASS, 
                sql_db_name=SQL_DB_NAME,
                local_db=True
              )
```