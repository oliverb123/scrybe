#!/usr/bin/env python
import sqlite3 as sql
import os

cwd = os.getcwd() + "/"

try:
    os.remove(cwd + "scrybe.db")
except:
    pass

conn = sql.connect(cwd + "scrybe.db")
c = conn.cursor()
command = "CREATE TABLE notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL, createTime REAL NOT NULL, archived INTEGER NOT NULL, tags TEXT NOT NULL)"
c.execute(command)
conn.commit()
conn.close()

with open(os.environ["HOME"] + "/.bashrc", "a+") as bashrc:
    bashrc.write("alias scrybe='python " + cwd + "scrybe.py" + "'\n")

#add needed shell file extensions to list
shellFiles = [".zshrc"]
for fileName in shellFiles:
    fullName = os.environ["HOME"] + "/" + fileName
    if os.path.exists(fullName):
        open(fullName, "a+").write("alias scrybe='python " + cwd + "scrybe.py" + "'\n")

with open(cwd + "dbLib.py", "r") as oldDbLib:
    newDbLibString = oldDbLib.read().replace("scrybe.db", cwd + "scrybe.db")

with open(cwd + "dbLib.py", "w") as newDbLib:
    newDbLib.write(newDbLibString)
    newDbLib.close()

editor = ""
while(editor not in ["vim", "emacs", "nano"]):
    editor = raw_input("Vim, emacs or nano?: ").strip().lower()

with open(cwd + ".scrybe.conf", "a") as configFile:
    configFile.write("editor:" + editor)

with open(cwd + "userLib.py", "r") as userLib:
    userLibString = userLib.read().replace(".scrybe.conf", cwd + ".scrybe.conf")

with open(cwd + "userLib.py", "w") as userLib:
    userLib.write(userLibString)
