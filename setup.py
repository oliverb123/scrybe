#!/usr/bin/env python
import sqlite3 as sql
import os

def main():
    cwd = os.getcwd() + "/"
    if(os.path.exists(cwd + "scrybe.db")):
        print("Oops, setup.py has already run in this directory")
        print("")
        print("To re-install, make a clean clone of the scrybe repo and")
        print("remove the alias from your ~/.bashrc (or whichever), then")
        print("run 'python setup.py' again.")
        return

    conn = sql.connect(cwd + "scrybe.db")
    c = conn.cursor()
    command = "CREATE TABLE notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL, createTime REAL NOT NULL, archived INTEGER NOT NULL, tags TEXT NOT NULL)"
    c.execute(command)
    conn.commit()
    conn.close()

    #add needed shell file extensions to list
    shellFiles = [".zshrc", ".bashrc"]
    for fileName in shellFiles:
        aliased = False
        #used so we can default to .bashrc on the off chance no .*rc file exists
        fullName = os.environ["HOME"] + "/" + fileName
        if(os.path.exists(fullName)):
            with open(fullName, "a+") as rcFile:
                rcFile.write("alias scrybe='python " + cwd + "scrybe.py" + "'\n")
            aliased = True
        if(not aliased):
            with open(os.environ["HOME"] + "/.bashrc", "a+") as rcFile:
                rcFile.write("alias scrybe='python " + cwd + "scrybe.py" + "'\n")

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

if(__name__ == "__main__"):
    main()
