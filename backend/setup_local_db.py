import mysql.connector
from mysql.connector import errorcode

# XAMPP Defaults
config = {
  'user': 'root',
  'password': '',
  'host': '127.0.0.1',
}

DB_NAME = 'nailvital'

def create_database(cursor):
    try:
        cursor.execute(
            f"CREATE DATABASE {DB_NAME} DEFAULT CHARACTER SET 'utf8'")
    except mysql.connector.Error as err:
        print(f"Failed creating database: {err}")
        exit(1)

def setup():
    try:
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()
        
        try:
            cursor.execute(f"USE {DB_NAME}")
            print(f"Database '{DB_NAME}' already exists.")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                create_database(cursor)
                print(f"Database '{DB_NAME}' created successfully.")
            else:
                print(err)
                exit(1)
        
        cursor.close()
        cnx.close()
        print("\n[READY] Local MySQL setup complete. You can now run the backend!")
        
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your username or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

if __name__ == "__main__":
    setup()
