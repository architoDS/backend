import os
import pyodbc
from config import Config

def get_db_connection():
    try:
        connection_string = 'DRIVER='+Config.DRIVER+';SERVER='+Config.SERVER+';DATABASE='+Config.DATABASE
        if os.getenv("MSI_SECRET"):
            conn = pyodbc.connect(connection_string+';Authentication=ActiveDirectoryInteractive')
            return conn
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return None