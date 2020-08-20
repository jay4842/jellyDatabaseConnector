from src.queryEngine import QueryEngine
from dotenv import load_dotenv
import pytest
import os
load_dotenv()

@pytest.fixture
def queryEngine():
  return QueryEngine(sql_host=os.getenv('SQL_HOST'), sql_user=os.getenv('SQL_USER'), sql_pass=os.getenv('SQL_PASS'), 
                    sql_db_name=os.getenv('SQL_DB_NAME'), ssh_host=os.getenv('SSH_HOST'), ssh_user=os.getenv('SSH_USER'), 
                    ssh_pass=os.getenv('SSH_PASS'), ssh_key=os.getenv('SSH_KEY'))

def test_pass_login(queryEngine):
  sql = queryEngine
  result = sql.execute_query('select * from ScheduleItem;')
  print(result)
  sql = None
  assert(len(result) > 0)
  
