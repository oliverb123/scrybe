import sqlite3 as sql
import time

class Note:
    def __init__(self, noteId=-1, title="", body="", createTime=-1, archived=0, tags=""):
        self.title = str(title)
        self.body = str(body)
        self.createTime = float(createTime)
        self.id = int(noteId)
        self.archived = int(archived)
        self.tags = [tag.strip() for tag in tags.split(",")]

class ConnectionHandler:
    def __init__(self, dbName="scrybe.db"):
        self.dbName = dbName
        self.conn = sql.connect(self.dbName)
    
    def __del__(self):
        self.conn.commit()
        self.conn.close()

    def getNotes(self, mode="current"):
        command = "SELECT * FROM notes "
        modeSelector = {"current":"WHERE archived = 0;", 
                        "archived":"WHERE archived = 1;",
                        "all":";"}
        command += modeSelector[mode]
        c = self.conn.cursor()
        c.execute(command)
        notes = []
        for note in c:
            newNote = Note(noteId=note[0], 
                           title=note[1], 
                           body=note[2],
                           createTime=note[3],
                           archived=note[4],
                           tags=note[5])
            notes.append(newNote)
        return(notes)

    def getNote(self, noteId=None):
        if(not noteId):
            raise IndexError("Cannot retrieve note of index None")
        command = "SELECT * FROM notes WHERE id = ?;"
        c = self.conn.cursor()
        c.execute(command, (noteId,))
        notesFetch = c.fetchall()
        if(not notesFetch):
            raise IndexError("No note found of index " + str(noteId))
        noteInfo = notesFetch[0]
        note = Note(noteId=noteInfo[0],
                    title=noteInfo[1],
                    body=noteInfo[2],
                    createTime=noteInfo[3],
                    archived=noteInfo[4],
                    tags=noteInfo[5])
        return(note)

    def addNote(self, title=None, body="", tags=""):
        if(not title):
            raise ValueError("Notes require a title")
        command = "INSERT INTO notes VALUES (NULL,?,?,?,0,?);"
        c = self.conn.cursor()
        c.execute(command, (str(title), str(body), time.time(), tags))
        self.conn.commit()
        return(self)

    def editNote(self, noteId=None, title=None, body="", tags=""):
        if(not noteId):
            raise IndexError("Note index required to edit note")
        if(not title):
            raise ValueError("Cannot edit note to have an empty title")
        command = "UPDATE notes SET title = ?, body = ?, tags = ? WHERE id = ?;"
        c = self.conn.cursor()
        c.execute(command, (title, body, tags, noteId))
        self.conn.commit()
        return(self.getNote(noteId))

    def archiveNote(self, noteId=None, archived=1):
        if(not noteId):
            raise IndexError("Note index required to archive note")
        command = "UPDATE notes SET archived = ? WHERE id = ?;"
        c = self.conn.cursor()
        c.execute(command, (archived, noteId))
        self.conn.commit()
        return(self.getNote(noteId))

    def deleteNote(self, noteId=None):
        if(not noteId):
            raise IndexError("Note index required to delete note")
        command = "DELETE FROM notes WHERE id = ?;"
        c = self.conn.cursor()
        c.execute(command, (noteId,))
        self.conn.commit()
        return(self)

    def getNoteCount(self, mode="current"):
        command = "SELECT COUNT(id) FROM notes "
        modeSelector = {"current":"WHERE archived = 0;",
                        "archived":"WHERE archived = 1;",
                        "all":";"}
        command += modeSelector[mode]
        c = self.conn.cursor()
        c.execute(command)
        return(c.fetchall()[0][0])
