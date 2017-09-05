#!/usr/bin/env python
import sqlite3 as sql
import os
import hashlib

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
    aliased = False
    for fileName in shellFiles:
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
        configFile.write("editor:" + editor + "\n")

    with open(cwd + "userLib.py", "r") as userLib:
        userLibString = userLib.read().replace(".scrybe.conf", cwd + ".scrybe.conf")

    with open(cwd + "userLib.py", "w") as userLib:
        userLib.write(userLibString)

#crypto shit
    crypto = raw_input("Encrypt note database at rest(y/n)?: ").strip().lower()
    if(crypto == "y"):
        try:
            from Crypto.Cipher import AES#TODO - Is this good library checking?
        except:
            print("Database encryption relies on the pyCrypto library")
            print("To install it run 'sudo pip install pycrypto'")
            install = raw_input("Do that now? (requires pip)(y/n): ").strip().lower()
            if(install == "y"):#TODO - Is there a better way of doing this?
                os.system("sudo pip install pycrypto")
            else:
                print("Continuing without database encryption")
                return
        #TODO - Is there a cleaner way to do password setting?
        print("Enter a passphrase, and keep it somewhere safe")
        print("Your notes CANNOT be retrieved if you lose it")
        userpass1 = ""
        userpass2 = ""
        while(userpass1 != userpass2 or len(userpass1) < 4):
            userpass1 = raw_input("Passphrase: ")
            userpass2 = raw_input("Repeat passphrase: ")
            if(userpass1 != userpass2):
                print("Sorry, those passwords don't match")
                print("Please try again, or hit control-c")
                print("to finish setup without database encryption")
        userPass = hasher(userpass1)
        with open(cwd + "scrybe.db", "rb") as plainFile:
            plainText = "scrybe" + plainFile.read()#TODO - Prepend iv instead
        while(len(plainText) % 16 != 0):
            plainText += " "
        os.rename(cwd + "scrybe.db", cwd + "scrybe.db.bak")
        iv = "1234567891234567"#TODO - Generate random 16 or better 32 byte iv
        encrypter = AES.new(userPass, AES.MODE_CBC, iv)
        with open(cwd + "scrybe.db.enc", "wb") as encFile:
            encFile.write(encrypter.encrypt(plainText))
        os.remove(cwd + "scrybe.db.bak")#TODO - Is this the best/safest time?
        with open(cwd + ".scrybe.conf", "a") as configFile:
            configFile.write("encrypted:true\n")
            configFile.write("iv:" + iv + "\n")

def hasher(plain):
    i = 0
    while(i < 64000):
        plain = hashlib.md5(plain).hexdigest()#TODO - Think about hashing algo
        i += 1
    return(plain)

if(__name__ == "__main__"):
    main()
