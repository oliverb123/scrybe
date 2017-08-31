#!/usr/bin/env python
import sqlite3 as sql
import os

try:
    os.remove("scrybe.db")
except:
    pass

cwd = os.getcwd() + "/"

conn = sql.connect(cwd + "scrybe.db")
c = conn.cursor()
command = "CREATE TABLE notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL, createTime REAL NOT NULL, archived INTEGER NOT NULL, tags TEXT NOT NULL)"
c.execute(command)
conn.commit()
conn.close()

with open(os.environ["HOME"] + "/.bashrc", "a+") as bashrc:
    bashrc.write("alias scrybe='python " + cwd + "scrybe.py" + "'\n")

os.system("python " + cwd + "scrybe.py")

with open(cwd + "dbLib.py", "r") as oldDbLib:
    newDbLibString = oldDbLib.read().replace("scrybe.db", cwd + "scrybe.db")

with open(cwd + "dbLib.py", "w") as newDbLib:
    newDbLib.write(newDbLibString)
    newDbLib.close()

print("Setup Finished, Starting Scrybe")
