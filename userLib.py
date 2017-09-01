import os
import dbLib
import time

class Session:
    def __init__(self):
        self.conn = dbLib.ConnectionHandler()
        self.conf = self.getConfig()

    def getConfig(self):
        conf = {}
        with open(".scrybe.conf", "r") as configFile:
            for line in configFile.readlines():
                if(line.strip() and line.strip()[0] != "#"):
                    try:
                        key, val = line.split(":")
                    except:
                        continue
                    conf[key.strip()] = val.strip()
        return(conf)

    def start(self):
        self.choice = ""
        self.displayHelp()
        while(self.choice.lower() != "q"):
            self.choice = raw_input("->")
            self.parseInput(self.choice)


    def displayHelp(self, choiceList=None):
            print("Options as follows:")
            print("h/H : Display this message")
            print("l/L;[c(urrent - default), a(rchived), b(oth)] : List notes")
            print("s/S;search-string;[c(urrent - default), a(rchived), b(oth)] : Search notes")
            print("a/A;title;[tags - comma-separated] : add a note")
#            print("i/I;title;/path/to/file;[tags] : import a note from file")
            print("arch;note-id;[in - default/out] : move a note into or out of archive")
            print("d/D;note-id : delete a note forever")
            print("e/E;note-id;[title];[tags] : Edit a note that already exists")
            print("g/G;note-id : View a specific note")
            print("c/C: Clear screen")
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
                       "q":self.quit}
        if(choiceList[0] not in choiceFuncs.keys()):
            print("Sorry, " + choiceList[0] + " isn't a valid command (enter 'h' for help)")
            return
        choiceFuncs[choiceList[0]](choiceList)

    def listNotes(self, choiceList):#list all notes in db
        modeSwitchDict = {"c":"current", "a":"archived", "b":"all"}
        if(len(choiceList) < 2):
            choiceList.append("c")
        if(choiceList[1] not in modeSwitchDict.keys()):
            print("Sorry, " + choiceList[1] + " isn't a valid option for list")
            return
        requestMode = modeSwitchDict[choiceList[1]]
        notesList = self.conn.getNotes(mode=requestMode)
        printString = ""
        if(not notesList):
            printString = "No notes found"
        else:
            for note in notesList:
                printString += self.oneLineStringGen(note)
        print(printString)

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

    def searchNotes(self, choiceList):#weighted search of title, body and tags
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
        printString = ""
        for noteTuple in matchingNotes:
            printString += self.oneLineStringGen(noteTuple[0])
        if(printString):
            print(printString)
        else:
            print("Nothing found matching those search terms, sorry")

    def addNote(self, choiceList):#adds a note to the db
        if(len(choiceList) > 2 and choiceList[1]):
            title = choiceList[1]
        else:
            print("Notes require a title")
            return
        tags = ""
        if(len(choiceList) > 2):
            tags = choiceList[2]
        with open(".scrybe.tmp", "w") as tmpFile:
            tmpFile.write("#Note: " + title + "(Esc :wq to save note and quit)")
        os.system(self.conf["editor"] + " .scrybe.tmp")
        with open(".scrybe.tmp", "r") as tmpFile:
            body = ""
            for line in tmpFile.readlines():
                if(line.strip() and line.strip()[0] != "#"):
                    body += line
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
        return(printString)

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
        if(len(choiceList) < 2):
            print("You need to sepcify a note by id")
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
        newTitle = note.title
        if(len(choiceList) > 2 and choiceList[2]):
            newTitle = choiceList[2]
        newBody = note.body
        newTags = ",".join(note.tags)
        if(len(choiceList) > 3 and choiceList[3]):
            newTags = choiceList[3]
        with open(".scrybe.tmp", "w") as tmpFile:
            tmpFile.write(newBody)
        os.system(self.conf["editor"] + " .scrybe.tmp")
        with open(".scrybe.tmp", "r") as tmpFile:
            newBody = ""
            for line in tmpFile.readlines():
                if(line.strip() and line.strip()[0] != "#"):
                    newBody += line
        os.remove(".scrybe.tmp")
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
        self.choice = "q"

    def clear(self, choiceList):
        os.system("clear")

    def importNote(self, choiceList):
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
