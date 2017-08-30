import sqlite3 as sql

conn = sql.connect("scrybe.db")
c = conn.cursor()
command = "CREATE TABLE notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL, createTime REAL NOT NULL, archived INTEGER NOT NULL, tags TEXT NOT NULL)"
c.execute(command)
conn.commit()
conn.close()

