import sqlalchemy

db_user = 'root'
db_password = 'Asdfasdf?1'
db_name = 'db_repo'
db_host = '34.175.137.71'
db_port = '3306'

connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

engine = sqlalchemy.create_engine(connection_string)

with engine.connect() as connection:
    result = connection.execute("SELECT * FROM your_table LIMIT 10;")
    for row in result:
        print(row)
