import os
import sys
import dbLib
import time
import re
import hashlib

try:
    import readline
except:
    print("Readline module not supported")
    pass

class Session:
    def __init__(self):
        self.conn = dbLib.ConnectionHandler()
        self.conf = self.getConfig()
        if(self.conf["encrypted"] == "true"):
            global AES
            from Crypto.Cipher import AES
            self.decrypt(self.conn.dbName)
        self.conn.connect()

    def getConfig(self):
        conf = {"editor":"vim",
                "encrypted":"false",
                "iv":"1234567891234567"}
        with open(".scrybe.conf", "r") as configFile:
            for line in configFile.readlines():
                if(line.strip() and line.strip()[0] != "#"):
                    try:
                        key, val = line.split(":")
                    except:
                        continue
                    if(key.strip().lower() not in ["iv",]):
                        conf[key.strip().lower()] = val.strip().lower()
                    else:
                        if(key.strip().lower() == "iv"):
                            conf[key.strip().lower()] = val[:-1]
        return(conf)

    def start(self):
        self.choice = ""
        self.displayHelp()
        while(self.choice.lower() != "q"):
            self.choice = raw_input("->")
            self.parseInput(self.choice)

    def displayHelp(self, choiceList=None):
        print("Check the README.md file for command references")
        print("Options as follows:")
        print("h/H : Display this message")
        print("l/L : List notes")
        print("t/T : List tags, and the number of notes each contains")
        print("s/S : Search notes")
        print("f/F : Filter notes")
        print("a/A : Add a note")
#        print("i/I;title;/path/to/file;[tags] : import a note from file")
        print("arch : Move a note into or out of archive")
        print("d/D : Delete a note forever")
        print("e/E : Edit a note that already exists - save an empty file to cancel")
        print("exp : Export a note to a file")
        print("g/G : View a specific note")
        print("c/C : Clear screen")
        print("q/Q : Quit Scrybe")

    def parseInput(self, choiceString):
        if(not choiceString):#user accidentally pressed enter
            return
        choiceList = []
        for choice in choiceString.split(";"):
            choiceList.append(choice.strip())
        choiceList[0] = choiceList[0].lower()
        choiceFuncs = {"h":self.displayHelp,
                       "l":self.listNotes,
                       "s":self.searchNotes,
                       "a":self.addNote,
                       "i":self.importNote,
                       "arch":self.archiveHandler,
                       "d":self.deleteNote,
                       "e":self.editNote,
                       "g":self.getNote,
                       "c":self.clear,
                       "f":self.filter,
                       "t":self.getTags,
                       "q":self.quit,
                       "exp":self.export}
        if(choiceList[0] not in choiceFuncs.keys()):
            print("Sorry, " + choiceList[0] + " isn't a valid command (enter 'h' for help)")
            return
        choiceFuncs[choiceList[0]](choiceList)

    def listNotes(self, choiceList, mode="print"):#list all notes in db
        modeSwitchDict = {"c":"current", "a":"archived", "b":"all"}
        if(len(choiceList) < 2):
            choiceList.append("c")
        if(choiceList[1] not in modeSwitchDict.keys()):
            print("Sorry, " + choiceList[1] + " isn't a valid option for list")
            return
        requestMode = modeSwitchDict[choiceList[1]]
        notesList = self.conn.getNotes(mode=requestMode)
        printString = ""
        if(mode == "print"):
            if(not notesList):
                printString = "No notes found"
            else:
                for note in notesList:
                    printString += self.oneLineStringGen(note)
            print(printString.strip())
        else:
            return(notesList)

    def oneLineStringGen(self, note, maxChars=60):#one line repr of passed note
        noteId = note.id
        title = note.title
        body = note.body
        createTimeString = time.strftime("%d/%m/%Y %H:%M", time.localtime(note.createTime))
        archived = ["Current", "Achived"][note.archived]
        appendString = " | " + createTimeString + " | " + archived + "\n"
        printString = ""
        printString += str(noteId) + " | "
        printString += title + " | "
        printString += body
        printString = printString.replace("\n", " ")
        if(len(printString + appendString) > maxChars):
            appendString = "..." + appendString
            maxLengthBeforeAppend = maxChars - len(appendString)
            printString = printString[0:maxLengthBeforeAppend]
        printString += appendString
        return(printString)

    def searchNotes(self, choiceList, mode="print"):#weighted search of title, body and tags
        if(len(choiceList) < 2):
            print("You need to specify a search string")
            return
        searchTerm = choiceList[1].lower()
        if(len(choiceList) < 3):
            choiceList.append("c")
        if(choiceList[2] not in ["a","b","c"]):
            print("Sorry, " + choiceList[2] + " isn't a valid search option")
            return
        selectorMode = {"c":"current", "a":"archived", "b":"all"}[choiceList[2]]
        matchingNotes = []
        for note in self.conn.getNotes(mode=selectorMode):
            matchValue = 0
            if(searchTerm in note.title.lower()):
                matchValue += 2
            matchValue += note.body.lower().count(searchTerm)
            matchValue += note.tags.count(searchTerm) * 3
            if(time.time() - note.createTime < 7*24*60*60):
                matchValue += 1
            if(matchValue > 0):
                matchingNotes.append((note, matchValue))
        matchingNotes.sort(key=lambda x: x[1], reverse=True)
        if(mode == "print"):
            printString = ""
            for noteTuple in matchingNotes:
                printString += self.oneLineStringGen(noteTuple[0])
            if(printString):
                print(printString.strip())
            else:
                print("Nothing found matching those search terms, sorry")
        else:
            return(matchingNotes)

    def addNote(self, choiceList):#adds a note to the db
        if(len(choiceList) > 2 and choiceList[1]):
            title = choiceList[1]
        else:
            print("Notes require a title")
            return
        tags = ""
        if(len(choiceList) > 2):
            tags = choiceList[2]
            if([char for char in ["(", ")", "[", "]"] if char in tags]):
                print("Brackets (square and rounded) aren't needed for tag")
                print("lists, and will be included as part of the tag they")
                print("are beside, e.g [tag1, tag2] becomes ['[tag1', 'tag2]']")
                print("in the notes tag list. If this wasn't intended, enter")
                print("'c' to cancel, anything else will add a note with the")
                print("tag list as it currently is")
                confirm = raw_input("->")
                if(confirm.lower() == "c"):
                    print("Note addition cancelled")
                    return
        os.system(self.conf["editor"] + " .scrybe.tmp")
        with open(".scrybe.tmp", "r") as tmpFile:
            body = tmpFile.read().strip()
        os.remove(".scrybe.tmp")
        if(not body):
            print("Note addition cancelled due to empty body")
        self.conn.addNote(title, body, tags)
        print("Note added")

    def fullStringGen(self, note):#generates a string repr of an entire note
        noteId = note.id
        title = note.title
        body = note.body
        tagString = "Tags: | "
        for tag in note.tags:
            tagString += tag + " | "
        createTimeString = time.strftime("%d/%m/%Y %H:%M", time.localtime(note.createTime))
        archived = ["Current", "Archived"][note.archived]
        printString = ""
        printString += title + "\n"
        printString += str(noteId) + " | " + createTimeString + " | " + archived  + "\n"
        printString += tagString + "\n"
        printString += body
        return(printString.strip())

    def archiveHandler(self, choiceList):
        if(len(choiceList) < 2):
            print("You need to specify a note to archive")
            return
        try:
            noteId = int(choiceList[1])
        except:
            print("Sorry, note ids need to be an integer")
            return
        archive = 1
        if(len(choiceList) > 2):
            if(choiceList[2].lower() not in ["in", "out"]):
                print("Sorry, " + choiceList + " isn't an option for archive")
                return
            archive = {"out":0, "in":1}[choiceList[2]]
        self.conn.archiveNote(noteId, archive)
        print("Note archived")

    def deleteNote(self, choiceList):
        if(len(choiceList) < 2):
            print("You must specify a note to be deleted")
            return
        try:
            noteId = int(choiceList[1])
        except:
            print("Note index must be an integer")
            return
        verify = raw_input("Are you sure (y/n)?")
        if(verify.strip().lower() == "y"):
            self.conn.deleteNote(noteId)
            print("Note deleted")
        else:
            print("Deletion cancelled")

    def editNote(self, choiceList):
#boilerplate to check if the mandatory params are ther
        if(len(choiceList) < 2):
            print("You need to specify a note by id")
            return
        try:
            noteId = int(choiceList[1])
        except:
            print("Note id must be an integer")
            return
        try:
            note = self.conn.getNote(noteId)
        except:
            print("No note found of that id (did you delete it?)")
            return
#end of boilerplate
        newTitle = note.title
        if(len(choiceList) > 2 and choiceList[2]):
            newTitle = choiceList[2]
        oldBody = note.body
        newTags = ",".join(note.tags)
        if(len(choiceList) > 3 and choiceList[3]):
            if(choiceList[3][0] == "+"):#append mode for tag modification
                newTags += "," + choiceList[3][1:]
            else:#otherwise replace mode
                newTags = choiceList[3]
        with open(".scrybe.tmp", "w") as tmpFile:
            tmpFile.write(oldBody)
        os.system(self.conf["editor"] + " .scrybe.tmp")
        with open(".scrybe.tmp", "r") as tmpFile:
            newBody = tmpFile.read().strip()
            if(not newBody):#if the user saved an empty file, cancel edit
                print("Edit cancelled due to empty note body")
                return
        os.remove(".scrybe.tmp")
        if(newBody == oldBody and newTags == note.tags):
            print("Note edit cancelled")
            return
        self.conn.editNote(noteId, newTitle, newBody, newTags)
        print("Note " + str(noteId) + " edited")

    def getNote(self, choiceList):
        if(len(choiceList) < 2):
            print("You need to specify a note by it's id (number on the left)")
            return
        try:
            requestId = int(choiceList[1])
        except:
            print("Note ids need to be integers")
            return
        try:
            note = self.conn.getNote(requestId)
        except IndexError:
            print("Sorry, there's no note with that id (did you delete it?)")
            return
        print(self.fullStringGen(note))

    def quit(self, choiceList):
        if(self.conf["encrypted"] == "true"):
           self.encrypt(self.conn.dbName)
        self.choice = "q"

    def clear(self, choiceList):
        os.system("clear")

    def importNote(self, choiceList):#NOTE - currently hidden from the user
        if(len(choiceList) < 3):
            print("You must specify title and path when importing a file")
            return
        title = choiceList[1]
        path = choiceList[2]
        tags = ""
        if(len(choiceList) > 3):
            tags = choiceList[3]
        try:
            with open(path, "r") as noteFile:
                body = noteFile.read()
        except:
            print("Sorry, failed to read file. Did you get the path right?")
            return
        self.conn.addNote(title, body, tags)
        print("Note imported")

    def filter(self, choiceList, printMode="print"):#function to work out filter mode; date or tag
        if(len(choiceList) < 4):
            self.tagFilter(choiceList, printMode)
        elif(choiceList[3].lower() not in ["t", "d"]):
            print("Sorry, " + choiceList[3] + " isn't a valid filter mode")
        else:
            filterMatch = {"t":self.tagFilter, "d":self.dateFilter}
            filterMatch[choiceList[3].lower()](choiceList, printMode)

    def tagFilter(self, choiceList, printMode="print"):
        if(len(choiceList) < 2 or not choiceList[1]):
            print("You need to supply at least one tag to filter by")
            return
        modeSelector = {"a":"archived", "b":"all", "c":"current"}
        if(len(choiceList) > 2 and choiceList[2]):#choose note get mode
            if(choiceList[2] not in modeSelector.keys() and printMode=="print"):
                print("Sorry, " + choiceList[2] + " isn't a valid option")
                return
            mode = modeSelector[choiceList[2]]
        else:
            mode = modeSelector["c"]
        tagList = [tag.strip() for tag in choiceList[1].split(",")]
        excludeList = [tag[1:] for tag in tagList if tag[0] == "-"]
        includeList = [tag for tag in tagList if tag[0] != "-"]
        notes = self.conn.getNotes(mode)
        if(printMode == "print"):
            printString = ""
            for note in notes:
                matchTags = [tag for tag in includeList if tag in note.tags]
                excTags = [tag for tag in excludeList if tag in note.tags]
                if(len(matchTags) == len(includeList) and not excTags):
                    printString += (self.oneLineStringGen(note))
            if(not printString):
                printString = "Sorry, nothing matching that filter found"
            print(printString.strip())
        else:
            return(notes)

    def getTags(self, choiceList, printMode="print"):
        notes = self.conn.getNotes()
        tagPairs = []
        for note in notes:
            for tag in note.tags:
                tagList = [tagPair[0] for tagPair in tagPairs]
                if(tag in tagList):
                    tagPairs[tagList.index(tag)][1] += 1
                else:
                    tagPairs.append([tag, 1])
        if(printMode == "print"):
            if(not tagPairs):
                print("You haven't tagged anything")
                return
            for tagPair in tagPairs:
                print(" | " + tagPair[0] + " : " + str(tagPair[1]) + " | ")
        else:
            return(tagPairs)

    def dateFilter(self, choiceList, printMode="print"):
        #TODO -- See if you can clean this up
        choiceList[1] = choiceList[1].lower()
        lowPass = time.time()
        highPass = 0
        keywordMap = {"day":60*60*24,
                      "week":60*60*24*7,
                      "month":60*60*24*7*31,
                      "quarter":60*60*24*7*31*3,
                      "year":60*60*24*365}#hazy second-to-keyword mapping
        singleDate = "\d\d/\d\d\/\d\d\d\d"
        singleDateRe = re.compile("^"+singleDate+"$")
        doubleDateRe = re.compile("^"+singleDate + ":" + singleDate+"$")
        if(choiceList[1] in keywordMap.keys()):
            lowPass -= keywordMap[choiceList[1]]
        elif(singleDateRe.match(choiceList[1])):
            lowPass = time.mktime(time.strptime(choiceList[1], "%d/%m/%Y"))
        elif(doubleDateRe.match(choiceList[1])):
            dates = choiceList[1].split(":")
            lowPass = time.mktime(time.strptime(dates[0], "%d/%m/%Y"))
            highPass = time.mktime(time.strptime(dates[1], "%d/%m/%Y"))
        else:
            if(printMode == "print"):
                print("Sorry, that date format isn't valid")
            return
        if(not highPass):
            highPass = time.time()
        modeSelector = {"a":"archived", "b":"all", "c":"current"}
        mode = "current"
        if(choiceList[2]):
            if(choiceList[2] in modeSelector.keys()):
                mode = modeSelector[choiceList[2]]
            else:
                if(printMode == "print"):
                    print("Sorry, " + choiceList[2] + " isn't a valid option")
                return
        notes = self.conn.getNotes(mode)
        if(not notes and printMode == "print"):
            print("You don't have any notes to filter")
        matchingNotes = []
        for note in notes:
            if(note.createTime > lowPass and note.createTime < highPass):
                matchingNotes.append(note)
        matchingNotes.sort(key = lambda x: x.createTime, reverse=True)
        if(printMode == "print"):
            printString = ""
            for note in matchingNotes:
                printString += self.oneLineStringGen(note)
            print(printString.strip())
        else:
            return(matchingNotes)

    def export(self, choiceList):#dumps the body of a note into a file
        if(len(choiceList) < 2 or not choiceList[1]):
            print("Sorry, you need to specify a note id")
            return
        try:
            noteId = int(choiceList[1])
        except:
            print("Sorry, note id needs to be an integer")
            return
        try:
            note = self.conn.getNote(noteId)
        except IndexError:
            print("Sorry, that note doesn't exist (did you delete it?)")
            return
        fileName = note.title
        if(len(choiceList) > 2 and choiceList[2]):
            fileName = choiceList[2]
        if(fileName[0] == "~"):
            fileName = os.path.join(os.environ["HOME"], fileName[1:])
        if(fileName[-1] == "/"):
            fileName = os.path.join(fileName, note.title)
        fileText = ""
        fileText += note.title + " | "
        fileText += time.strftime("%d/%m/%Y %H:%M", time.localtime(note.createTime))
        fileText += " | "
        for tag in note.tags:
            fileText += tag + " | "
        fileText = fileText[:-3]
        fileText += "\n\n"
        fileText += note.body
        try:
            with open(fileName, "w") as exportFile:
                exportFile.write(fileText)
        except:
            print("Sorry, scrybe couldn't open " + fileName)
            print("Are you sure it exists?")
            return
        print("Note exported to " + fileName)

    def encrypt(self, dbName):
        iv = self.iv
        userPass = self.userPass#use passphrase hash generated on decryption
        with open(dbName, "rb") as plainFile:
            plainText = iv + plainFile.read()
        os.rename(dbName, dbName + ".bak")
        while(len(plainText) % 16 != 0):
            plainText += " "
        encText = iv + AES.new(userPass, AES.MODE_CBC, iv).encrypt(plainText)
        with open(dbName + ".enc", "wb") as encFile:
            encFile.write(encText)
        os.remove(dbName + ".bak")#NOTE - only remove backup after write
    
    def decrypt(self, dbName):
        userPass = hasher(raw_input("Enter passphrase: "))
        with open(dbName + ".enc", "rb") as encFile:
            encText = encFile.read()
        iv = encText[:16]#pull iv from front of ciphertext
        encText = encText[16:]#strip iv from cipherText
        plainText = AES.new(userPass, AES.MODE_CBC, iv).decrypt(encText)
        if(plainText[0:16] != iv):
            print("Decryption failed, likely due to a wrong password.")
            print("Exiting")
            sys.exit()
        #remove padding
        while(plainText[-1] == " "):
            plainText = plainText[:-1]
        self.iv = iv#Store iv for encrpytion later
        self.userPass = userPass#Store good userpass for encryption later
        if(os.path.exists(dbName)):
            os.remove(dbName)
        with open(dbName, "wb") as plainFile:
            plainFile.write(plainText[16:])
            plainFile.flush()


def hasher(plain):
    i = 0
    while(i < 64000):
        plain = hashlib.sha256(plain).digest()
        i += 1
    return(plain)
