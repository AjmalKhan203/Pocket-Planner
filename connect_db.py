import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="ajmal203",
    database="expenses_tracker"
)
print("Connected successfully!")
conn.close()
