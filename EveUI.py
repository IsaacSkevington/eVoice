MYSQL = "mysql"
MICROSOFTSQL = "mssql"


##############################################################################################
#############################CHANGE SERVER DETAILS HERE !!!!!!!!!!!!!#########################
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV#

SERVERADDRESS="evoice.cermmtd1vgvf.eu-west-2.rds.amazonaws.com"
PORT=3306
USERNAME="eVoice"
PASSWORD="latymerevoice"
DATABASE="evoice"
SERVERARCHITECTURE = MYSQL #Change this from MYSQL to MICROSOFTSQL depending on what the server is running


##############################################################################################

#Imports
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog
from PIL import ImageTk ,Image
from tkcalendar import Calendar, DateEntry
import random
import time
import mysql.connector
import pyodbc
import xlsxwriter
from datetime import date
from datetime import datetime
import os
import os.path
import copy
import requests
import ctypes
import sys
import pickle
import glob

##############Global variables

#Login page
backgroundLabel = None #Background label window
loginFrame = None #Login window
loginButton = None #Login button
usernameEntry = None #The username entry box
passwordEntry = None #The password entry box

#Login details
userName = '' #Username 
passWord = '' #Password

#Form
toDoArea = None #Do do surveys window
missingArea = None #Missing surveys window
formFrame = None #Window for the forms
classID = None #Class ID (unique based on form)
questionFrame = None #The window for answering questions
people = None #Number of people in a class

#Answering surveys
addRowButtons = {} #List of buttons to add answer rows
removeRowButtons = {} #List of buttons to remove answer rows
surveyArea = None #The window in which a survey is taken
classNameMap = {} #The map of classIDs to class names (for efficiency)
firstTimeClassName = True #Variable storing whether the class name map has been populated
surveyTitle = None #The title of the survey

#School council
schoolCouncilFrame = None #School councillor window
accessLevel = None #The access level of a councillor
createNewAccountsArea = None #The create new account window
statisticsArea = None #The window in which survey stats are displayed
passArea = None #The area a new password is entered
userdatalabels = [] #List of users searched for

#Creating surveys
firstAddButton = None #The handle to the first question add button
incorrectSurveyLabel = None #The label displaying an error in survey creation
createNewSurveyArea = None #The create new survey window
questionEntries = [] #List of boxes in which to enter questions

#New users
newPass = '' #The new password
newPassEntry = None #The new password entry box
newUserSurnameEntryBox = None #The new surname entry box
newUserFirstnameEntryBox = None #The new first name entry box
newUserUsernameEntryBox = None #The new username entry box
newUserPasswordEntryBox = None #The new password entry box
setAccessLevelEntry = None #Entry drop down to choose access level
newUserSurnameEntry = '' # The entry data into the newSurname box
newUserFirstnameEntry = '' #The entry data into the newFirstname box
newUserUsernameEntry = '' #The entry data into the newUsername box
newUserPasswordEntry = '' #The entry data into the newPassword box
newAccessLevel = '' #The entry data into the new accessLevel box

#Deleting users
toDeleteUsernameEntry = None #The entry box for the username to delete
toDeleteUsername = '' #The username to delete

#Offline surveys
offline = False #Whether the user is offline
offlineSurvey = None #The handle to the offline survey
offlinePeople = 0 #The number of people offline
offlineclass= None #The class name when offline

#Misc
save = None #Save function
popupWin =None #A pop up window global handle
allClassesList = [] #A list of all classes


###########Constants
VERSION = 4 #Program version
TWOSAME = "¬||¬||¬||¬" #Constant that can be returned (Akin to false, prevents autotyping issues)
QUESTIONTYPEOPTIONS = 0 #Options question
QUESTIONTYPEOPEN = 1 #Open question
ID_QUESTIONTYPE = 2 #Question type array index
ID_QUESTIONID = 0 #Question ID array index
ID_QUESTIONBODY = 1 #Question Body array index
ID_SURVEYOR = 0 #Surveyor type
ID_CLASS = 1 #Class type
ID_CLASS_NEW = 2 #New class type
ACCESSLEVELR = 0 #Read permissions - view surveys and download
ACCESSLEVELRW = 1 #Write permissions - add new and alter old surveys/questions
ACCESSLEVELA = 2 #Add and remove councillor users, classes - administrator
ACCESSLEVELS = 3 #Add and remove administrators - system
ACCESSLEVELP = 4 #Program access level - program uses to automatically add and delete users

#return relative_path
def resourcePath(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


###########################QUESTION CLASSES


#A question - takes all the parameters stored in the DB
class Question:
    def __init__(self, questionID, surveyID, questionType, questionBody, questionNumber, targetYears):
        self.questionID = questionID
        self.surveyID = surveyID
        self.questionType = questionType
        self.questionBody = questionBody
        self.questionNumber = questionNumber
        self.targetYears = targetYears


#An answer - takes all the parameters stored in the DB
class Answer:
    def __init__(self, className, questionID, answerType, answerList, complete):
        self.className = className
        self.questionID = questionID
        self.answerType = answerType
        self.answerList = answerList
        self.complete = complete
    
#A full survey - consists of a list of questions, answers and survey information
class Survey:
    def __init__(self, surveyID, name, questionIDs, people = None):
        self.questionIDs = questionIDs
        self.name = name
        self.surveyID = surveyID
        self.questions = []
        self.answers = []
        self.classID = None
        self.people = people

    #Fetch the information from the server
    def getInformation(self):
        for questionID in self.questionIDs:
            sql = "Select * from Question where questionID = " + str(questionID)
            csr.execute(sql)
            qd = csr.fetchall()[0]
            q = Question(qd[0],qd[1],qd[2],qd[3],qd[4], targetYearsParse(qd[5]))
            self.questions.append(q)

    #Submit infomation to the server
    def setInformation(self):
        classID = getClassID(self.answers[0].className)
        if getClassPeople(classID) == -1:
            self.people = 30
            changeClassPeople(classID, self.people, ACCESSLEVELP)
        for answer in self.answers:
            if answer.complete == 1:
                submitAnswer(answer.answerList, answer.questionID, classID, answer.answerType, offlineAnswer = True)

    #Gets a list of questions to do
    def getQuestions(self):
        global offlineclass
        outQuestions = []
        for question in self.questions:
            if getYear(name = offlineclass) in question.targetYears:
                inAnswer = False
                for answer in self.answers:
                    if answer.questionID == question.questionID :
                        if answer.complete == 0:
                            outQuestions.append(question)
                            break
                        inAnswer = True   
                if not inAnswer:
                    outQuestions.append(question)
        return outQuestions



#A scrollable frame - take the width, height and background colour, along with the parent (container)
#width and height aren't needed if pack is used to display
#You should pack the ScrollableFrame object itself
#But the parent window for children should be the scrollable frame (ScrollableFrane.scrollableFrame)
class ScrollableFrame(tk.Frame):
    def __init__(self, container, verticalSB = True, horizontalSB = False, height= -1, width=-1, *args, **kwargs):
        """Pass in height, width and background colour"""
        super().__init__(container, *args, **kwargs)
        if verticalSB and horizontalSB:
            raise ValueError("Cannot have more than one scrollbar in a window.\n Please put horizontal Scrollable frame IN vertical one")

        if height == -1 and width == -1:
            self.canvas = tk.Canvas(self,highlightthickness=0)
        else:
            self.canvas = tk.Canvas(self, height = height, width = width, highlightthickness=0)

        if verticalSB:
            vscrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        if horizontalSB:
            hscrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.scrollableFrame = tk.Frame(self.canvas)
        self.scrollableFrame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollableFrame, anchor="nw")
        if verticalSB:
            self.canvas.configure(yscrollcommand=vscrollbar.set)
        if horizontalSB:
            self.canvas.configure(xscrollcommand=hscrollbar.set)
        
        if verticalSB:
            vscrollbar.pack(side="right", fill="y")
            self.canvas.pack(side="left", fill="both", expand=True, anchor = 'nw')
        if horizontalSB:
            hscrollbar.pack(side="bottom", fill="x")
            self.canvas.pack(side="top", fill="both", expand=True, anchor = 'nw')

        self.canvas.bind('<Configure>', self.FrameWidth)

    def FrameWidth(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame, width = canvas_width)


#A Popup window with some text and if an entry box should be displayed
class PopupWindow(object):
    def __init__(self, parent, text, entryBoxNeeded = True):
        top=self.top=tk.Toplevel(parent)  
        self.entryBoxNeeded = entryBoxNeeded
        #Add the icon
        try:
            icon = ImageTk.PhotoImage(Image.open(resourcePath("icon.png")))
            icon.image = resourcePath("icon.png")
            self.top.iconphoto(False, icon)
        except:
            pass
        self.l=tk.Label(top,text=text)
        self.l.bind('<Configure>', lambda e: self.l.config(wraplength=self.l.winfo_width()))
        self.l.pack(fill="both", expand =True)
        if self.entryBoxNeeded: #Only creates entry if requested
            self.e=tk.Entry(top)
            self.e.pack()
        self.b=tk.Button(top, text='Ok', command=self.cleanup, width = 30) #Button destroys window
        self.b.pack()

    #Destroys itself when button is pressed
    def cleanup(self):
        if self.entryBoxNeeded:
            self.value=self.e.get()
        self.top.destroy()


#Class for entering a new question (school council) - the startColumn and rows are passed in as well as question details and the parent window
class QuestionEntry():
    def __init__(self, parent, startColumn, addRows, position, options = [], questionType = -1, questionBody = "", targetYears = []):
        
        
        ###Set local variables and constants

        #Columns and rows for windows
        self.QUESTIONENTRYCOLUMN = 1
        self.QUESTIONLABELCOLUMN = 0 
        self.QUESTIONTYPECOLUMN = 2
        self.TARGETYEARSCOLUMN = 2
        self.ENTRYBOXENTRYCOLUMN = 1
        self.ENTRYBOXLABELSCOLUMN = 0
        self.ADDCOLUMN = 0
        self.REMOVECOLUMN = 3

        #Variables
        self.addRows = addRows
        self.startRow = (position * 100) + addRows
        self.position = position
        self.startColumn = startColumn
        self.parent = parent
        self.options = []
        self.options = options
        self.optionsBoxes = []
        self.optionsLabels = []

        ###Create boxes and menus
        count = 1

        #Option boxes
        for option in self.options:
            self.optionsBoxes.append(tk.Entry(self.parent, font = ('verdana', 12), relief = tk.RIDGE))
            self.optionsBoxes[len(self.optionsBoxes) -1 ].insert(0, option)
            self.optionsLabels.append(tk.Label(self.parent, text = "Option " + str(count) + ":", font = ('verdana', 12)))
            count += 1

        #Drop box
        self.dropBox =  ttk.Combobox(
                parent, 
                width = 27, 
                values= [
                '<Choose a question type>',
                'Multi-optioned',
                'Open Ended',
                'Yes/No',
                ],
                state = "readonly"
            ) 
        self.dropBox.bind("<<ComboboxSelected>>", lambda e: self.display())
        self.dropBox.current(int(questionType)+1)

        #Target year checkboxes
        self.checkBoxes = [[],[]]
        self.years = [7, 8, 9, 10, 11, 12, 13]
        for year in self.years:
            if year in targetYears:
                self.checkBoxes[1].append(tk.IntVar(value = 1))
            else:
                self.checkBoxes[1].append(tk.IntVar())
            self.checkBoxes[0].append(tk.Checkbutton(self.parent, text = int(year),  
                                variable = self.checkBoxes[1][len(self.checkBoxes[1]) - 1],     
                                onvalue = 1, 
                                offvalue = 0, 
                                height = 2, 
                                width = 10))
        self.targetYearsLabel = ttk.Label(self.parent, text='Select years to set to', font = ('verdana', 12))

        #Questions
        self.questionTitleLabel = ttk.Label(self.parent, text='Question ' + str(self.position) + ":", font = ('verdana', 18))
        self.questionTitleEntry = tk.Entry(self.parent, font = ('verdana', 12), relief = tk.RIDGE)
        self.questionTitleEntry.insert(0, questionBody)
        self.add = tk.Button(
            parent,
            bd = 0,
            activeforeground = '#4d84af',
            bg = '#2f2f31',
            fg = 'white',
            activebackground = '#2f2f31',
            text = 'Add Question',
            font = ('verdana', 12),
        )
        self.remove = tk.Button(
            parent,
            bd = 0,
            activeforeground = '#4d84af',
            bg = '#2f2f31',
            fg = 'white',
            activebackground = '#2f2f31',
            text = 'Remove Question',
            font = ('verdana', 12),
        )


    #Destroys the question structure and returns the startRow of the object
    def destroy(self):
        for ob in self.optionsBoxes:
            try:
                ob.destroy()
            except:
                pass       
        for ol in self.optionsLabels:
            try:
                ol.destroy()
            except:
                pass
        for cb in self.checkBoxes[0]:
            try:
                cb.destroy()
            except:
                pass
        try:
            self.questionTitleLabel.destroy()
        except:
            pass
        try:
            self.questionTitleEntry.destroy()
        except:
            pass
        try:
            self.dropBox.destroy()
        except:
            pass   
        try:
            self.add.destroy()
        except:
            pass
        try:
            self.remove.destroy()
        except:
            pass
        try:
            self.addEntry.destroy()
        except:
            pass
        try:
            self.removeEntry.destroy()
        except:
            pass
        try:
            self.targetYearsLabel.destroy()
        except:
            pass
        return self.startRow

    #Moves the question up in the question order
    def moveUp(self):
        self.position = self.position - 1
        self.startRow = (self.position * 100) + self.addRows
        self.display()

    #Moves the question down in the question order
    def moveDown(self):
        self.position = self.position + 1
        self.startRow = (self.position * 100) + self.addRows
        self.display()

    #Displays the object by gridding all the Tk objects
    def display(self):
        #Remove all the Tk objects
        for ob in self.optionsBoxes:
            try:
                ob.grid_forget()
            except:
                pass
       
        for ol in self.optionsLabels:
            try:
                ol.grid_forget()
            except:
                pass
        for cb in self.checkBoxes[0]:
            try:
                cb.grid_forget()
            except:
                pass
        try:
            self.questionTitleLabel.grid_forget()
        except:
            pass
        try:
            self.questionTitleEntry.grid_forget()
        except:
            pass
        try:
            self.dropBox.grid_forget()
        except:
            pass
        try:
            self.add.grid_forget()
        except:
            pass
        try:
            self.remove.grid_forget()
        except:
            pass
        try:
            self.addEntry.destroy()
        except:
            pass
        try:
            self.removeEntry.destroy()
        except:
            pass
        try:
            self.targetYearsLabel.grid_forget()
        except:
            pass
        
        #Redraw all the windows
        questionType = self.dropBox.current() - 1
        if questionType == 2:
            self.displayTargetYears()
        elif questionType == QUESTIONTYPEOPTIONS:
            self.displayTargetYears()
            self.displayOptionsEntry()
        elif questionType == QUESTIONTYPEOPEN:
            self.displayTargetYears()
        self.questionTitleLabel.config(text='Question ' + str(self.position) + ":")
        self.questionTitleLabel.grid(row = self.startRow, column = self.QUESTIONLABELCOLUMN, padx = 20, pady = 20)
        self.questionTitleEntry.grid(row = self.startRow, column = self.QUESTIONENTRYCOLUMN, padx = 20, pady = 20)
        self.dropBox.grid(row = self.startRow, column = self.QUESTIONTYPECOLUMN, padx = 20, pady = 20)
        if len(self.optionsLabels) > len(self.years):
            self.add.grid(row = self.startRow + len(self.optionsLabels) + 1, column = self.ADDCOLUMN, padx = 20, pady = 20)
        else:
            self.add.grid(row = self.startRow + len(self.years) + 2, column = self.ADDCOLUMN, padx = 20, pady = 20)
        self.remove.grid(row = self.startRow, column = self.REMOVECOLUMN, padx = 20, pady = 20)
        

    #Displays target year checkboxes
    def displayTargetYears(self):
        row = self.startRow + 2
        self.targetYearsLabel.grid(row = self.startRow + 1, column = self.TARGETYEARSCOLUMN, padx = 20, pady = 20)
        for checkBox in self.checkBoxes[0]:
            checkBox.grid(row=row, column = self.TARGETYEARSCOLUMN)
            row += 1

    #Removes a single row for options entry
    def removeEntryRow(self):
        self.optionsBoxes[len(self.optionsBoxes)-1].destroy()
        self.optionsBoxes.pop(len(self.optionsBoxes)-1)
        self.optionsLabels[len(self.optionsLabels)-1].destroy()
        self.optionsLabels.pop(len(self.optionsLabels)-1)
        self.displayOptionsEntry()

    #Adds a single row for options entry
    def addEntryRow(self):
        labelNumber = len(self.optionsBoxes) + 1
        self.optionsBoxes.append(tk.Entry(self.parent, font = ('verdana', 12), relief = tk.RIDGE))
        self.optionsLabels.append(tk.Label(self.parent, text = "Option " + str(labelNumber) + ":", font = ('verdana', 12)))
        self.displayOptionsEntry()

    #Displays the options entry boxes
    def displayOptionsEntry(self):
        currentInternalRow = self.startRow + 1

        #Must destroy all current boxes first to avoid overlapping
        try:
            self.addEntry.destroy()
        except:
            pass
        try:
            self.removeEntry.destroy()
        except:
            pass
        for box in self.optionsBoxes:
            try:
                box.grid_forget()
            except:
                pass
        for label in self.optionsLabels:
            try:
                label.grid_forget()
            except:
                pass

        #Redraw all windows
        for i in range(len(self.optionsBoxes)):
            self.optionsBoxes[i].grid(row = currentInternalRow, column = self.ENTRYBOXENTRYCOLUMN, padx = 20, pady = 20)
            self.optionsLabels[i].grid(row = currentInternalRow, column = self.ENTRYBOXLABELSCOLUMN, padx = 20, pady = 20)
            currentInternalRow += 1
        self.addEntry = tk.Button(
            self.parent,
            bd = 0,
            activeforeground = '#4d84af',
            bg = '#2f2f31',
            fg = 'white',
            activebackground = '#2f2f31',
            text = 'Add Option',
            font = ('verdana', 12),
            command = lambda :self.addEntryRow()
        )
        self.removeEntry = tk.Button(
            self.parent,
            bd = 0,
            activeforeground = '#4d84af',
            bg = '#2f2f31',
            fg = 'white',
            activebackground = '#2f2f31',
            text = 'Remove Option',
            font = ('verdana', 12),
            command = lambda: self.removeEntryRow()
        )
        self.addEntry.grid(row = currentInternalRow, column = self.ENTRYBOXLABELSCOLUMN, padx = 20, pady = 20)
        if len(self.optionsBoxes) > 0:
            self.removeEntry.grid(row =currentInternalRow, column = self.ENTRYBOXENTRYCOLUMN, padx = 20, pady = 20)
        self.add.grid_forget()
        if len(self.optionsLabels) > len(self.years):
            self.add.grid(row = currentInternalRow + 1, column = self.ADDCOLUMN, padx = 20, pady = 20)
        else:
            self.add.grid(row = self.startRow + len(self.years) + 2, column = self.ADDCOLUMN, padx = 20, pady = 20)
           
    #Gets the data from each of the boxes, compiles it and outputs the 6 required pieces of information
    #If an error occurs, False and the error code are returned as well as 4 None variables which are not used
    def getData(self):
        questionType = self.dropBox.current() - 1
        options = []
        question = ""
        if questionType == -1:
            return False, "No question type selected", None, None, None, None
        if questionType == QUESTIONTYPEOPTIONS:
            for ob in self.optionsBoxes:
                option = ob.get()
                if option != "":
                    options.append(option)
            if len(options) < 1:
                return False, "Not enough options supplied", None, None, None, None
            question = self.questionTitleEntry.get()
            if question == "":
                return False, "Question title not input", None, None, None, None
            targetYears = []
            for i in range(len(self.checkBoxes[1])):
                if self.checkBoxes[1][i].get() == 1:
                    targetYears.append(i + 7)
                targetYears.sort()
            if len(targetYears) == 0:
                return False, "Target years not selected", None, None, None, None
            return True, "Success", question, questionType, targetYears, options

        if questionType == QUESTIONTYPEOPEN:
            options = None
            question = self.questionTitleEntry.get()
            if question == "":
                return False, "Title not input", None, None, None, None
        targetYears = []
        for i in range(len(self.checkBoxes[1])):
            if self.checkBoxes[1][i].get() == 1:
                targetYears.append(i + 7)
            targetYears.sort()
        if len(targetYears) == 0:
            return False, "Target years not selected", None, None, None, None

        if questionType == 2:
            options = ["Yes", "No"]
            questionType = QUESTIONTYPEOPTIONS
            question = self.questionTitleEntry.get()
            if question == "":
                return False, "Title not input", None, None, None, None
        targetYears = []
        for i in range(len(self.checkBoxes[1])):
            if self.checkBoxes[1][i].get() == 1:
                targetYears.append(i + 7)
            targetYears.sort()
        if len(targetYears) == 0:
            return False, "Target years not selected", None, None, None, None

        return True, "Success", question, questionType, targetYears, options




#######################################################################################################
################################################ UI ###################################################
#######################################################################################################        


#Starts the User interface
def start():
    """The main UI function"""
    startUI = tk.Tk()
    startUI.state('zoomed')
    startUI.configure(bg='#6f6f6f')
    startUI.title('Eve')
    try:
        icon = ImageTk.PhotoImage(Image.open(resourcePath("icon.png")))
        icon.image = resourcePath("icon.png")
        startUI.iconphoto(False, icon)
    except:
        pass
    startUI.minsize(900, 450)

    #Displays the program information (F1)
    def progInfo():
        """Program Info"""
        text = ("E-voice (Eve) Survey Viewer Version 1.3\n "
                "© Copyright 2020\n"
                "Jacqueline Dobreva, Isaac Skevington\n"
                "All Rights Reserved\n"
                "You are not licensed to copy, change, or distribute this software without permission, for profit or otherwise\n"
                "Doing so could leave you open to suit\n"
                "Report any issues to y14jadob@latymer.co.uk or y14isske@latymer.co.uk\n"
                "This program contains: 4050 line of code, Stable Build 23:36, 16/11/2020\n\n"
                "Changes from 1.2:\n"
                "Offline mode added, bugs fixed")
        PopupWindow(startUI, text, entryBoxNeeded=False)

    #A little easter egg :)
    def easterEggI():
        """Isaac's Easter egg :)"""
        text = "Hot cross bun time ~ I\n"
        PopupWindow(startUI, text, entryBoxNeeded=False)

    #Binding Keys to above functions    
    startUI.bind('<F1>', lambda e : progInfo())
    startUI.bind('<F8>', lambda e : easterEggI())

    global save

    #Opens an offline survey file
    def openFile():
        filename = tk.filedialog.askopenfilename(title = "Open survey", defaultextension = ".evs", filetypes = [("Survey Files", ".evs")])
        return filename        
        
    #Returns a user selected filename (default is xlsx extension, but also used for the Survey files)
    def saveFile(filename, defaultextension = ".xlsx", filetypes = [("Excel Spreadsheet",".xlsx")]): 
        startUI.filename =  tk.filedialog.asksaveasfilename(initialdir = "/",
                                                        title = "Save As",
                                                        filetypes = filetypes,
                                                        defaultextension= defaultextension,
                                                        initialfile = filename)
        return startUI.filename
    save = saveFile    


    def incorrect():
        """Incorrect login alert"""
        global backgroundLabel

        incorrectLabel = tk.Label(
            startUI,
            fg = 'red',
            bg = '#ffffff',
            text = 'Incorrect username / password',
            wraplength = 100,
            justify="center"
        )
        incorrectLabel.bind('<Configure>', lambda e: incorrectLabel.config(wraplength=incorrectLabel.winfo_width()))
        incorrectLabel.place(relx = 0.6, rely = 0.590, relwidth = 0.1)
        startUI.mainloop()



    def levelOfAccess():
        """Returns access level, asks for class numbers, or calls incorrect function"""
        global userName
        global passWord
        global classID
        global usernameEntry
        global passwordEntry
        global accessLevel
        global offlineSurvey
        global offline
        global offlinePeople
        global offlineclass
        usernameEntry = userName.get()
        passwordEntry = passWord.get()
        if offline: #If the user is offline
            surveyFile = openFile()
            offlinePeople = enterClassPeoplePopUp()
            with open (surveyFile, 'rb') as file:
                offlineSurvey = pickle.load(file)
            offlineSurvey.people = offlinePeople
            offlineclass = usernameEntry
            form(None)

        else: #Otherwise try to log the user in
            loginSuccess, userType, userData = sqlLogin(usernameEntry, passwordEntry)

            #Handle the login
            if loginSuccess:
                if userType == ID_SURVEYOR:
                    accessLevel = userData
                    schoolCouncil(accessLevel)
                else:
                    if userType == ID_CLASS_NEW:
                        people = enterClassPeoplePopUp()
                        changeClassPeople(userData, people, ACCESSLEVELP)

                    classID = userData
                    form(classID)
            else:
                incorrect()

    def enterClassPeoplePopUp():
        """Prompts new class to enter total number of students"""
        global popupWin
        global loginButton
        popupWin=PopupWindow(startUI, "You haven't logged in before, please\n enter the number of people in your class")
        loginButton["state"] = "disabled" 
        startUI.wait_window(popupWin.top)
        loginButton["state"] = "normal"
        return popupWin.value

    def schoolCouncil(access):
        """Main school council function, 1 of 2 possible pages post login"""
        global backgroundLabel
        global loginFrame
        global surveyArea
        global createNewAccountsArea
        global statisticsArea
        global schoolCouncilFrame
        global createButton
        
        #Destroys superfluous frames
        try:
            schoolCouncilFrame.destroy()
        except:
            pass
        try:
            backgroundLabel.destroy()
        except:
            pass
        try:
            loginFrame.destroy()
        except:
            pass

        schoolCouncilFrame = tk.Frame(startUI, bd = 0)
        schoolCouncilFrame.pack(expand = tk.YES, fill = tk.BOTH, anchor = 'nw', side = "top")
        sidebar = tk.Frame(schoolCouncilFrame, width = 220, bg = '#2f2f31')
        sidebar.pack(expand = 0, fill = tk.BOTH, side = 'left', anchor = 'nw')
      

        def changeToNewPass():
            """Enforces changes of user pass to new pass (UI)"""
            global newPass
            global newPassEntry
            global usernameEntry
            global passwordEntry
            newPass = newPassEntry.get()
            changePassword(usernameEntry, passwordEntry, newPass)
            schoolCouncil(accessLevel)

        def changePass():
            """Follows 'change password' button click"""
            global surveyArea
            global statisticsArea
            global createNewAccountsArea
            global classID
            global passArea
            global newPassEntry
            global createNewSurveyArea
        
            #Destroys superfluous frames
            try:
                createNewSurveyArea.destroy()
            except:
                pass
            try:
                surveyArea.destroy()
            except:
                pass
            try:
                statisticsArea.destroy()
            except:
                pass
            try:
                createNewAccountsArea.destroy()
            except:
                pass
            try:
                questionFrame.destroy()
            except:
                pass
            try:
                passArea.destroy()
            except:
                pass
            try:
                createButton.destroy()
            except:
                pass
            try:
                incorrectSurveyLabel.destroy()
            except:
                pass
            

            passArea = ScrollableFrame(schoolCouncilFrame, width = 800)
            parent = passArea.scrollableFrame
            parent.grid_rowconfigure(0, weight=1)
            parent.grid_columnconfigure(0, minsize=80)
            parent.grid_columnconfigure(1, minsize=80)
            parent.grid_rowconfigure(2, minsize=80)
            parent.grid_rowconfigure(1, minsize=80)

            #Attached to entry widgets- allows 'fade in, fade out' effect of text
            def on_entry_click(event):
                if newPassEntry.cget('fg') == 'grey':
                    newPassEntry.delete(0, "end") 
                    newPassEntry.insert(0, '') 
                    newPassEntry.config(fg = 'black', show = '•')
                
            def on_focusout(event):
                if newPassEntry.get() == '':
                    newPassEntry.insert(0, 'New Password')
                    newPassEntry.config(fg = 'grey', show = '')

            #user entry space for new password
            newPassEntry = tk.Entry(parent, font = ('verdana', 12), relief = tk.RIDGE,)
            newPassEntry.insert(0, 'New Password')
            newPassEntry.bind('<FocusIn>', on_entry_click)
            newPassEntry.bind('<FocusOut>', on_focusout)
            newPassEntry.config(fg = 'grey')
            newPassEntry.grid(column = 0, row = 1, sticky = 'NSEW', padx = (30, 30), pady = (50, 50))


            changeButton = tk.Button(
                parent,
                bd = 0,
                activeforeground = '#4d84af',
                bg = '#2f2f31',
                fg = 'white',
                activebackground = '#2f2f31',
                text = 'Change',
                anchor = tk.W,
                font = ('verdana', 12),
                width = '15',
                padx = 10,
                pady = 10,
                command = changeToNewPass
            )

            changeButton.grid(column = 1, row = 1, sticky = 'nsew', padx = (30, 30), pady = (50, 50))
            warningLabel = tk.Label(parent, font = ('verdana', 18, "underline", "bold"), text = "Use a different password to other sites!")
            warningLabel.grid(column = 0, row = 0, padx = 30, pady = 10, columnspan = 3)

            #Changes buttons to make sure active/inactive appearance is maintained, even after immediate click
            statisticsButton.config(fg = 'white', bg = '#2f2f31', text = '« Survey Statistics')
            surveysButton.config(fg = 'white', bg = '#2f2f31', text = '« Existing Surveys')
            createNewAccountsButton.config(fg = 'white', bg = '#2f2f31', text = '« Create/Delete\nAccounts') 
            createNewSurveyButton.config(fg = 'white', bg = '#2f2f31', text = '« Create New \nSurvey')

            passArea.pack(expand = True, fill = "both") 

            startUI.mainloop()

        def createNAButtonFunc():
            """Function called by clicking button to create a new account"""
            global newUserSurnameEntryBox 
            global newUserFirstnameEntryBox
            global newUserUsernameEntry 
            global newUserPasswordEntry
            global setAccessLevelEntry
            global newUserSurnameEntry 
            global newUserFirstnameEntry 
            global newUserUsernameEntryBox
            global newUserPasswordEntryBox
            global newAccessLevel 
            global accessLevel
            global createNewAccountsArea

            #Creating an account Entry boxes
            newUserSurnameEntry = newUserSurnameEntryBox.get()
            newUserFirstnameEntry = newUserFirstnameEntryBox.get()
            newUserUsernameEntry = newUserUsernameEntryBox.get()
            newUserPasswordEntry = newUserPasswordEntryBox.get()

            if newUserUsernameEntry == "Username" or newUserPasswordEntry == "Password" or newUserFirstnameEntry == "First name" or newUserSurnameEntryBox == "Surname":
                newAccessLevel = 100
                
            if newUserUsernameEntry == "" or newUserPasswordEntry == "" or newUserFirstnameEntry == "" or newUserSurnameEntryBox == "":
                newAccessLevel = 100
            newAccessLevel = setAccessLevelEntry.current() - 1
            if newAccessLevel < 0:
                    newAccessLevel = 100
            if not createSurveyor(newUserUsernameEntry, newUserPasswordEntry, newAccessLevel, accessLevel, firstname = newUserFirstnameEntry, surname = newUserSurnameEntry):
                noCanDo = tk.Label(
                    createNewAccountsArea.scrollableFrame,
                    fg = 'red',
                    bg = 'white',
                    font = ('verdana', 12),
                    text = 'Incorrect Details'
                )
                noCanDo.grid(column = 1, row = 1, sticky = 'NSEW', columnspan = 4)
            else:
                schoolCouncil(accessLevel)


        def deleteThisUser():
            """Deletes existing user (UI side)"""

            global toDeleteUsernameEntry
            global toDeleteUsername

            toDeleteUsername = toDeleteUsernameEntry.get()
            if deleteSurveyorAccount(toDeleteUsername, access):
                schoolCouncil(access)
            
        def createNewAccounts():
            """UI for creating new accounts of deleting exsisting ones"""
            global surveyArea
            global statisticsArea
            global createNewAccountsArea
            global createButton
            global classID
            global passArea
            global newUserSurnameEntryBox 
            global newUserFirstnameEntryBox
            global newUserUsernameEntryBox 
            global newUserPasswordEntryBox 
            global setAccessLevelEntry
            global toDeleteUsernameEntry
            global createNewSurveyArea

            #Destroys superfluous frames
            try:
                createNewSurveyArea.destroy()
            except:
                pass
            try:
                surveyArea.destroy()
            except:
                pass
            try:
                statisticsArea.destroy()
            except:
                pass
            try:
                createNewAccountsArea.destroy()
            except:
                pass
            try:
                questionFrame.destroy()
            except:
                pass
            try:
                passArea.destroy()
            except:
                pass
            try:
                createButton.destroy()
            except:
                pass
            try:
                incorrectSurveyLabel.destroy()
            except:
                pass
            

            #setting up area
            createNewAccountsArea = ScrollableFrame(schoolCouncilFrame, width = 800)
            parent = createNewAccountsArea.scrollableFrame
            parent.grid_columnconfigure(0, minsize=30)
            parent.grid_columnconfigure(1, minsize=30)
            parent.grid_columnconfigure(2, minsize=30)
            parent.grid_columnconfigure(3, minsize=30)
            parent.grid_columnconfigure(3, minsize=30)
            parent.grid_rowconfigure(0, minsize=10)

            #All things to do with the 'delete user' entry box and button
            def on_entry_click5(event):
                if toDeleteUsernameEntry.cget('fg') == 'grey':
                    toDeleteUsernameEntry.delete(0, "end") 
                    toDeleteUsernameEntry.insert(0, '') 
                    toDeleteUsernameEntry.config(fg = 'black')
                
            def on_focusout5(event):
                if toDeleteUsernameEntry.get() == '':
                    toDeleteUsernameEntry.insert(0, 'Old User Username')
                    toDeleteUsernameEntry.config(fg = 'grey', show = '')

            toDeleteUsernameEntry = tk.Entry(parent, font = ('verdana', 12), relief = tk.RIDGE,)
            toDeleteUsernameEntry.insert(0, 'Old User Username')
            toDeleteUsernameEntry.bind('<FocusIn>', on_entry_click5)
            toDeleteUsernameEntry.bind('<FocusOut>', on_focusout5)
            toDeleteUsernameEntry.config(fg = 'grey')
            toDeleteUsernameEntry.grid(column = 0, row = 7, sticky = 'NSEW', padx = (30, 30), pady = (5, 5))

            deleteUserButton = tk.Button(
                parent,
                bd = 0,
                activeforeground = '#4d84af',
                bg = '#2f2f31',
                fg = 'white',
                activebackground = '#2f2f31',
                text = 'Delete User',
                anchor = tk.W,
                font = ('verdana', 12),
                width = '15',
                padx = 10,
                command = deleteThisUser
            )

            deleteUserButton.grid(column = 1, row = 7, sticky = 'nsew', padx = (30, 30))

            #All things to do with gathering the first name and last name of the person an account is about to be created for
            def on_entry_click3(event):
                if newUserSurnameEntryBox.cget('fg') == 'grey':
                    newUserSurnameEntryBox.delete(0, "end") 
                    newUserSurnameEntryBox.insert(0, '') 
                    newUserSurnameEntryBox.config(fg = 'black')
                
            def on_focusout3(event):
                if newUserSurnameEntryBox.get() == '':
                    newUserSurnameEntryBox.insert(0, 'Surname')
                    newUserSurnameEntryBox.config(fg = 'grey', show = '')
      
            def on_entry_click2(event):
                if newUserFirstnameEntryBox.cget('fg') == 'grey':
                    newUserFirstnameEntryBox.delete(0, "end") 
                    newUserFirstnameEntryBox.insert(0, '') 
                    newUserFirstnameEntryBox.config(fg = 'black')
                
            def on_focusout2(event):
                if newUserFirstnameEntryBox.get() == '':
                    newUserFirstnameEntryBox.insert(0, 'First name')
                    newUserFirstnameEntryBox.config(fg = 'grey', show = '')

            newUserFirstnameEntryBox = tk.Entry(parent, font = ('verdana', 12), relief = tk.RIDGE,)
            newUserFirstnameEntryBox.insert(0, 'First name')
            newUserFirstnameEntryBox.bind('<FocusIn>', on_entry_click2)
            newUserFirstnameEntryBox.bind('<FocusOut>', on_focusout2)
            newUserFirstnameEntryBox.config(fg = 'grey')
            newUserFirstnameEntryBox.grid(column = 0, row = 0, sticky = 'NSEW', padx = (30, 30), pady = (5, 5))

            newUserSurnameEntryBox = tk.Entry(parent, font = ('verdana', 12), relief = tk.RIDGE,)
            newUserSurnameEntryBox.insert(0, 'Surname')
            newUserSurnameEntryBox.bind('<FocusIn>', on_entry_click3)
            newUserSurnameEntryBox.bind('<FocusOut>', on_focusout3)
            newUserSurnameEntryBox.config(fg = 'grey')
            newUserSurnameEntryBox.grid(column = 0, row = 1, sticky = 'NSEW', padx = (30, 30), pady = (5, 5))

            #Takes in information about the to-be-created users username and password
            def on_entry_click1(event):
                if newUserUsernameEntryBox.cget('fg') == 'grey':
                    newUserUsernameEntryBox.delete(0, "end") 
                    newUserUsernameEntryBox.insert(0, '') 
                    newUserUsernameEntryBox.config(fg = 'black')
                
            def on_focusout1(event):
                if newUserUsernameEntryBox.get() == '':
                    newUserUsernameEntryBox.insert(0, 'Username')
                    newUserUsernameEntryBox.config(fg = 'grey', show = '')

            newUserUsernameEntryBox = tk.Entry(parent, font = ('verdana', 12), relief = tk.RIDGE,)
            newUserUsernameEntryBox.insert(0, 'Username')
            newUserUsernameEntryBox.bind('<FocusIn>', on_entry_click1)
            newUserUsernameEntryBox.bind('<FocusOut>', on_focusout1)
            newUserUsernameEntryBox.config(fg = 'grey')
            newUserUsernameEntryBox.grid(column = 0, row = 2, sticky = 'NSEW', padx = (30, 30), pady = (5, 5))

            def on_entry_click(event):
                if newUserPasswordEntryBox.cget('fg') == 'grey':
                    newUserPasswordEntryBox.delete(0, "end") 
                    newUserPasswordEntryBox.insert(0, '') 
                    newUserPasswordEntryBox.config(fg = 'black')
                
            def on_focusout(event):
                if newUserPasswordEntryBox.get() == '':
                    newUserPasswordEntryBox.insert(0, 'Password')
                    newUserPasswordEntryBox.config(fg = 'grey', show = '')

            newUserPasswordEntryBox = tk.Entry(parent, font = ('verdana', 12), relief = tk.RIDGE,)
            newUserPasswordEntryBox.insert(0, 'Password')
            newUserPasswordEntryBox.bind('<FocusIn>', on_entry_click)
            newUserPasswordEntryBox.bind('<FocusOut>', on_focusout)
            newUserPasswordEntryBox.config(fg = 'grey')
            newUserPasswordEntryBox.grid(column = 0, row = 3, sticky = 'NSEW', padx = (30, 30), pady = (5, 5))
            accessLevelPossibles = ["<Select an access level>"] + getPossibleAccessLevelNames(accessLevel)
            setAccessLevelEntry = ttk.Combobox(parent, values=accessLevelPossibles, state = "readonly")
            setAccessLevelEntry.current(0)
            setAccessLevelEntry.grid(column = 0, row = 4, sticky = 'NSEW', padx = (30, 30), pady = (5, 5))

            createButton = tk.Button(
                parent,
                bd = 0,
                activeforeground = '#4d84af',
                bg = '#2f2f31',
                fg = 'white',
                activebackground = '#2f2f31',
                text = 'Create Account',
                anchor = tk.W,
                font = ('verdana', 12),
                width = '15',
                padx = 10,
                command = createNAButtonFunc
            )
            
            #Searches for users with the given username
            def searchUsers(body, outerparent):
                global userdatalabels
                global accessLevel
                if body == "Search for users":
                    body = ""
                for userdatalabel in userdatalabels:
                    try:
                        userdatalabel.destroy()
                    except:
                        pass
                innerparent = tk.Frame(parent)
                innerparent.grid(row = 10, column = 0, columnspan = 5, sticky = "NW", padx = 30, pady = 30)
                userdatalabels = []
                sql = "SELECT username, accessLevel, firstname, surname FROM CouncilMember WHERE accessLevel <= " + str(accessLevel) + " and username like + '%" + body + "%' ORDER BY accessLevel desc"
                csr.execute(sql)
                userdata = csr.fetchall()
                currentLabel = tk.Label(innerparent, font = ('verdana', 14, "underline", "bold"), text = "Username", justify = 'left')
                userdatalabels.append(currentLabel)
                currentLabel.grid(column = 0, row = 0)
                currentLabel = tk.Label(innerparent, font = ('verdana', 14, "underline", "bold"), text = "Name", justify = 'left')
                userdatalabels.append(currentLabel)
                currentLabel.grid(column = 1, row = 0)
                currentLabel = tk.Label(innerparent, font = ('verdana', 14, "underline", "bold"), text = "Access Level", justify = 'left')
                userdatalabels.append(currentLabel)
                currentLabel.grid(column = 2, row = 0)
                counter = 1
                for data in userdata:
                    currentLabel = tk.Label(innerparent, font = ('verdana', 12), text = str(data[0]), justify = 'left')
                    userdatalabels.append(currentLabel)
                    currentLabel.grid(column = 0, row = counter, padx = 10, pady = 10)
                    currentLabel = tk.Label(innerparent, font = ('verdana', 12), text = str(data[2]) + " " + str(data[3]), justify = 'left')
                    userdatalabels.append(currentLabel)
                    currentLabel.grid(column = 1, row = counter, padx = 10, pady = 10)
                    accessLevelString = getAccessLevelName(data[1])
                    accessLevelString = accessLevelString[0].upper() + accessLevelString[1:]
                    currentLabel = tk.Label(innerparent, font = ('verdana', 12), text = accessLevelString, justify = 'left')
                    userdatalabels.append(currentLabel)
                    currentLabel.grid(column = 2, row = counter, padx = 10, pady = 10)
                    counter += 1



            def on_entry_clickSearch(event):
                if searchUserEntry.cget('fg') == 'grey':
                    searchUserEntry.delete(0, "end") 
                    searchUserEntry.insert(0, '') 
                    searchUserEntry.config(fg = 'black')
                
            def on_focusoutSearch(event):
                if searchUserEntry.get() == '':
                    searchUserEntry.insert(0, 'Search for users')
                    searchUserEntry.config(fg = 'grey', show = '')

            searchUserEntry = tk.Entry(parent, font = ('verdana', 12), relief = tk.RIDGE,)
            searchUserEntry.insert(0, 'Search for users')
            searchUserEntry.bind('<FocusIn>', on_entry_clickSearch)
            searchUserEntry.bind('<FocusOut>', on_focusoutSearch)
            searchUserEntry.config(fg = 'grey')

            listUsersButton = tk.Button(
                parent,
                bd = 0,
                activeforeground = '#4d84af',
                bg = '#2f2f31',
                fg = 'white',
                activebackground = '#2f2f31',
                text = 'Search',
                anchor = tk.W,
                font = ('verdana', 12),
                width = '15',
                padx = 10,
                command = lambda p = parent: searchUsers(searchUserEntry.get(), p)
            )
            searchUserEntry.grid(column = 0, row = 8, padx = 30, pady = 10, sticky = "w")
            listUsersButton.grid(column = 0, row = 9, sticky = 'w', padx = 30, pady = 10)
            createButton.grid(column = 1, row = 4, sticky = 'nsew', padx = (30, 30))

            #Label explaining the access level scheme
            accessLevelExplainLabel = tk.Label(
                parent, 
                bd = 0,
                font = ('verdana', 10),
                text = '''Access levels:\n
                        \nView: Read permissions - view surveys and download
                        \nEdit: Write permissions - add new and alter old surveys/questions
                        \nAdministrator: Add and remove councillor users, classes
                        \nSystem: Add and remove administrators
                        \nYou can only create users with a lower access level than yours
                        \nYou can find your access level on the bottom left ''',
                justify = 'left'
            )

            accessLevelExplainLabel.grid(column = 0, row = 5, sticky = 'nsew', padx = (30, 30), pady = (5, 5))

            #changes buttons to make sure active/inactive appearance is maintained, even after immediate click
            statisticsButton.config(fg = 'white', bg = '#2f2f31', text = '« Survey Statistics')
            surveysButton.config(fg = 'white', bg = '#2f2f31', text = '« Existing Surveys')
            createNewAccountsButton.config(fg = '#4d84af', bg = '#2f2f31', text = '» Create/Delete\nAccounts') 
            createNewSurveyButton.config(fg = 'white', bg = '#2f2f31', text = '« Create New \nSurvey')
            
            createNewAccountsArea.pack(expand = True, fill = "both")

            startUI.mainloop()

            #small entry widget beneath with 'type question here' as default
            #add/remove buttons (view isaacs code)

        #Remove a question object from the question stack
        def removeQuestion(index):
            global questionEntries
            position = questionEntries[index].position
            questionEntries[index].destroy()
            questionEntries.pop(index)
            for questionEntry in questionEntries:
                if questionEntry.position > position:
                    questionEntry.moveUp()
                    questionEntry.display()

        #Add a question object to the question stack
        def addQuestion(position, options = [], questionType = -1, questionBody = "", targetYears = [], parent = "default"):
            global createNewSurveyArea
            global questionEntries
            if parent == "default":
                parent = createNewSurveyArea.scrollableFrame
            newEntry = QuestionEntry(parent, 1, 4, position, options = options, questionType = questionType, questionBody = questionBody, targetYears = targetYears)
            newEntry.add.configure(command=lambda: addQuestion(newEntry.position + 1))
            newEntry.remove.configure(command=lambda : removeQuestion(newEntry.position - 1))
            for questionEntry in questionEntries:
                if questionEntry.position >= position:
                    questionEntry.moveDown()
                    questionEntry.display()
            questionEntries.append(newEntry)
            newEntry.display()
            

        #Sets a survey to a number of years
        def setSurvey(surveyName, questions, dueDate, parent, surveyID = None, afterDelete = False):
            global accessLevel
            global incorrectSurveyLabel
            global questionEntries
            processingLabel = tk.Label(
            startUI,
            fg = 'red',
            bg = '#ffffff',
            text = 'Processing...\n(This could take some time)',
            justify="center",
            font = ("verdana", 50, "underline", "bold")
            )
            processingLabel.place(relx = 0, rely = 0, relwidth = 1, relheight = 1)
            startUI.update()
            success = True
            questionData = []
            allTargetYears = []
            for question in questions:
                qSuccess, errorCode, questionBody, questionType, targetYears, options = question.getData()
                if not qSuccess:
                    success = False
                    break
                questionData.append([questionBody, questionType, targetYears, options])
                for targetYear in targetYears:
                    if targetYear not in allTargetYears:
                        allTargetYears.append(targetYear)
            if success:
                SID = newSurvey(surveyName, allTargetYears, dueDate.strftime('%Y-%m-%d'), myAccessLevel = accessLevel)
                if SID == "False":
                    success = False
                else:
                    for question in questionData:
                        if newQuestion(question[1], question[0], SID, question[2], myAccessLevel = accessLevel, options = question[3]) == "False":
                            success = False
                            break
            if success:
                questionEntries = []
                if afterDelete:
                    deleteSurvey(surveyID)
                try:
                    processingLabel.destroy()
                except:
                    pass
                schoolCouncil(accessLevel)
            else:                   
                try:
                    incorrectSurveyLabel.destroy()
                except:
                    pass
                if errorCode == "Success":
                    deleteSurvey(SID)
                    incorrectSurveyLabel = tk.Label(parent, fg = 'red', text="Submission failed, please try again in a minute", font = ("verdana", 15))
                    incorrectSurveyLabel.pack(side = "top", anchor = "sw")
                else:
                    incorrectSurveyLabel = tk.Label(parent, fg = 'red', text="Error: " + errorCode, font = ("verdana", 15))
                    incorrectSurveyLabel.pack(side = "top", anchor = "sw")
            try:
                processingLabel.destroy()
            except:
                pass
            

        def createNewSurvey():
            """Allows school councillor to create new surveys (UI)"""
            global surveyArea
            global statisticsArea
            global createNewAccountsArea
            global classID
            global passArea
            global createNewSurveyArea
            global questionEntries
            global firstAddButton
            global createButton
            questionEntries = []
            #Destroys superfluous frames
            try:
                createNewSurveyArea.destroy()
            except:
                pass
            try:
                surveyArea.destroy()
            except:
                pass
            try:
                statisticsArea.destroy()
            except:
                pass
            try:
                createNewAccountsArea.destroy()
            except:
                pass
            try:
                questionFrame.destroy()
            except:
                pass
            try:
                passArea.destroy()
            except:
                pass
            try:
                createButton.destroy()
            except:
                pass
            try:
                incorrectSurveyLabel.destroy()
            except:
                pass
            
            #Set up work area
            createNewSurveyArea = ScrollableFrame(schoolCouncilFrame, width = 800)
            parent = createNewSurveyArea.scrollableFrame
            parent.grid_columnconfigure(0, minsize=200)
            parent.grid_columnconfigure(1, minsize=200)
            parent.grid_columnconfigure(2, minsize=200)
            parent.grid_columnconfigure(3, minsize=200)
            parent.grid_columnconfigure(4, minsize=200)
            parent.grid_columnconfigure(5, minsize=200)
            parent.grid_rowconfigure(0, minsize=50)
            parent.grid_rowconfigure(1, minsize=50)
            surveyTitleLabel = ttk.Label(parent, text='Survey Title:', font = ("verdana", 18, "bold", "underline"))
            surveyTitleEntry = tk.Entry(parent, font = ('verdana', 15, "bold"), relief = tk.RIDGE)
            dueDateLabel = ttk.Label(parent, text='Pick due date:', font = ("verdana", 18, "bold", "underline"))
            calendar =  Calendar(parent)
            firstAddButton = tk.Button(
                        parent,
                        bd = 0,
                        activeforeground = '#4d84af',
                        bg = '#2f2f31',
                        fg = 'white',
                        activebackground = '#2f2f31',
                        text = 'Add Question',
                        font = ('verdana', 12),
                        command = lambda : addQuestion(1)
                        )
            createButton = tk.Button(
                        schoolCouncilFrame,
                        bd = 0,
                        activeforeground = '#4d84af',
                        bg = '#2f2f31',
                        fg = 'white',
                        activebackground = '#2f2f31',
                        text = 'Create',
                        font = ('verdana', 14, "bold", "underline"),
                        command = lambda : setSurvey(surveyTitleEntry.get(), questionEntries, calendar.selection_get(), schoolCouncilFrame)
                        )
            firstAddButton.grid(row = 2, column = 0)
            surveyTitleLabel.grid(row = 0, column = 0, padx = 10)
            surveyTitleEntry.grid(row = 0, column = 1, padx = 10)
            statisticsButton.config(fg = 'white', bg = '#2f2f31', text = '« Survey Statistics')
            surveysButton.config(fg = 'white', bg = '#2f2f31', text = '« Existing Surveys')
            createButton.pack(side = "bottom", anchor = "se", padx = 10, pady = 30)
            dueDateLabel.grid(row = 0, column = 2, padx = 10)
            calendar.grid(row = 0, column = 3, padx = 10)
            createNewAccountsButton.config(fg = 'white', bg = '#2f2f31', text = '« Create/Delete\nAccounts') 
            createNewSurveyButton.config(fg = '#4d84af', bg = '#2f2f31', text = '» Create New \nSurvey')

            createNewSurveyArea.pack(expand = True, fill = "both")

            startUI.mainloop()

        def statistics():
            """Allows School Councillor to view some general statistics on the surveys (UI)"""
            allSurveys = loadAllSurveys()
            global surveyArea
            global statisticsArea
            global createNewAccountsArea
            global classID
            global passArea
            global createNewSurveyArea

            #Destroys superfluous frames
            try:
                createNewSurveyArea.destroy()
            except:
                pass
            try:
                surveyArea.destroy()
            except:
                pass
            try:
                statisticsArea.destroy()
            except:
                pass
            try:
                createNewAccountsArea.destroy()
            except:
                pass
            try:
                questionFrame.destroy()
            except:
                pass
            try:
                passArea.destroy()
            except:
                pass
            try:
                createButton.destroy()
            except:
                pass
            try:
                incorrectSurveyLabel.destroy()
            except:
                pass
            
            
            #Create a scrollable frame, and setting up the rest of the workspace
            statisticsArea = ScrollableFrame(schoolCouncilFrame, width = 800)
            statisticslabels = {}
            parent = statisticsArea.scrollableFrame
            parent.grid_rowconfigure(0, weight=1)
            parent.grid_columnconfigure(1, minsize = 80)
            surveyText = tk.Label(parent, text = 'Surveys', padx = 20, pady = 20 , bg = '#ebf1f6', font = ('verdana', 12), fg = '#4d84af')
            surveyText.grid(column=0,row=0, sticky = "NSEW")
            notDoneText = tk.Label(parent, text = 'Classes not done', bg = '#ebf1f6', padx = 20, pady = 20, font = ('verdana', 12), fg = '#4d84af')
            notDoneText.grid(column=1,row=0, sticky = "NSEW")
            percentageText = tk.Label(parent, text = 'Percent completed', bg = '#ebf1f6', padx = 20, pady = 20, font = ('verdana', 12), fg = '#4d84af')
            percentageText.grid(column=2,row=0, sticky = "NSEW")
            strOfClasses = ''
                
            #Creates a light blue topbar with the necessary headings    
            for i in range(1, len(allSurveys)+1):
                allS = allSurveys[i-1]
                complete, completeS = isComplete(allS)
                classes = [getClassName(classID) for classID in completeS]
                strOfClasses = ", ".join(classes)
                label = {}   
                label["name"] = tk.Label(parent, text = getSurveyName(allS), padx = 20, pady = 20)
                label["name"].grid(column=0,row =i, sticky = "NSEW")
                label["notDone"]= tk.Label(parent, text = strOfClasses, anchor = tk.W, justify = 'left', width = 50)
                label["notDone"].bind('<Configure>', lambda e, l=label["notDone"]: l.config(wraplength=l.winfo_width()))
                label["notDone"].grid(column=1,row=i)
                label["percentage"] = tk.Label(parent, text = str(int(percentageSurveyComplete(allS))), padx = 20, pady = 20)
                label["percentage"].grid(column=2, row=i, sticky = "NSEW")
                
                statisticslabels[(allS)] = label

            #Pack the frame
            statisticsArea.pack(side="top", fill="both", expand=True)

            #changes buttons to make sure active/inactive appearance is maintained, even after immediate click
            statisticsButton.config(fg = '#4d84af', bg = '#2f2f31', text = '» Survey Statistics')
            surveysButton.config(fg = 'white', bg = '#2f2f31', text = '« Existing Surveys')
            createNewAccountsButton.config(fg = 'white', bg = '#2f2f31', text = '« Create/Delete\nAccounts') 
            createNewSurveyButton.config(fg = 'white', bg = '#2f2f31', text = '« Create New \nSurvey')
            
            startUI.mainloop() 
        
        #Save as excel document
        def doTheSaving(surveyID):
            """Calls 'saveAsExcel' function (UI)"""
            saveAsExcel(surveyID)


        #Displaying the surveys and their information to councillors
        def surveysButtonCommand():
            allSurveys = loadAllSurveys()
            global surveyArea
            global statisticsArea
            global createNewAccountsArea
            global classID
            global usernameEntry
            global passwordEntry
            global passArea
            global createNewSurveyArea

            #Destroys superfluous frames
            try:
                createNewSurveyArea.destroy()
            except:
                pass            
            try:
                surveyArea.destroy()
            except:
                pass
            try:
                statisticsArea.destroy()
            except:
                pass
            try:
                createNewAccountsArea.destroy()
            except:
                pass
            try:
                questionFrame.destroy()
            except:
                pass
            try:
                passArea.destroy()
            except:
                pass
            try:
                createButton.destroy()
            except:
                pass
            try:
                incorrectSurveyLabel.destroy()
            except:
                pass
            

            #Create a scrollable frame, and setting up the rest of the workspace 
            surveyArea = ScrollableFrame(schoolCouncilFrame, width = 800)
            surveylabels = {}
            parent = surveyArea.scrollableFrame
            parent.grid_rowconfigure(0, weight=1)
            parent.grid_columnconfigure(5, minsize=100)  # Here
            parent.grid_columnconfigure(6, minsize=100)
            parent.grid_columnconfigure(7, minsize=100)

            #Various headings for blue 'topbar'
            surveyText = tk.Label(parent, text = 'Surveys', padx = 20, pady = 20 , bg = '#ebf1f6', font = ('verdana', 12), fg = '#4d84af')
            surveyText.grid(column=0,row=0, sticky = "NSEW")

            classesSetToText = tk.Label(parent, text = 'Classes set to', bg = '#ebf1f6', padx = 20, pady = 20, font = ('verdana', 12), fg = '#4d84af')
            classesSetToText.grid(column=1,row=0, sticky = "NSEW")

            setDateText = tk.Label(parent, text = 'Set Date', bg = '#ebf1f6', padx = 20, pady = 20, font = ('verdana', 12), fg = '#4d84af')
            setDateText.grid(column=2,row=0, sticky = "NSEW")

            dueDateText = tk.Label(parent, text = 'Due Date', bg = '#ebf1f6', padx = 20, pady = 20, font = ('verdana', 12), fg = '#4d84af')
            dueDateText.grid(column=3,row=0, sticky = "NSEW")

            #creates the main table with all the surveys
            for i in range(1, len(allSurveys)+1):
                allS = allSurveys[i-1]
                details = getSurveyDetails(allS)
                label = {}   
                label["name"] = tk.Label(parent, text = details[0], padx = 20, pady = 20)
                label["name"].grid(column=0,row =i, sticky = "NSEW")
                label["classesSetTo"]= tk.Label(parent, text = details[1], padx = 20, pady = 20)
                label["classesSetTo"].bind('<Configure>', lambda e: label["classesSetTo"].config(wraplength=label["classesSetTo"].winfo_width()))
                label["classesSetTo"].grid(column=1,row=i, sticky = "NSEW")
                label["setDate"] = tk.Label(parent, text = details[2], padx = 20, pady = 20)
                label["setDate"].grid(column=2,row=i, sticky = "NSEW")
                label["dueDate"] = tk.Label(parent, text = details[3], padx = 20, pady = 20)
                label["dueDate"].grid(column=3,row=i, sticky = "NSEW")
                label["Editbutton"] = tk.Button(
                            parent,
                            bd = 0,
                            activeforeground = '#4d84af',
                            bg = 'grey',
                            fg = 'white',
                            activebackground = '#2f2f31',
                            text = 'Edit',
                            font = ('verdana', 10),
                            width = '8',
                            padx = 10,
                            pady = 10,
                            command = lambda allS=allS: editSurvey(allS)
                        )
                label["Editbutton"].grid(column = 5, row = i)
                if access < 1:
                    label["Editbutton"].config(state = 'disabled')
                label["Deletebutton"] = tk.Button(
                            parent,
                            bd = 0,
                            activeforeground = '#4d84af',
                            bg = 'grey',
                            fg = 'white',
                            activebackground = '#2f2f31',
                            text = 'Delete',
                            font = ('verdana', 10),
                            width = '8',
                            padx = 10,
                            pady = 10,
                            command = lambda allS=allS: deleteSurveyUI(allS)
                        )
                label["Deletebutton"].grid(column = 6, row = i)
                if access < 1:
                    label["Deletebutton"].config(state = 'disabled')
                label["DownloadDatabutton"] = tk.Button(
                            parent,
                            bd = 0,
                            activeforeground = '#4d84af',
                            bg = 'grey',
                            fg = 'white',
                            activebackground = '#2f2f31',
                            text = 'Download',
                            font = ('verdana', 10),
                            width = '8',
                            padx = 10,
                            pady = 10,
                            command = lambda allS=allS: doTheSaving(allS)
                        )
                label["DownloadDatabutton"].grid(column = 8, row = i)
                surveylabels[(allS)] = label
                label["DownloadSurveyButton"] = tk.Button(
                            parent,
                            bd = 0,
                            activeforeground = '#4d84af',
                            bg = 'grey',
                            fg = 'white',
                            activebackground = '#2f2f31',
                            text = 'Export offline',
                            font = ('verdana', 10),
                            width = '8',
                            padx = 10,
                            pady = 10,
                            command = lambda allS=allS: exportSurvey(allS)
                        )
                label["DownloadSurveyButton"].grid(column = 7, row = i)
                surveylabels[(allS)] = label
            #Pack the frame
            surveyArea.pack(side="right", fill="both", expand=True)

            #changes buttons to make sure active/inactive appearance is maintained, even after immediate click
            surveysButton.config(fg = '#4d84af', bg = '#2f2f31', text = '» Existing Surveys')
            statisticsButton.config(fg = 'white', bg = '#2f2f31', text = '« Survey Statistics')
            createNewAccountsButton.config(fg = 'white', bg = '#2f2f31', text = '« Create/Delete\nAccounts') 
            createNewSurveyButton.config(fg = 'white', bg = '#2f2f31', text = '« Create New \nSurvey')

            startUI.mainloop()

        #Sidebar buttons for School councillor    
        surveysButton = tk.Button(
            sidebar,
            bd = 0,
            activeforeground = '#4d84af',
            bg = '#2f2f31',
            fg = 'white',
            activebackground = '#2f2f31',
            text = '« Existing Surveys',
            anchor = tk.W,
            font = ('verdana', 12),
            width = '15',
            padx = 10,
            pady = 10,
            command = surveysButtonCommand
        )

        surveysButton.pack()

        statisticsButton = tk.Button(
            sidebar,
            bd = 0,
            activeforeground = '#4d84af',
            bg = '#2f2f31',
            fg = 'white',
            activebackground = '#2f2f31',
            text = '« Survey Statistics',
            anchor = tk.W,
            font = ('verdana', 12),
            width = '15',
            padx = 10,
            pady = 10,
            command = statistics
        )

        statisticsButton.pack()

        createNewSurveyButton = tk.Button(
            sidebar,
            bd = 0,
            activeforeground = '#4d84af',
            bg = '#2f2f31',
            fg = 'white',
            activebackground = '#2f2f31',
            text = '« Create New \nSurvey',
            anchor = tk.W,
            font = ('verdana', 12),
            width = '15',
            padx = 10,
            pady = 10,
            command = createNewSurvey
        )

        createNewSurveyButton.pack()

        #Disables buttons if access level is lower than set amount- creates distinction between user levels
        if access < 1:
            createNewSurveyButton.config(state = tk.DISABLED)

        createNewAccountsButton = tk.Button(
            sidebar,
            bd = 0,
            activeforeground = '#4d84af',
            bg = '#2f2f31',
            fg = 'white',
            activebackground = '#2f2f31',
            text = '« Create/Delete\nAccounts',
            anchor = tk.W,
            font = ('verdana', 12),
            width = '15',
            padx = 10,
            pady = 10,
            command = createNewAccounts
        )

        createNewAccountsButton.pack()
        if accessLevel >= ACCESSLEVELP:
            importButton = tk.Button(
                sidebar,
                bd = 0,
                activeforeground = '#4d84af',
                bg = '#2f2f31',
                fg = 'white',
                activebackground = '#2f2f31',
                text = '« Import',
                anchor = tk.W,
                font = ('verdana', 12),
                width = '15',
                padx = 10,
                pady = 10,
                command = importAndUpload
            )
            importButton.pack()



        if access < ACCESSLEVELA:
            createNewAccountsButton.config(state = tk.DISABLED)
        if not(usernameEntry == "latymer" and passwordEntry == "latymer"):
            changePassButton = tk.Button(
                sidebar,
                bd = 0,
                bg = '#2f2f31',
                fg = 'red',
                activebackground = '#2f2f31',
                text = 'Change Password',
                anchor = tk.W,
                font = ('verdana', 12),
                width = '15',
                padx = 10,
                pady = 10,
                command = changePass
            )

        welcomeText = tk.Label(
            sidebar,
            font = ('verdana', 9),
            text = 'Welcome ' + getSurveyorName(usernameEntry, passwordEntry)[0] + ',\nYou have ' + getAccessLevelName(int(access)) + ' level access',
            bg = '#2f2f31',
            fg = 'white',
            pady = 20,
            padx = 5,
            justify = tk.LEFT
        )

        logoutButton = tk.Button(
                        sidebar,
                        bd = 0,
                        activeforeground = '#4d84af',
                        bg = 'grey',
                        fg = 'white',
                        activebackground = '#2f2f31',
                        text = 'Logout',
                        font = ('verdana', 10),
                        width = '8',
                        padx = 10,
                        pady = 10,
                        command = login
                    )
        logoutButton.pack(anchor = "s", side = "bottom")
        if not(usernameEntry == "latymer" and passwordEntry == "latymer"):
            changePassButton.pack(anchor = "n", side = "bottom")
        welcomeText.pack(anchor = "sw", side = 'bottom')

        #Deletes a survey
        def deleteSurveyUI(surveyID):
            """Maps to delete survey button (school council UI)"""
            if(ctypes.windll.user32.MessageBoxW(0, "Are you sure you want to delete this survey", "Delete?", 4) == 6):
                deleteSurvey(surveyID, access)
                infoPopUp = tk.Toplevel()
                infoPopUp.minsize(100, 100)

                try:
                    icon = ImageTk.PhotoImage(Image.open(resourcePath("icon.png")))                                                             
                    icon.image = resourcePath("icon.png")            
                    infoPopUp.iconphoto(False, icon)
                except:
                    pass
                text = tk.Label(
                    infoPopUp,
                    text = 'You may have to restart the application for\n the changes to take effect',
                    padx = 10,
                    pady = 30
                )   

                text.pack()

                startUI.mainloop()     

        #Changes a survey (should maybe be on a different thread?)
        def changeSurvey(surveyTitleEntry, questionEntries, calendarselection, schoolCouncilFrame, surveyID):
            setSurvey(surveyTitleEntry, questionEntries, calendarselection, schoolCouncilFrame, surveyID = surveyID, afterDelete = True)

        #Edits a survey
        def editSurvey(surveyID):
            """Maps to edit survey button (school council UI)"""
            global schoolCouncilFrame
            global surveyArea
            global statisticsArea
            global createNewAccountsArea
            global classID
            global questionFrame
            global passArea
            global createNewSurveyArea
            global firstAddButton
            global createButton
            global questionEntries
            questionEntries = []
            #Destroys superfluous frames
            try:
                createNewSurveyArea.destroy()
            except:
                pass
            try:
                surveyArea.destroy()
            except:
                pass
            try:
                statisticsArea.destroy()
            except:
                pass
            try:
                createNewAccountsArea.destroy()
            except:
                pass
            try:
                questionFrame.destroy()
            except:
                pass
            try:
                passArea.destroy()
            except:
                pass

            createNewSurveyArea = ScrollableFrame(schoolCouncilFrame)
            parent = createNewSurveyArea.scrollableFrame
            parent.grid_rowconfigure(0, minsize=100)
            parent.grid_columnconfigure(0, minsize=10)
            parent.grid_columnconfigure(2, minsize=25)

            
            #Set up workspace
            for question in getAllQuestions(surveyID):
                questionData = getAllQuestionData(question)
                questionType = questionData["Question Type"]
                questionBody = questionData["Question"]
                try:
                    options = questionData["Options"]
                except:
                    options = []
                YesNo = questionData["YesNo"]
                if (questionType == QUESTIONTYPEOPTIONS) and YesNo:
                    questionType = 2
                tYears = questionData["Target Years"]
                questionNumber = questionData["Question Number"]
                addQuestion(position = questionNumber + 1, options = options, questionType = questionType, questionBody = questionBody, targetYears = tYears, parent = parent)
            surveyTitleLabel = ttk.Label(parent, text='Survey Title:', font = ("verdana", 18, "bold", "underline"))
            surveyTitleEntry = tk.Entry(parent, font = ('verdana', 15, "bold"), relief = tk.RIDGE)
            surveyTitleEntry.insert(0, getSurveyName(surveyID))
            dueDateLabel = ttk.Label(parent, text='Pick due date:', font = ("verdana", 18, "bold", "underline"))
            date = str(getDueDate(surveyID))
            year = int(date[0:4])
            month = int(date[5:7])
            day = int(date[8:10])
            calendar =  Calendar(parent, year = year, month = month, day=day)
            firstAddButton = tk.Button(
                        parent,
                        bd = 0,
                        activeforeground = '#4d84af',
                        bg = '#2f2f31',
                        fg = 'white',
                        activebackground = '#2f2f31',
                        text = 'Add Question',
                        font = ('verdana', 12),
                        command = lambda : addQuestion(1)
                        )
            createButton = tk.Button(
                        schoolCouncilFrame,
                        bd = 0,
                        activeforeground = '#4d84af',
                        bg = '#2f2f31',
                        fg = 'white',
                        activebackground = '#2f2f31',
                        text = 'Change',
                        font = ('verdana', 14, "bold", "underline"),
                        command = lambda : changeSurvey(surveyTitleEntry.get(), questionEntries, calendar.selection_get(), schoolCouncilFrame, surveyID)
                        )
            firstAddButton.grid(row = 2, column = 0)
            surveyTitleLabel.grid(row = 0, column = 0, padx = 10)
            surveyTitleEntry.grid(row = 0, column = 1, padx = 10)
            statisticsButton.config(fg = 'white', bg = '#2f2f31', text = '« Survey Statistics')
            surveysButton.config(fg = 'white', bg = '#2f2f31', text = '« Existing Surveys')
            createButton.pack(side = "bottom", anchor = "se", padx = 10, pady = 30)
            dueDateLabel.grid(row = 0, column = 2, padx = 10)
            calendar.grid(row = 0, column = 3, padx = 10)
            createNewSurveyArea.pack(side = "top", expand = True, fill = "both", anchor = "nw")

            startUI.mainloop()
        surveysButtonCommand()

        startUI.mainloop()


    def form(classID, function = None):
        """Possible page post login 2/2- for forms"""
        global backgroundLabel
        global loginFrame
        global toDoArea
        global missingArea
        global formFrame
        global offline


        def submitAnswerOnClick(classID, boxes): 
            """Submits survey to database"""
            global offlineSurvey
            global offlineclass
            correctPeople = {}
            answerDataParsed = {}
            try:
                offlineSurvey.answers = []
            except:
                pass
            for questionID in boxes.keys():
                answerData = []
                questionType = boxes[questionID]["QuestionType"]
                questionComplete = True
                for box in boxes[questionID]["Boxes"]:
                    boxVal = box.get()
                    if boxVal == "Enter number of students" or len(boxVal) == 0:
                        if questionType == QUESTIONTYPEOPTIONS:
                            questionComplete = False
                            answerData.append("")
                    else:
                        answerData.append(boxVal)

                answerDataParsed[questionID] = answerData
                if questionComplete and len(answerData) > 0:
                    if offline:
                        if questionType == QUESTIONTYPEOPTIONS:
                            totalPeopleSurveyed = 0
                            for data in answerData:
                                try:
                                    totalPeopleSurveyed += int(data)
                                except:
                                    correctPeople[questionID] = False
                            global offlinePeople
                            if int(offlinePeople) < totalPeopleSurveyed:
                                correctPeople[questionID] = False
                            else:
                                a = Answer(offlineclass, questionID, questionType, answerData, 1)
                                offlineSurvey.answers.append(a)
                                correctPeople[questionID] = True
                        else:
                            a = Answer(offlineclass, questionID, questionType, answerData, 1)
                            offlineSurvey.answers.append(a)
                            correctPeople[questionID] = True
                    else:
                        if(submitAnswer(answerData, questionID, classID, questionType)):
                            correctPeople[questionID] = True
                        else:
                            correctPeople[questionID] = False
                else:
                    correctPeople[questionID] = False
            allCorrect = True
            retake = {}

            for qid in correctPeople.keys():
                if not correctPeople[qid]:
                    allCorrect = False
                    retake[qid] = answerDataParsed[qid]
            if allCorrect:
                if offline:
                    saveSurvey(offlineSurvey)
                    ctypes.windll.user32.MessageBoxW(0, "Survey submitted, please now email the file to latdatascience@gmail.com", "Please email the survey response", 0)
                    startUI.destroy()
                else:
                    toDo()
            else:
                if offline:
                    takeSurveyOffline(None, retake = True, toRetake = retake)
                else:
                    takeSurvey(getContainingSurvey(qid), retake = True, toRetake = retake)

        def takeSurveyOffline(surveyID = None, retake = False, toRetake = []):
            """Maps to take survey button - allows form to view the survey and submit their responses when offline"""
            global formFrame
            global toDoArea
            global missingArea
            global questionFrame
            global offlineSurvey
            global loginFrame
            try:
                missingArea.destroy()
            except:
                pass
            try:
                toDoArea.destroy()
            except:
                pass
            try:
                questionFrame.destroy()
            except:
                pass
            
            #Set up workspace
            questionFrame = ScrollableFrame(startUI)
            boxData = {}
            parent = questionFrame.scrollableFrame
            parent.grid_rowconfigure(0, minsize=100)
            parent.grid_columnconfigure(0, minsize=10)
            parent.grid_columnconfigure(2, minsize=25)
            currentExternalRow = 1
            label = tk.Label(parent, text = offlineSurvey.name, padx = 10, pady = 10, font = ("verdana", 18, "bold", "underline"))
            label.grid(column=1,row=0, sticky = "W", columnspan = 4)
            def on_entry_click_peopleEntry(event, box):
                if box.cget('fg') == 'grey':
                    box.delete(0, "end") 
                    box.insert(0, '') 
                    box.config(fg = 'black', show = '')
                    
            def on_focusout_peopleEntry(event, box):
                if box.get() == '':
                    box.insert(0, 'Enter number of students')
                    box.config(fg = 'grey', show = '')


            #Spawns ability to view the survey questions and respond to them
            questions = offlineSurvey.getQuestions()
            for i in range(len(questions)):
                currentInternalRow = currentExternalRow
                question = questions[i]
                boxes = []
                labels = []
                questionID = question.questionID
                questionType = question.questionType
                boxData[questionID] = {}
                boxData[questionID]["QuestionType"] = questionType
                if questionType == QUESTIONTYPEOPTIONS:
                    questionBody, options = optionQuestionParse(question.questionBody)
                    for j in range(len(options)):
                        label = tk.Label(parent, text = options[j], padx = 10, pady = 10)
                        box = tk.Entry(parent)
                        label.grid(column=3,row=currentInternalRow, sticky = "EW")
                        box.grid(column=4,row=currentInternalRow, sticky = "EW")
                        labels.append(label)
                        box.bind('<FocusIn>', lambda x, box = box : on_entry_click_peopleEntry(x, box))
                        box.bind('<FocusOut>', lambda x, box = box : on_focusout_peopleEntry(x, box))
                        on_focusout_peopleEntry(None, box)
                        boxes.append(box)
                        currentInternalRow += 1
                    boxData[questionID]["Boxes"] = boxes
                    boxData[questionID]["Labels"] = labels
                    if retake:
                            if questionID in toRetake.keys():
                                label = tk.Label(parent, text = "Incorrect numbers", padx = 10, pady = 10)
                                label.grid(column=5,row=currentExternalRow, sticky = "EW")
                                for k in range(len(boxData[questionID]["Boxes"])):
                                    boxData[questionID]["Boxes"][k].delete(0, 'end')
                                    boxData[questionID]["Boxes"][k].insert(tk.END, str(toRetake[questionID][k]))
                                    on_focusout_peopleEntry(None, boxData[questionID]["Boxes"][k])
                else:
                    boxData[questionID]["Boxes"] = []
                    boxData[questionID]["Labels"] = []
                    def editBox(row, questionID, add):
                        global addRowButtons
                        global removeRowButtons
                        if add:
                            label = tk.Label(parent, text = str(row - boxData[questionID]["startRow"] + 1) + ")", padx = 10, pady = 10)
                            label.grid(column=3,row=row, sticky = "EW")
                            boxData[questionID]["Labels"].append(label)
                            box = tk.Entry(parent, width = 50)
                            box.grid(column=4,row=row, sticky = "EW", columnspan=2)
                            boxData[questionID]["Boxes"].append(box)
                        else:
                            if len(boxData[questionID]["Boxes"]) > 1:
                                boxData[questionID]["Labels"][len(boxData[questionID]["Labels"])-1].destroy()
                                boxData[questionID]["Labels"].pop(len(boxData[questionID]["Labels"])-1)
                                boxData[questionID]["Boxes"][len(boxData[questionID]["Boxes"])-1].destroy()
                                boxData[questionID]["Boxes"].pop(len(boxData[questionID]["Boxes"])-1)
                        try:
                            addRowButtons[questionID].destroy()
                        except:
                            pass
                        try:
                            removeRowButtons[questionID].destroy()
                        except:
                            pass
                        addRowButtons[questionID] = tk.Button(
                        parent,
                        bd = 0,
                        activeforeground = '#4d84af',
                        bg = '#2f2f31',
                        fg = 'white',
                        activebackground = '#2f2f31',
                        text = 'Add',
                        font = ('verdana', 12),
                        command = lambda questionID=questionID: editBox(boxData[questionID]["currentRow"], questionID, True)
                        )
                        if add:
                            addRowButtons[questionID].grid(column=4, row=row+1, sticky = "W")
                            boxData[questionID]["currentRow"] += 1
                        else:
                            addRowButtons[questionID].grid(column=4, row=row-1, sticky = "W")
                            boxData[questionID]["currentRow"] -= 1
                        removeRowButtons[questionID] = tk.Button(
                        parent,
                        bd = 0,
                        activeforeground = '#4d84af',
                        bg = '#2f2f31',
                        fg = 'white',
                        activebackground = '#2f2f31',
                        text = 'Remove',
                        font = ('verdana', 12),
                        command = lambda questionID=questionID: editBox(boxData[questionID]["currentRow"], questionID, False)
                        )
                        if add:
                            if len(boxData[questionID]["Boxes"]) > 1:
                                removeRowButtons[questionID].grid(column=5, row=row+1, sticky = "E")
                        else:
                            if len(boxData[questionID]["Boxes"]) > 1:
                                removeRowButtons[questionID].grid(column=5, row=row-1, sticky = "E")
                    questionBody = question.questionBody
                    boxData[questionID]["currentRow"] = currentInternalRow
                    boxData[questionID]["startRow"] = currentInternalRow
                    editBox (boxData[questionID]["currentRow"], questionID, True)
                    currentInternalRow+=100
                qLabel = tk.Label(parent, text =  str(i + 1) + ") " + questionBody, padx = 20, wraplength = 200)
                qLabel.grid(column = 1, row = currentExternalRow, sticky = "NEW", rowspan = 10)
                parent.grid_rowconfigure(currentInternalRow + 1, minsize=100)
                currentExternalRow = currentInternalRow + 2

            submitButton = tk.Button(
                questionFrame,
                bd = 0,
                activeforeground = '#4d84af',
                bg = '#2f2f31',
                fg = 'white',
                activebackground = '#2f2f31',
                text = 'Submit Current Answers',
                font = ('verdana', 12),
                padx = 10,
                pady = 10,
                command = lambda : submitAnswerOnClick(None, boxData)
            )
            if retake:
                label = tk.Label(questionFrame, text = "Some entries have been left blank", padx = 10, pady = 10, font = ("verdana", 18, "bold", "underline"))
                label.pack(side = "left", anchor = "se")
            submitButton.pack(side = "right", anchor = "se")

            questionFrame.pack(side = "top", expand = True, fill = "both", anchor = "nw")            
            startUI.mainloop()

        #Destroys superfluous frames
        try:
            backgroundLabel.destroy()
        except:
            pass
        try:
            loginFrame.destroy()
        except:
            pass
        if classID is None:
            takeSurveyOffline()




        #Sets up frames for form
        formFrame = tk.Frame(startUI, bd = 0)
        formFrame.pack(expand = tk.YES, fill = tk.BOTH, anchor = 'nw', side = "top")
        sidebar = tk.Frame(formFrame, width = 220, bg = '#2f2f31')
        sidebar.pack(expand = 0, fill = tk.BOTH, side = 'left', anchor = 'nw')
        logoutButton = tk.Button(
                        sidebar,
                        bd = 0,
                        activeforeground = '#4d84af',
                        bg = 'grey',
                        fg = 'white',
                        activebackground = '#2f2f31',
                        text = 'Logout',
                        font = ('verdana', 10),
                        width = '8',
                        padx = 10,
                        pady = 10,
                        command = login
                    )
        logoutButton.pack(anchor = "s", side = "bottom")

        todoSurveys, missingSurveys = getCurrentSurveysSplit(classID)


        #To do surveys
        def toDo():
            """One of 2 possible form pages- shows all surveys to do"""
            global toDoArea
            global missingArea
            global classID

            #Try to destroy previous windows if they exist
            try:
                missingArea.destroy()
            except:
                pass
            try:
                toDoArea.destroy()
            except:
                pass
            try:
                questionFrame.destroy()
            except:
                pass
            
            #Set up workspace
            toDoArea = ScrollableFrame(formFrame, width = 800)
            toDolabels = {}
            parent = toDoArea.scrollableFrame
            parent.grid_rowconfigure(0, weight=1)
            parent.grid_columnconfigure(5, minsize=100) 

            #Set up the table headings in the 'topbar'
            surveyText = tk.Label(parent, text = 'Surveys', padx = 20, pady = 20 , bg = '#ebf1f6', font = ('verdana', 12), fg = '#4d84af')
            surveyText.grid(column=0,row=0, sticky = "NSEW")

            percentageText = tk.Label(parent, text = 'Percent Complete', bg = '#ebf1f6', padx = 20, pady = 20, font = ('verdana', 12), fg = '#4d84af')
            percentageText.grid(column=1,row=0, sticky = "NSEW")

            setDateText = tk.Label(parent, text = 'Set Date', bg = '#ebf1f6', padx = 20, pady = 20, font = ('verdana', 12), fg = '#4d84af')
            setDateText.grid(column=2,row=0, sticky = "NSEW")

            dueDateText = tk.Label(parent, text = 'Due Date', bg = '#ebf1f6', padx = 20, pady = 20, font = ('verdana', 12), fg = '#4d84af')
            dueDateText.grid(column=3,row=0, sticky = "NSEW")
            
            qTimeText = tk.Label(parent, text = 'Time to Complete', bg = '#ebf1f6', padx = 20, pady = 20, font = ('verdana', 12), fg = '#4d84af')
            qTimeText.grid(column=4,row=0, sticky = "NSEW")

            #Calculates estimated time of completion
            for i in range(1, len(todoSurveys)+1):
                timeToComplete = 0               
                td = todoSurveys[i-1]
                for question in getQuestionsNotCompleted(td, classID):
                    if question[ID_QUESTIONTYPE] == QUESTIONTYPEOPEN:
                        timeToComplete += 6
                    else:
                         timeToComplete += 3

                #sets up main body of table, with all surveys and all information for the 'to-do' surveys
                label = {}   
                label["name"] = tk.Label(parent, text = getSurveyName(td), padx = 20, pady = 20)
                label["name"].grid(column=0,row =i, sticky = "NSEW")
                label["percentage"]= tk.Label(parent, text = percentageComplete(td, classID), padx = 20, pady = 20)
                label["percentage"].grid(column=1,row=i, sticky = "NSEW")
                label["setDate"] = tk.Label(parent, text = getSetDate(td), padx = 20, pady = 20)
                label["setDate"].grid(column=2,row=i, sticky = "NSEW")
                label["dueDate"] = tk.Label(parent, text = getDueDate(td), padx = 20, pady = 20)
                label["dueDate"].grid(column=3,row=i, sticky = "NSEW")
                label["QTime"] = tk.Label(parent, text = str(timeToComplete) + " minutes", padx = 20, pady = 20)
                label["QTime"].grid(column=4,row=i, sticky = "NSEW")
                label["button"] = tk.Button(
                            parent,
                            bd = 0,
                            activeforeground = '#4d84af',
                            bg = '#2f2f31',
                            fg = 'white',
                            activebackground = '#2f2f31',
                            text = 'Take',
                            font = ('verdana', 12),
                            width = '15',
                            padx = 10,
                            pady = 10,
                            command = lambda td=td: takeSurvey(td)
                        )
                label["button"].grid(column = 6, row = i, sticky = "EW")
                toDolabels[(td)] = label

            #Pack the frame
            toDoArea.pack(side="top", fill="both", expand=True)
            toDoButton.config(fg = '#4d84af', bg = '#2f2f31', text = '» To-do (' + str(len(todoSurveys)) + ')')
            missingButton.config(fg = 'white', bg = '#2f2f31', text = '« Missing (' + str(len(missingSurveys)) + ')')

        #Missing surveys
        def missing():
            """Page 2 of 2 for Forms (UI)- displays missing (overdue) surveys"""
            global toDoArea
            global missingArea
            global classID

            #Try to destroy previous windows if they exist
            try:
                toDoArea.destroy()
            except:
                pass
            try:
                missingArea.destroy()
            except:
                pass
            try:
                questionFrame.destroy()
            except:
                pass

            #Create a scrollable frame and set up rest of workspace
            missingArea = ScrollableFrame(formFrame, width = 800)
            missinglabels = {}
            parent = missingArea.scrollableFrame
            parent.grid_rowconfigure(0, weight=1)
            parent.grid_columnconfigure(5, minsize=100)  # Here

            #Set up 'topbar' table headings
            surveyText = tk.Label(parent, text = 'Surveys', padx = 20, pady = 20 , bg = '#ebf1f6', font = ('verdana', 12), fg = '#4d84af')
            surveyText.grid(column=0,row=0, sticky = "NSEW")

            percentageText = tk.Label(parent, text = 'Percent Complete', bg = '#ebf1f6', padx = 20, pady = 20, font = ('verdana', 12), fg = '#4d84af')
            percentageText.grid(column=1,row=0, sticky = "NSEW")

            setDateText = tk.Label(parent, text = 'Set Date', bg = '#ebf1f6', padx = 20, pady = 20, font = ('verdana', 12), fg = '#4d84af')
            setDateText.grid(column=2,row=0, sticky = "NSEW")

            dueDateText = tk.Label(parent, text = 'Due Date', bg = '#ebf1f6', padx = 20, pady = 20, font = ('verdana', 12), fg = '#4d84af')
            dueDateText.grid(column=3,row=0, sticky = "NSEW")
         
            qTimeText = tk.Label(parent, text = 'Time to Complete', bg = '#ebf1f6', padx = 20, pady = 20, font = ('verdana', 12), fg = '#4d84af')
            qTimeText.grid(column=4,row=0, sticky = "NSEW")


            #Creates rest of the table- all the missing surveys
            for i in range(1, len(missingSurveys)+1):
                timeToComplete = 0               
                td = missingSurveys[i-1]
                for question in getQuestionsNotCompleted(td, classID):
                    if question[ID_QUESTIONTYPE] == QUESTIONTYPEOPEN:
                        timeToComplete += 6
                    else:
                         timeToComplete += 3

                label = {}   
                label["name"] = tk.Label(parent, text = getSurveyName(td), padx = 20, pady = 20)
                label["name"].grid(column=0,row =i, sticky = "NSEW")
                label["percentage"]= tk.Label(parent, text = percentageComplete(td, classID), padx = 20, pady = 20)
                label["percentage"].grid(column=1,row=i, sticky = "NSEW")
                label["setDate"] = tk.Label(parent, text = getSetDate(td), padx = 20, pady = 20)
                label["setDate"].grid(column=2,row=i, sticky = "NSEW")
                label["dueDate"] = tk.Label(parent, text = getDueDate(td), padx = 20, pady = 20)
                label["dueDate"].grid(column=3,row=i, sticky = "NSEW")
                label["QTime"] = tk.Label(parent, text = str(timeToComplete) + " minutes", padx = 20, pady = 20)
                label["QTime"].grid(column=4,row=i, sticky = "NSEW")
                label["button"] = tk.Button(
                            parent,
                            bd = 0,
                            activeforeground = '#4d84af',
                            bg = '#2f2f31',
                            fg = 'white',
                            activebackground = '#2f2f31',
                            text = 'Take',
                            font = ('verdana', 12),
                            width = '15',
                            padx = 10,
                            pady = 10,
                            command = lambda td=td: takeSurvey(td)
                        )
                label["button"].grid(column = 6, row = i, sticky = "EW")
                missinglabels[(td)] = label

            #Pack the frame
            missingArea.pack(side="right", fill="both", expand=True)

            #Configure buttons so that they remain changed, even after initial click/revert back to original form
            missingButton.config(fg = '#4d84af', bg = '#2f2f31', text = '» Missing (' + str(len(missingSurveys)) + ')')
            toDoButton.config(fg = 'white', bg = '#2f2f31', text = '« To-do (' + str(len(todoSurveys)) + ')')

        
        #Main Form window buttons (available on sidebar)
        toDoButton = tk.Button(
            sidebar,
            bd = 0,
            activeforeground = '#4d84af',
            bg = '#2f2f31',
            fg = 'white',
            activebackground = '#2f2f31',
            text = '« To-do (' + str(len(todoSurveys)) + ')',
            anchor = tk.W,
            font = ('verdana', 12),
            width = '15',
            padx = 10,
            pady = 10,
            command = toDo
        )

        toDoButton.pack()

        missingButton = tk.Button(
            sidebar,
            bd = 0,
            activeforeground = '#4d84af',
            bg = '#2f2f31',
            fg = 'white',
            activebackground = '#2f2f31',
            text = '« Missing (' + str(len(missingSurveys)) + ')',
            anchor = tk.W,
            font = ('verdana', 12),
            width = '15',
            padx = 10,
            pady = 10,
            command = missing
        )

        missingButton.pack()

        welcomeText = tk.Label(
            sidebar,
            font = ('verdana', 9),
            text = 'Welcome Class ' + getClassName(classID),
            bg = '#2f2f31',
            fg = 'white',
            pady = 20,
            padx = 10
        )

        welcomeText.pack(anchor = "sw", side = "bottom")

        def takeSurvey(surveyID, retake = False, toRetake = {}):
            """Maps to take survey button- allows form to view the survey and submit their responses"""
            global formFrame
            global toDoArea
            global missingArea
            global classID
            global questionFrame

            try:
                missingArea.destroy()
            except:
                pass
            try:
                toDoArea.destroy()
            except:
                pass
            try:
                questionFrame.destroy()
            except:
                pass
            
            #Set up workspace
            questions = getQuestionsNotCompleted(surveyID, classID)
            questionFrame = ScrollableFrame(formFrame)
            boxData = {}
            parent = questionFrame.scrollableFrame
            parent.grid_rowconfigure(0, minsize=100)
            parent.grid_columnconfigure(0, minsize=10)
            parent.grid_columnconfigure(2, minsize=25)
            currentExternalRow = 1
            label = tk.Label(parent, text = getSurveyName(surveyID), padx = 10, pady = 10, font = ("verdana", 18, "bold", "underline"))
            label.grid(column=1,row=0, sticky = "W", columnspan = 4)

            def on_entry_click_peopleEntry(event, box):
                if box.cget('fg') == 'grey':
                    box.delete(0, "end") 
                    box.insert(0, '') 
                    box.config(fg = 'black', show = '')
                    
            def on_focusout_peopleEntry(event, box):
                if box.get() == '':
                    box.insert(0, 'Enter number of students')
                    box.config(fg = 'grey', show = '')


            #Spawns ability to view the survey questions and respond to them - probably should be in a class but didn't have time :)
            #To that end, there is a complicated dictionary/array structure (sorry :( )
            #The box data dictionary stores: {QuestionID : {QuestionData}}
            #Labels and Boxes are arrays of the boxes and their labels per survey question
            #The dictionary format is {QuestionID : {"Boxes" : [ListOfBoxes], "Labels" : [ListOfLabels], "startRow" : integer, "currentRow" : integer}}
            for i in range(len(questions)):
                currentInternalRow = currentExternalRow
                question = questions[i]
                boxes = []
                labels = []
                questionID = question[ID_QUESTIONID]
                questionType = question[ID_QUESTIONTYPE]
                boxData[questionID] = {}
                boxData[questionID]["QuestionType"] = questionType
                if questionType == QUESTIONTYPEOPTIONS:
                    questionBody, options = optionQuestionParse(question[ID_QUESTIONBODY])
                    for j in range(len(options)):
                        label = tk.Label(parent, text = options[j], padx = 10, pady = 10)
                        box = tk.Entry(parent)
                        label.grid(column=3,row=currentInternalRow, sticky = "EW")
                        box.grid(column=4,row=currentInternalRow, sticky = "EW")
                        labels.append(label)
                        box.bind('<FocusIn>', lambda x, box = box : on_entry_click_peopleEntry(x, box))
                        box.bind('<FocusOut>', lambda x, box = box : on_focusout_peopleEntry(x, box))
                        on_focusout_peopleEntry(None, box)
                        boxes.append(box)
                        currentInternalRow += 1
                    boxData[questionID]["Boxes"] = boxes
                    boxData[questionID]["Labels"] = labels
                    if retake:
                            if questionID in toRetake.keys():
                                label = tk.Label(parent, text = "Incorrect numbers", padx = 10, pady = 10)
                                label.grid(column=5,row=currentExternalRow, sticky = "EW")
                                for k in range(len(boxData[questionID]["Boxes"])):
                                    boxData[questionID]["Boxes"][k].delete(0, 'end')
                                    boxData[questionID]["Boxes"][k].insert(tk.END, str(toRetake[questionID][k]))
                                    on_focusout_peopleEntry(None, boxData[questionID]["Boxes"][k])
                else:
                    boxData[questionID]["Boxes"] = []
                    boxData[questionID]["Labels"] = []
                    def editBox(row, questionID, add):
                        global addRowButtons
                        global removeRowButtons
                        if add:
                            label = tk.Label(parent, text = str(row - boxData[questionID]["startRow"] + 1) + ")", padx = 10, pady = 10)
                            label.grid(column=3,row=row, sticky = "EW")
                            boxData[questionID]["Labels"].append(label)
                            box = tk.Entry(parent, width = 50)
                            box.grid(column=4,row=row, sticky = "EW", columnspan=2)
                            boxData[questionID]["Boxes"].append(box)
                        else:
                            if len(boxData[questionID]["Boxes"]) > 1:
                                boxData[questionID]["Labels"][len(boxData[questionID]["Labels"])-1].destroy()
                                boxData[questionID]["Labels"].pop(len(boxData[questionID]["Labels"])-1)
                                boxData[questionID]["Boxes"][len(boxData[questionID]["Boxes"])-1].destroy()
                                boxData[questionID]["Boxes"].pop(len(boxData[questionID]["Boxes"])-1)
                        try:
                            addRowButtons[questionID].destroy()
                        except:
                            pass
                        try:
                            removeRowButtons[questionID].destroy()
                        except:
                            pass
                        addRowButtons[questionID] = tk.Button(
                        parent,
                        bd = 0,
                        activeforeground = '#4d84af',
                        bg = '#2f2f31',
                        fg = 'white',
                        activebackground = '#2f2f31',
                        text = 'Add',
                        font = ('verdana', 12),
                        command = lambda questionID=questionID: editBox(boxData[questionID]["currentRow"], questionID, True)
                        )
                        if add:
                            addRowButtons[questionID].grid(column=4, row=row+1, sticky = "W")
                            boxData[questionID]["currentRow"] += 1
                        else:
                            addRowButtons[questionID].grid(column=4, row=row-1, sticky = "W")
                            boxData[questionID]["currentRow"] -= 1
                        removeRowButtons[questionID] = tk.Button(
                        parent,
                        bd = 0,
                        activeforeground = '#4d84af',
                        bg = '#2f2f31',
                        fg = 'white',
                        activebackground = '#2f2f31',
                        text = 'Remove',
                        font = ('verdana', 12),
                        command = lambda questionID=questionID: editBox(boxData[questionID]["currentRow"], questionID, False)
                        )
                        if add:
                            if len(boxData[questionID]["Boxes"]) > 1:
                                removeRowButtons[questionID].grid(column=5, row=row+1, sticky = "E")
                        else:
                            if len(boxData[questionID]["Boxes"]) > 1:
                                removeRowButtons[questionID].grid(column=5, row=row-1, sticky = "E")
                    questionBody = question[ID_QUESTIONBODY]
                    boxData[questionID]["currentRow"] = currentInternalRow
                    boxData[questionID]["startRow"] = currentInternalRow
                    editBox (boxData[questionID]["currentRow"], questionID, True)
                    currentInternalRow+=100
                qLabel = tk.Label(parent, text =  str(i + 1) + ") " + questionBody, padx = 20, wraplength = 200)
                qLabel.grid(column = 1, row = currentExternalRow, sticky = "NEW", rowspan = 10)
                parent.grid_rowconfigure(currentInternalRow + 1, minsize=100)
                currentExternalRow = currentInternalRow + 2

            submitButton = tk.Button(
                questionFrame,
                bd = 0,
                activeforeground = '#4d84af',
                bg = '#2f2f31',
                fg = 'white',
                activebackground = '#2f2f31',
                text = 'Submit Current Answers',
                font = ('verdana', 12),
                padx = 10,
                pady = 10,
                command = lambda : submitAnswerOnClick(classID, boxData)
            )

            submitButton.pack(side = "right", anchor = "se")
            questionFrame.pack(side = "top", expand = True, fill = "both", anchor = "nw")
            
            startUI.mainloop()

        
        
        toDo()
        startUI.mainloop()

    #Home page
    def login():
        """First UI frame- the login page"""
        global userName
        global passWord
        global usernameEntry
        global passwordEntry
        global backgroundLabel
        global loginFrame
        global loginButton
        global schoolCouncilFrame
        global formFrame
        usernameEntry = ""
        passwordEntry = ""
        try:
            schoolCouncilFrame.destroy()
        except:
            pass
        try:
            formFrame.destroy()
        except:
            pass

        #Set up login Frames
        loginFrame = tk.Frame(startUI, bd=0)
        loginFrame.pack(expand = True, fill = tk.BOTH)

        def resize_image(event):
            """Dynamically resizes background image"""
            new_width = event.width
            new_height = event.height
            image = copy_of_image.resize((new_width, new_height))
            photo = ImageTk.PhotoImage(image)
            backgroundLabel.config(image = photo)
            backgroundLabel.image = photo #avoid garbage collection

        #Puts in the background image
        try:
            background = Image.open(resourcePath("combined.png"))
            copy_of_image = background.copy()
            background = ImageTk.PhotoImage(background)
            backgroundLabel = tk.Label(startUI, image = background)
            backgroundLabel.bind('<Configure>', resize_image)
            backgroundLabel.pack(fill=tk.BOTH, expand=tk.YES)
        except:
            backgroundLabel = tk.Label(startUI)
            backgroundLabel.pack(fill=tk.BOTH, expand=tk.YES)


        #Allows the 'focus in/focus out' effect of the username and password entry widgets
        def on_entry_click(event):
            if userName.cget('fg') == 'grey':
                userName.delete(0, "end") # delete all the text in the userName
                userName.insert(0, '') #Insert blank for user input
                userName.config(fg = 'black')

        def on_focusout(event):
            if userName.get() == '':
                userName.insert(0, 'username')
                userName.config(fg = 'grey')

        def on_entry_click2(event):
            if passWord.cget('fg') == 'grey':
                passWord.delete(0, "end") 
                passWord.insert(0, '') 
                passWord.config(fg = 'black', show = '•')
                
        def on_focusout2(event):
            if passWord.get() == '':
                passWord.insert(0, 'password (not forms)')
                passWord.config(fg = 'grey', show = '')

        userName = tk.Entry(
            startUI,
            bg = '#ffffff',
            bd = 1, 
            font = ('verdana', 12), 
            fg = '#f0000f', 
            relief = tk.RIDGE)

        userName.insert(0, 'Username')
        userName.bind('<FocusIn>', on_entry_click)
        userName.bind('<FocusOut>', on_focusout)
        userName.bind('<Return>', lambda e: levelOfAccess())
        userName.config(fg = 'grey')
        userName.place(relx = 0.60, rely = 0.43, relwidth = 0.14)

        passWord = tk.Entry(
            startUI, 
            bg = '#ffffff', 
            bd = 1, 
            font = ('verdana', 12), 
            fg = '#f0000f', 
            relief = tk.RIDGE)

        passWord.insert(0, 'Password (not forms)')
        passWord.bind('<FocusIn>', on_entry_click2)
        passWord.bind('<FocusOut>', on_focusout2)
        passWord.bind('<Return>', lambda e : levelOfAccess())
        passWord.config(fg = 'grey')
        passWord.place(relx = 0.60, rely = 0.52, relwidth = 0.14)

        loginButton = tk.Button(
            startUI,
            text = 'login',
            activebackground = '#000000',
            activeforeground = '#bbbbbb',
            fg = '#555555',
            bd = 0,
            command = levelOfAccess
        )

        loginButton.place(relx = 0.72, rely = 0.6)

        startUI.mainloop()

    #Calls the main login function and starts off the rest of the UI as soon as the start() function is called
    login()
    




##########################################################################################################################
####################################################### DB CONNECTIVITY ##################################################
##########################################################################################################################

#Connects to MySQL DB
def connectMySQLDatabase():
    try:
        lines = ["" for i in range(6)]
        lines[0]=SERVERADDRESS
        lines[1]=PORT
        lines[2]=USERNAME
        lines[3]=PASSWORD
        lines[4]=DATABASE
        db = mysql.connector.connect(
            host=lines[0],
            port = int(lines[1]),
            username=lines[2],
            password=lines[3]
        )
        cursor = db.cursor()
        sql = "USE " + lines[4]
        cursor.execute(sql)
        return db, cursor
    except:
        return "False", None

#Connects to MicrosoftSQL DB
def connectMicrosoftSQLDatabase():
    try:
        db = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + SERVERADDRESS + ';DATABASE=' + DATABASE + ';UID=' + USERNAME + ';PWD=' + PASSWORD)
        cursor = db.cursor()
        sql = "USE " + DATABASE
        cursor.execute(sql)
        return db, cursor
    except:
        return "False", None

#Adds zeros to the front of a number
def addZeros(number, totalChars):
    outString = ""
    zerosToAdd = totalChars - len(str(number))
    for i in range(zerosToAdd):
        outString += "0"
    outString += str(number)
    return outString

#Finds out if one list consists of only terms in another
def isSublist(biglist, smallist):
    for item in smallist:
        if item not in biglist:
            return False
    return True 

#Gets the key with the largest value
def getBiggestKey(dictionary):
    currentBiggest = -1
    currentBiggestKey = ""
    twoSame = False
    for key in dictionary.keys():
        twoSame = dictionary[key] == currentBiggest
        if dictionary[key] > currentBiggest:
            currentBiggest = dictionary[key] 
            currentBiggestKey = key
    if twoSame:
        return TWOSAME
    return currentBiggestKey

#looks nice n(n)

##########################################################  YEAR FUNCTIONS #################################################

#Checks if it is a new school year
def reshuffleNeeded():
    sql = ("SELECT paramValue FROM Admin WHERE paramName = 'reshuffleDue'")
    csr.execute(sql)
    rdate = csr.fetchall()[0][0]
    fulldate = datetime.strptime(rdate, '%Y-%m-%d').date()
    return date.today() > fulldate

#Gets the current school year
def getCurrentSchoolYear():
    today = date.today()
    todayStr = date.today().strftime('%Y-%m-%d')
    currentYear = todayStr[0:4]
    rdate = currentYear + "-09-01"
    compareDate = datetime.strptime(rdate, '%Y-%m-%d').date()
    if today > compareDate:
        return int(currentYear)
    else:
        return int(currentYear) - 1

#Gets the school year a survey was made
def getSchoolYear(surveyID):
    return str(getDueDate(surveyID))[0:4]

#Create new class accounts
def reshuffle(houses, years):
    sql = ("SELECT classID FROM Class WHERE schoolYear = " + str(getCurrentSchoolYear()))
    csr.execute(sql)
    classes = [i[0] for i in csr.fetchall()]
    for classID in classes:
        deleteClass(classID, ACCESSLEVELP)
    for year in years:
        for house in houses:
            createClass(str(year) + house, ACCESSLEVELP)
    sql = ("SELECT username FROM CouncilMember WHERE accessLevel < 3")
    csr.execute(sql)
    councillors = [i[0] for i in csr.fetchall()]
    for councillor in councillors:
        deleteSurveyorAccount(councillor, ACCESSLEVELP)

#Checks if a new class name is valid (Form YCC or YYCC or YYCCC where Y is an integer and C is a character)
def validClassName(className):
    if len(className) == 3 or len(className) == 2:
        try:
            if int(className[0:1]) < 7:
                try:
                    if int(className[0:2] > 11):
                        return False
                except:
                    pass
        except:
            return False
        try:
            int(className[1])
            try:
                int(className[0:2])
            except:
                return False
        except:
            pass
    elif len(className) == 4:
        try:
            if int(className[0:2]) > 13 or int(className[0:2]) < 10:
                return False
        except:
            return False
    elif len(className) == 5:
        try:
            if int(className[0:2]) > 13 or int(className[0:2]) < 12:
                return False
        except:
            return False
    else:
        return False
    try:
        int(className[2])
        return False
    except:
        pass
    try:
        int(className[3])
        return False
    except:
        pass
    try:
        int(className[4])
        return False
    except:
        pass
    return True

#Sets a new school year date
def setReshuffleDate():
    fulldate = str(date.today().strftime('%Y-%m-%d'))
    newDate = str(int(fulldate[0:4])+1) + "-09-01"
    sql = ("UPDATE Admin SET paramValue = '" + newDate +
        "' WHERE paramName = 'reshuffleDue'")
    csr.execute(sql)
    db.commit()
    

######################################################## LOGIN FUNCTIONS ###########################################################

#Logs in a user, returning Success, UserType, UserData
def sqlLogin(username, password):
    """Logs in a class or councillor"""
    if reshuffleNeeded():
        reshuffle(["A", "D", "K", "LB", "LT", "W"], [7,8,9,10,11])
        setReshuffleDate()
    classdetails = checkClassDetails(username)
    global allClassesList
    allClassesList = getAllClasses(getCurrentSchoolYear())
    if classdetails == -1:
        accesslevel = loginSurveyor(username, password)
        if  accesslevel == -1:
            if username == password and validClassName(username):
                success, classID = createClass(username, ACCESSLEVELP)
                return success, ID_CLASS_NEW, classID
            return False, None, None
        else:
            return True, ID_SURVEYOR, accesslevel
    else:
        if getClassPeople(classdetails) == -1:
            return True, ID_CLASS_NEW, classdetails
        else:
            return True, ID_CLASS, classdetails

#Returns a classID from valid username, otherwise -1
def checkClassDetails(username):
    try:
        sql = ("SELECT classID FROM Class WHERE username = '" + username + "'" "AND schoolYear = " + str(getCurrentSchoolYear()))
        csr.execute(sql)
        out=csr.fetchall()
        if(len(out) == 0):
            return -1
        else:
            return out[0][0]
    except:
        return -1

#Checks a user's credentials
def loginSurveyor(username, password):
    sql = ("SELECT accessLevel, username, password from CouncilMember WHERE username = '" + username + "' AND password = '" + password + "'")
    csr.execute(sql)
    try:
        outData = csr.fetchall()
        if(len(outData) == 0):
            return -1
        else:
            if username == outData[0][1] and password == outData[0][2]:
                return outData[0][0]
            else:
                return -1
    except:
        return -1

#######################################################  COUNCILLOR ACCOUNT FUNCTIONS ##########################################

#Changes a user's password
def changePassword(username, password, newpassword):
    """Change password to newpassword"""
    sql = ("SELECT * FROM CouncilMember WHERE username = '" + username + "' AND password = '" + password + "'")
    csr.execute(sql)
    if len(csr.fetchall()[0]) != 0:
        sql = ("UPDATE CouncilMember SET password = '" + newpassword + 
        "' WHERE username = '" + username + "' AND password = '" + password + "'")
        csr.execute(sql)
        db.commit()
        return True
    return False

#Creates a new councillor
def createSurveyor(username, password, accessLevel, myAccessLevel, firstname = "Not_Set", surname = "Not_Set"):
    """Create a new councillor"""#
    if int(accessLevel) < int(myAccessLevel):
        sql = ("SELECT MAX(memberID) AS maxMID FROM CouncilMember")
        csr.execute(sql)
        try:
            newMID = int(csr.fetchall()[0][0]) + 1
        except:
            newMID = 0
        
        sql = ("INSERT INTO CouncilMember (memberID, username, password, accessLevel, firstname, surname) "
                "VALUES (" + str(newMID) + ", '" + username + "', '" + password + "', " + str(accessLevel) + ", '" + firstname + "', '" + surname + "')")
        csr.execute(sql)
        db.commit()
        return True
    return False

#Gets councillor name
def getSurveyorName(username, password):
    """Gets a councillor's name"""
    sql = ("SELECT Firstname, Surname FROM CouncilMember WHERE username = '" + username + "' AND password = '" + password + "'")
    csr.execute(sql)
    return csr.fetchall()[0]

def getSurveyorAccessLevel(username):
    """Gets a councillor's access level"""
    sql = ("SELECT accessLevel FROM CouncilMember WHERE username = '" + username + "'")
    csr.execute(sql)
    return csr.fetchall()[0][0]

#Delete a councillor account
def deleteSurveyorAccount(username, myAccessLevel):
    """Delete a councillor account"""
    try:
        if getSurveyorAccessLevel(username) < myAccessLevel:
            sql = ("DELETE FROM CouncilMember WHERE username = '" + username + "'")
            csr.execute(sql)
            db.commit()
            return True
        else:
            return False
    except:
        return False


#Gets the possible different access levels below ones access level
def getPossibleAccessLevelNames(accessLevel):
    values = []
    for i in range(accessLevel):
        value = getAccessLevelName(i)
        value = value[0].upper() + value[1:]
        values.append(value)
    return values


#Translates a number access level into a text string
def getAccessLevelName(accessLevel):
    if accessLevel == ACCESSLEVELR:
        return "view"
    if accessLevel == ACCESSLEVELRW:
        return "edit"
    if accessLevel == ACCESSLEVELA:
        return "administrator"
    if accessLevel == ACCESSLEVELS:
        return "system"
    if accessLevel == ACCESSLEVELP:
        return "program"

########################################################### CLASS ACCOUNT FUNCTIONS ##############################################

#Gets a list of all classes
def getAllClasses(schoolYear):
    """Returns a list of all classes"""
    sql = ("SELECT classID FROM Class WHERE schoolYear = " + str(schoolYear))
    csr.execute(sql)
    return [i[0] for i in csr.fetchall()]

#Gets the first available classID
def getNewClassID(year, currentClasses):
    classesInYear = []
    for currentClass in currentClasses:
        if getYear(classID = currentClass) == year:
            classesInYear.append(currentClass)
    try:
        currentCID = classesInYear[0]
    except:
        currentCID = int(str(year) + "01")
    for classID in classesInYear:
        if classID != currentCID:
            return currentCID
        currentCID += 1
    return currentCID

#Creates a new account and returns the class username
def createClass(classname, myAccessLevel, people = -1, schoolYear = getCurrentSchoolYear()):
    classname = classname.upper()
    if validClassName(classname):
        if myAccessLevel >= ACCESSLEVELA:
            """Creates a new class"""
            year = getYear(name = classname)
            classID = getNewClassID(year, getAllClasses(schoolYear))
            sql = ("INSERT INTO Class (classID, username, schoolYear, people) " +
                    " VALUES (" + str(classID) + ", '" + classname + "', " + str(schoolYear) + ", " + str(people) + ")")
            csr.execute(sql)
            db.commit()
            for surveyID in loadAllSurveys():
                if year in getTargetYears(surveyID):
                    sql = ("INSERT INTO ClassSurvey (surveyID, classID, completed) " +
                    " VALUES (" + str(surveyID) + ", " + str(classID) + ", " + str(0) + ")")
                    csr.execute(sql)
                    db.commit()
                    for questionID in getAllQuestions(surveyID):
                        if year in getTargetYearsQuestion(questionID):
                            sql = ("INSERT INTO Answer (classID, questionID, complete) "
                            "VALUES (" + str(classID) + ", " + str(questionID) +  ", " + str(0) + ")")
                            csr.execute(sql)
                            db.commit()
            classNameMap[classID] = classname
            return True, classID
    return False, None

#Changes the name of a class
def changeClassName(classID, newName, myAccessLevel):
    newName = newName.upper()
    if myAccessLevel >= ACCESSLEVELA:
        """Change the username of a class"""
        sql = ("UPDATE Class SET username = " + str(newName) +
            " WHERE classID = " + str(classID))
        csr.execute(sql)
        db.commit()
        return True
    return False

#Changes the number of people in a class
def changeClassPeople(classID, newPeople, myAccessLevel):
    if myAccessLevel >= ACCESSLEVELA:
        """Change the number of people in the class"""
        sql = ("UPDATE Class SET people = " + str(newPeople) +
            " WHERE classID = " + str(classID))
        csr.execute(sql)
        db.commit()
        return True
    return False

#Gets the number of people in a class
def getClassPeople(classID):
    """Get the number of people in a class"""
    sql = ("SELECT people FROM Class WHERE classID = " + str(classID))
    csr.execute(sql)
    return csr.fetchall()[0][0]

#Deletes a class by classID
def deleteClass(classID, myAccessLevel):
    """Delete a class"""
    if myAccessLevel >= ACCESSLEVELA:
        sql = ("DELETE FROM ClassSurvey WHERE classID = " + str(classID))
        csr.execute(sql)
        db.commit()
        sql = ("DELETE FROM Answer WHERE classID = " + str(classID))
        csr.execute(sql)
        db.commit()
        sql = ("DELETE FROM Class WHERE classID = " + str(classID))
        csr.execute(sql)
        db.commit()
        return True
    return False

############################################ SURVEY / QUESTION EDITTING FUNCTIONS #######################################################

#Makes a new survey, returns the surveyID if successful, otherwise returns False
def newSurvey(name, targetYears, dateDue, myAccessLevel = ACCESSLEVELP, schoolYear = getCurrentSchoolYear(), surveyID = None):
    """Make a new survey"""
    global allClassesList
    try:
        if myAccessLevel >= ACCESSLEVELRW:
            sql = ("SELECT MAX(surveyID) AS maxSID FROM Survey")
            csr.execute(sql)
            if surveyID is None:
                try:
                    newSID = int(csr.fetchall()[0][0]) + 1
                except:
                    newSID = 0
            else:
                newSID = surveyID
            classes = allClassesList
            name = name.replace("'", "''")
            sql = ("INSERT INTO Survey (surveyID, name, numberOfQuestions, setDate, dueDate, targetYears) "
                    "VALUES (" + str(newSID) + ", '" + name + "', " + str(0) + ", '" + str(date.today().strftime('%Y-%m-%d')) + "', '" + dateDue + "', '" + targetYearsCompile(targetYears)+ "')")
            csr.execute(sql) 
            db.commit()
            for classID in classes:
                if int(getYear(classID=classID)) in targetYears:
                    sql = ("INSERT INTO ClassSurvey (classID, surveyID, completed) "
                    "VALUES (" + str(classID) + ", " + str(newSID) + ", " + str(0) +  ")")
                    csr.execute(sql)
                    db.commit()
            return newSID
        return "False"
    except:
        return "False"

#Makes a new question, returns the questionID if successful, otherwise returns False
def newQuestion(qType, body, surveyID, targetYears, myAccessLevel = ACCESSLEVELP, options = ["Yes", "No"], schoolYear = getCurrentSchoolYear(), questionID = None, questionNum = None):
    """Make a new question"""
    try:
        if myAccessLevel >= ACCESSLEVELRW:
            if qType == QUESTIONTYPEOPTIONS:
                body = optionQuestionCompile(body, options)
            sql = ("SELECT MAX(questionID) AS maxQID FROM Question")
            csr.execute(sql)
            if questionID is None:
                try:
                    newQID = int(csr.fetchall()[0][0]) + 1
                except:
                    newQID = 0
            else:
                newQID = questionID
            sql = ("SELECT MAX(QuestionNumber) AS maxQN FROM Question WHERE surveyID = " + str(surveyID))
            csr.execute(sql)
            if questionNum is None:
                try:
                    newQN = int(csr.fetchall()[0][0]) + 1
                except:
                    newQN = 0
            else:
                newQN = questionNum
            body = body.replace("\'", "\'\'")
            sql = ("INSERT INTO Question (questionID, surveyID, questionType, questionBody, questionNumber, targetYears) "
                    "VALUES (" + str(newQID) + ", " + str(surveyID) + ", " + str(qType) + ", '" + body + "', " + str(newQN)  + ", '" + targetYearsCompile(targetYears)+ "')")
            csr.execute(sql)
            db.commit()
            global allClassesList
            classes = allClassesList
            for classID in classes:
                if int(getYear(classID=classID)) in targetYears:
                    sql = ("INSERT INTO Answer (classID, questionID, complete) "
                    "VALUES (" + str(classID) + ", " + str(newQID) +  ", " + str(0) + ")")
                    csr.execute(sql)
                    db.commit()
            sql = ("UPDATE Survey SET numberOfQuestions = " + str(getTotalNumberOfQuestions(surveyID) + 1) + " WHERE surveyID = " + str(surveyID))
            csr.execute(sql)
            db.commit()
            return newQID
        return "False"
    except:
        return "False"

#Sets the order of questions
def setQuestionOrder(questionIDs):
    """Set the order of questions based on an ordered list of questionIDs"""
    for i in range(len(questionIDs)):
        sql = ("UPDATE Question SET questionNumber = " + str(i) +
                " WHERE questionID = " + str(questionIDs[i]))
        csr.execute(sql)
        db.commit()

#Deletes a question
def deleteQuestion(questionID, myAccessLevel = ACCESSLEVELP):
    """Deletes a question"""
    if myAccessLevel >= ACCESSLEVELRW:
        surveyID = getContainingSurvey(questionID)
        sql = ("DELETE FROM Answer WHERE questionID  = " + str(questionID))
        csr.execute(sql)
        db.commit()
        sql = ("DELETE FROM Question WHERE questionID  = " + str(questionID))
        csr.execute(sql)
        db.commit()
        sql = ("UPDATE Survey SET numberOfQuestions = " + str(getTotalNumberOfQuestions(surveyID) + 1) + " WHERE surveyID = " + str(surveyID))
        csr.execute(sql)
        db.commit()
        return True
    return False

#Delete a survey
def deleteSurvey(surveyID, myAccessLevel = ACCESSLEVELP):
    """Deletes a survey"""
    if myAccessLevel >= ACCESSLEVELRW:
        sql = ("DELETE FROM ClassSurvey WHERE surveyID = " + str(surveyID))
        csr.execute(sql)
        db.commit()
        questions = getAllQuestions(surveyID)
        for question in questions:
            sql = ("DELETE FROM Answer WHERE questionID  = " + str(question))
            csr.execute(sql)
            db.commit()
        sql = ("DELETE FROM Question WHERE surveyID  = " + str(surveyID))
        csr.execute(sql)
        db.commit()
        sql = ("DELETE FROM Survey WHERE surveyID = " + str(surveyID))
        csr.execute(sql)
        db.commit()
        return True
    return False


#Change target years
def changeTargetYears(questionID, oldTargetYears, newTargetYears):
    toAdd = []
    for tYear in newTargetYears:
        if tYear not in oldTargetYears:
            toAdd.append(tYear)
    global allClassesList
    classes=allClassesList
    for classID in classes:
        if int(getYear(classID=classID)) in newTargetYears:
            sql = ("INSERT INTO Answer (classID, questionID, complete) "
            "VALUES (" + str(classID) + ", " + str(questionID) +  ", " + str(0) + ")")
            csr.execute(sql)
            db.commit()


################################################# ID <-> NAME CONVERSIONS##################################

#Gets a survey ID from a name
def getSurveyID(name):
    """Gets surveyID"""
    sql = ("SELECT surveyID FROM Survey WHERE name = '" + name + "'")
    csr.execute(sql)
    ID = csr.fetchall()
    return ID[0][0]

#Gets a name from a surveyID
def getSurveyName(surveyID):
    """Gets survey name"""
    sql = ("SELECT name FROM Survey WHERE surveyID = " + str(surveyID))
    csr.execute(sql)
    ID = csr.fetchall()
    return ID[0][0]

#Gets the surveyID of the survey a question is in
def getContainingSurvey(questionID):
    """Gets the survey a question is in"""
    sql = ("SELECT surveyID FROM Question WHERE questionID = " + str(questionID))
    csr.execute(sql)
    return(csr.fetchall()[0][0])

#Returns the question of a questionID
def getQuestion(questionID):
    """Gets the questionID of a question"""
    sql = ("SELECT questionBody, questionType FROM Question WHERE questionID = " + str(questionID))
    csr.execute(sql)
    questionData = csr.fetchall()[0]
    if questionData[1] == QUESTIONTYPEOPTIONS:
        return optionQuestionParse(questionData[0])[0]
    else:
        return(questionData[0])

#Returns a list of all questions in a survey
def getQuestionDetails(surveyID):
    """Gets a map of questionID to question for all questions"""
    questions = {}
    sql = ("SELECT questionID, questionBody, questionType FROM Question WHERE surveyID = " + str(surveyID) + " ORDER BY questionNumber ASC")
    csr.execute(sql)
    questionData = csr.fetchall()
    for data in questionData:
        if data[ID_QUESTIONTYPE] == QUESTIONTYPEOPEN:
            questions[data[ID_QUESTIONID]] = data[ID_QUESTIONBODY]
        else:
            question, options = optionQuestionParse(data[ID_QUESTIONBODY])
            questions[data[ID_QUESTIONID]] = question
    return questions

#Gets all the data for a question #Question, Options, YesNo, Target Years, QuestionNumber
def getAllQuestionData(questionID):
    outData = {}
    sql = ("SELECT questionID, questionBody, questionType, questionNumber FROM Question WHERE questionID = " + str(questionID))
    csr.execute(sql)
    questionData = csr.fetchall()[0]
    if questionData[ID_QUESTIONTYPE] == QUESTIONTYPEOPEN:
        outData["Question"] = questionData[ID_QUESTIONBODY]
    else:
        outData["Question"], outData["Options"] = optionQuestionParse(questionData[ID_QUESTIONBODY])
    try:
        outData["YesNo"] = outData["Options"] == ["Yes", "No"]
    except:
        outData["YesNo"] = False
    outData["Target Years"] = getTargetYearsQuestion(questionID)
    outData["Question Number"] = questionData[3]
    outData["Question Type"] = questionData[ID_QUESTIONTYPE]
    return outData
 
#Gets a classname from classID
def getClassName(classID):
    """Gets a class name"""
    global classNameMap
    global firstTimeClassName
    if firstTimeClassName:
        sql = "SELECT username, ClassID FROM Class"
        csr.execute(sql)
        allClassNames =  csr.fetchall()
        for classDetails in allClassNames:
            classNameMap[classDetails[1]] = classDetails[0]
        firstTimeClassName = False
    return classNameMap[int(classID)]

#Gets classID from username
def getClassID(username, schoolYear = getCurrentSchoolYear()):
    """Gets a classID"""
    sql = ("SELECT classID FROM Class WHERE username = '" + username + "'" + "AND schoolYear = " + str(schoolYear))
    csr.execute(sql)
    return csr.fetchall()[0][0]

#Gets a year from a classname
def getYear(name = "Undefined", classID = 0000):
    """Gets the year a class is in"""
    if name == "Undefined":
        if classID == 0000:
            raise ValueError("Name and classID were both undefined")
        name = getClassName(classID)
    try:
        return int(name[0:2])
    except:
        return int(name[0:1])

##################################################  ANSWER-QUESTION COMPILING/PARSING FUNCTIONS ###########################################

#Compiles years to open question
def openAnswerCompile(answers):
    out = answers[0]
    for i in range(1, len(answers)):
        out += "¬" + answers[i]
    return out

#Parses years to an open question
def openAnswerParse(body):
    years = []
    previousLine = -1
    for i in range(len(body)):
        if body[i] == "¬":
            years.append(body[previousLine+1:i])
            previousLine = i
    years.append(body[previousLine+1:])
    return years

#Compiles years to option question
def optionAnswerCompile(answers):
    out =answers[0]
    for i in range(1, len(answers)):
        out += "¬" + answers[i]
    return out

#Parses years to option question
def optionAnswerParse(body):
    years = []
    previousLine = -1
    for i in range(len(body)):
        if body[i] == "¬":
            years.append(body[previousLine+1:i])
            previousLine = i
    years.append(body[previousLine+1:])
    return years

#Compiles the options and the question for an option question
def optionQuestionCompile(question, options):
    out = question
    for option in options:
        out += "¬" + option
    return out

#Parses the options and the question for an option question
def optionQuestionParse(body):
    question = ""
    options = []
    previousLine = 0
    questionFound = False
    for i in range(len(body)):
        if body[i] == "¬":
            if questionFound:
                options.append(body[previousLine+1:i])
            else:
                questionFound = True
                question = body[0:i]
            previousLine = i
    options.append(body[previousLine+1:])
    return question, options

#Compiles target years
def targetYearsCompile(years):
    out = str(years[0])
    for i in range(1, len(years)):
        out += "¬" + str(years[i])
    return out

#Parses targetYears
def targetYearsParse(body):
    years = []
    previousLine = -1
    for i in range(len(body)):
        if body[i] == "¬":
            years.append(int(body[previousLine+1:i]))
            previousLine = i
    years.append(int(body[previousLine+1:]))
    return years


##################################################### DUE DATE CHECKING FUNCTIONS ###############################################

#Gets the date a survey was set
def getSetDate(surveyID):
    """Get when the survey was set"""
    sql = ("SELECT setDate FROM Survey WHERE surveyID = " + str(surveyID))
    csr.execute(sql)
    return(csr.fetchall()[0][0])

#Gets the date a survey is due
def getDueDate(surveyID):
    """Get when the survey is due"""
    sql = ("SELECT dueDate FROM Survey WHERE surveyID = " + str(surveyID))
    csr.execute(sql)
    return(csr.fetchall()[0][0])

def setDueDate(surveyID, newDueDate):
    date = newDueDate.strftime('%Y-%m-%d')
    sql = ("UPDATE Survey SET dueDate = " + str(date) + " WHERE SurveyID = " + str(surveyID))
    csr.execute(sql)
    db.commit()

#Checks if a survey is overdue
def isOverdue(surveyID):
    """Get if the survey is overdue"""
    dueDate = str(getDueDate(surveyID))
    today = str(date.today().strftime('%Y-%m-%d'))
    if today[0:4] == dueDate[0:4]:
        if today[5:7] == dueDate[5:7]:
            if today[8:10] == dueDate[8:10]:
                return True
            elif int(today[8:10]) > int(dueDate[8:10]):
                return True
        elif int(today[5:7]) > int(dueDate[5:7]):
            return True
    elif int(today[0:4]) > int(dueDate[0:4]):
        return True
    return False


############################################## FULFILLING FUNCTIONS ###################################

#Sets a class survey to complete
def completeSurvey(surveyID, classID):
    sql = ("UPDATE ClassSurvey SET completed = 1"+
        " WHERE classID = " + str(classID) + " AND surveyID = " + str(surveyID))
    csr.execute(sql)
    db.commit()

#Submits and answer to a question Answer data is a list of responses - for options, the numbers must be in the right order
def submitAnswer(answerData , questionID, classID, questionType, offlineAnswer = False):
    """Submits the answer to a question"""
    surveyID = getContainingSurvey(questionID)
    if int(questionType) == QUESTIONTYPEOPTIONS:
        sql = ("SELECT people FROM Class WHERE classID = " + str(classID))
        csr.execute(sql)
        people = int(csr.fetchall()[0][0])
        totalPeopleSurveyed = 0
        if not offlineAnswer:
            for data in answerData:
                try:
                    totalPeopleSurveyed += int(data)
                except:
                    return False
            if people < totalPeopleSurveyed:
                return False
        body = optionAnswerCompile(answerData)
    elif int(questionType) == QUESTIONTYPEOPEN:
        body = openAnswerCompile(answerData)
    body = body.replace("\'", "\'\'")
    sql = ("UPDATE Answer SET answerType = " + str(questionType) + ", answerBody = '" + body + "', complete = " + str(1) +
        " WHERE classID = " + str(classID) + " AND questionID = " + str(questionID))
    csr.execute(sql)
    db.commit()
    if len(getQuestionsNotCompleted(surveyID, classID)) == 0:
        completeSurvey(surveyID, classID)
    return True

##################################################### CONDITIONAL QUESTION ID/SURVEY ID GETTING FUNTIONS ####################################

#Gets the question IDs of a survey
def getAllQuestions(surveyID):
    """Gets the questions in a survey"""
    sql = ("SELECT questionID FROM Question where surveyID = " + str(surveyID) + " ORDER BY questionNumber")
    csr.execute(sql)
    return [i[0] for i in csr.fetchall()]


#Gets the target years of a question
def getTargetYearsQuestion(questionID):
    """Gets the years taking the question"""
    sql = ("SELECT targetYears FROM Question WHERE questionID = " + str(questionID))
    csr.execute(sql)
    return targetYearsParse(csr.fetchall()[0][0])


#Gets the questionIDs for a specific class survey
def getClassQuestions(surveyID, classID):
    """Gets the questions for a class survey"""
    sql = ("SELECT Answer.questionID from Answer, Question WHERE Answer.classID = + " + str(classID) + 
    " AND Answer.questionID = Question.questionID AND Question.surveyID = " + str(surveyID))
    csr.execute(sql)
    return [i[0] for i in csr.fetchall()]

#Gets the questionIDs for the completed questions in a class survey
def getQuestionsCompleted(surveyID, classID):
    """Gets the questions completed in a class survey"""
    sql = ("SELECT Answer.questionID from Answer, Question WHERE Answer.classID = " + str(classID) + 
    " AND Answer.questionID = Question.questionID AND Answer.complete = 1 AND Question.surveyID = " + str(surveyID))
    csr.execute(sql)
    return [i[0] for i in csr.fetchall()]

#Gets the questionIDs for the questions not completed in a class survey
def getQuestionsNotCompleted(surveyID, classID):
    """Get the questions not completed in a class survey"""
    sql = ("SELECT Question.questionID, Question.questionBody, Question.questionType from Answer, Question WHERE Answer.classID = " + str(classID) + 
    " AND Answer.questionID = Question.questionID AND Answer.complete = 0 AND Question.surveyID = " + str(surveyID))
    csr.execute(sql)
    return [i for i in csr.fetchall()]

#Returns a list of all class surveys
def loadAllClassSurveys(classID):
    """Gets all class surveys"""
    sql = ("SELECT surveyID FROM ClassSurvey WHERE classID = " + str(classID))
    csr.execute(sql)
    return [i[0] for i in csr.fetchall()]

#Returns a list of all surveys
def loadAllSurveys():
    """Gets all surveys"""
    sql = ("SELECT surveyID FROM Survey")
    csr.execute(sql)
    return [i[0] for i in csr.fetchall()]

#Returns a list of incomplete surveys
def loadCurrentSurveys(classID):
    """Gets incomplete surveys"""
    sql = ("SELECT surveyID FROM ClassSurvey WHERE classID = " + str(classID) + " AND completed = " + str(0))
    csr.execute(sql)
    return [i[0] for i in csr.fetchall()]

#Gets the total number of questions in a survey
def getTotalNumberOfQuestions(surveyID):
    """Gets total number of questions in a survey"""
    sql = ("SELECT numberOfQuestions FROM Survey WHERE surveyID = " + str(surveyID))
    csr.execute(sql)
    return(csr.fetchall()[0][0])

#Gets a list of all the classes taking a survey
def getClassesTaking(surveyID):
    """Gets the classes taking the survey"""
    sql = ("SELECT classID FROM ClassSurvey WHERE surveyID = " + str(surveyID))
    csr.execute(sql)
    return [i[0] for i in csr.fetchall()]

#Gets a list of the targetYears taking a survey
def getTargetYears(surveyID):
    """Get the years taking the survey"""
    sql = ("SELECT targetYears FROM Survey WHERE SurveyID = " + str(surveyID))
    csr.execute(sql)
    return targetYearsParse(csr.fetchall()[0][0])

#Get details of a survey
def getSurveyDetails(surveyID):
    """Gets details of a survey"""
    returnArr = []
    sql = ("SELECT name, setDate, dueDate FROM Survey WHERE surveyID = " + str(surveyID))
    csr.execute(sql)
    out = csr.fetchall()[0]
    returnArr.append(out[0])
    returnArr.append(", ".join([str(i) for i in getTargetYears(surveyID)]))
    returnArr.append(out[1])
    returnArr.append(out[2])
    return returnArr

############################################################  COMPLETENESS CHECKS  ##################################################

#Checks if a survey has been completed by all classes and returns classIDs of which classes haven't
def isComplete(surveyID):
    """Gets if a survey is completed"""
    sql = ("SELECT classID FROM ClassSurvey WHERE surveyID = " + str(surveyID) + " AND completed = 0")
    csr.execute(sql)
    incompleteClasses = [i[0] for i in csr.fetchall()]
    if len(incompleteClasses) == 0:
        return True, []
    else:
        return False, incompleteClasses

#Returns the percentage of a survey a class has completed
def percentageComplete(surveyID, classID):
    """Gets the percentage completedness of a class survey"""
    totalQuestions = len(getClassQuestions(surveyID, classID))
    completed = len(getQuestionsCompleted(surveyID, classID))
    return round((completed/totalQuestions) *100)

#Gets the percetage completeness of a survey
def percentageSurveyComplete(surveyID):
    """Get percentage completeness of a survey"""
    complete, number = isComplete(surveyID)
    if complete:
        return 100
    else:
        total = len(getClassesTaking(surveyID))
        return ((total - len(number)) / total) * 100

###################################################### LIST DISPLAY GETTING FUNCTIONS #######################################

def getCurrentSurveysSplit(classID):
    todo = []
    missing = []
    surveys = loadCurrentSurveys(classID)
    for survey in surveys:
        if isOverdue(survey):
            missing.append(survey)
        else:
            todo.append(survey)
    return todo, missing

####################################################################################################################################
################################################# ExcelWriter Object ###############################################################
####################################################################################################################################

#Saves survey as excel
def saveAsExcel(surveyID):
    """Save a survey as excel"""
    try:
        ew = ExcelWriter(surveyID)
        ew.write()
        ctypes.windll.user32.MessageBoxW(0, "File exported successfully!", "Success", 0)
        return True
    except:
        ctypes.windll.user32.MessageBoxW(0, "File didn't export", "Failed", 0)
        return False

class ExcelWriter:
    #Pass in the surveyID to write
    def __init__(self, surveyID):
        self.surveyID = surveyID

    #Writes the survey to the workbook
    def write(self):
        sql = ("SELECT name FROM Survey WHERE surveyID = " + str(self.surveyID))
        csr.execute(sql)
        surveys = csr.fetchall()[0][0]
        savePath = save(surveys)
        try:
            os.remove(savePath)
        except:
            pass
        workbook = xlsxwriter.Workbook(savePath)
        sql = ("SELECT questionID, questionType, questionBody FROM Question WHERE surveyID = " + str(self.surveyID))
        csr.execute(sql)
        questions = csr.fetchall()
        self.cell_formatTITLE = workbook.add_format({'bold': True, 'underline':True}) 
        self.cell_format = workbook.add_format()
        self.cell_formatBIGGER = workbook.add_format({'bg_color' : 'red'})
        self.cell_formatYEAR = workbook.add_format({'bold': True})
        self.cell_formatYEARBIGGER = workbook.add_format({'bold': True, 'bg_color' : 'red'})
        self.normalStyles = {True: self.cell_formatBIGGER, False:self.cell_format}
        self.yearStyles = {True: self.cell_formatYEARBIGGER, False:self.cell_formatYEAR}
        for questionData in questions:
            if questionData[1] == QUESTIONTYPEOPTIONS:
                self.writeAnswersOptions(workbook, questionData)
            elif questionData[1] == QUESTIONTYPEOPEN:
                self.writeAnswersOpen(workbook, questionData)
        workbook.close()
            
    #Writes open question answer to sheet
    def writeAnswersOpen(self, workbook, questionData):
        if len(questionData[2]) < 28:
            worksheet = workbook.add_worksheet(questionData[2])
        else:
            worksheet = workbook.add_worksheet(questionData[2][0:25] + "...")
        
        worksheet.write(0, 0, questionData[2], self.cell_formatTITLE)
        sql = ("SELECT classID, answerBody FROM Answer WHERE questionID = " + str(questionData[0]) + " AND complete = " + str(1) +
        " ORDER BY classID ASC")
        csr.execute(sql)
        years = csr.fetchall()
        fullAnswers = {}
        for answer in years:
            sql = ("SELECT username, schoolYear FROM Class WHERE classID = " + str(answer[0]) + " AND people > 0" +
            " ORDER BY classID ASC")
            csr.execute(sql)
            result = csr.fetchall()[0]
            className = result[0]
            schoolYear = result[1]
            if int(schoolYear) == int(getSchoolYear(self.surveyID)):
                classAnswers = openAnswerParse(answer[1])
                fullAnswers[className] = classAnswers
        
        classesByYear = {year : [] for year in range(7,14)}
        for classname in fullAnswers.keys():
            year = getYear(classname)
            classesByYear[year].append(classname)
        
        for i in range(7, 14):
            if len(classesByYear[i]) == 0:
                classesByYear.pop(i)

        STARTROW = 3
        currentRow = 0
        for year in classesByYear.keys():
            worksheet.write(currentRow + STARTROW, 0, "Year " + str(year), self.cell_formatTITLE)
            currentRow += 3
            for classname in classesByYear[year]:
                worksheet.write(currentRow + STARTROW, 0, classname, self.cell_format)
                for answer in fullAnswers[classname]:
                    worksheet.write(currentRow + STARTROW, 1, answer, self.cell_format)
                    currentRow+=1
                currentRow +=1
                
    #Writes options question answer to sheet
    def writeAnswersOptions(self, workbook, questionData):
        question, columnTitles = optionQuestionParse(questionData[2])
        if len(question) < 28:
            worksheet = workbook.add_worksheet(question)
        else:
            worksheet = workbook.add_worksheet(question[0:25] + "...")
        
        worksheet.write(0, 0, question, self.cell_formatTITLE)
        sql = ("SELECT classID, answerBody FROM Answer WHERE questionID = " + str(questionData[0]) + " AND complete = " + str(1) +
        " ORDER BY classID ASC")
        csr.execute(sql)
        years = csr.fetchall()
        fullAnswers = {}
        fullPeople = {}
        for answer in years:
            sql = ("SELECT username, people, schoolYear FROM Class WHERE classID = " + str(answer[0]) + " AND people > 0" +
            " ORDER BY classID ASC")
            csr.execute(sql)
            result = csr.fetchall()[0]
            className = result[0]
            people = result[1]
            schoolYear = result[2]
            if int(schoolYear) == int(getSchoolYear(self.surveyID)):
                classAnswers = optionAnswerParse(answer[1])
                answerDictionary = {}
                for i in range(len(columnTitles)):
                    answerDictionary[columnTitles[i]] = int(classAnswers[i])
                fullPeople[className] = int(people)
                fullAnswers[className] = answerDictionary
        
        classesByYear = {year : [] for year in range(7,14)}
        for classname in fullAnswers.keys():
            year = getYear(classname)
            classesByYear[year].append(classname)
        for i in range(7, 14):
            if len(classesByYear[i]) == 0:
                classesByYear.pop(i)
        STARTROW = 3
        currentRow = 0
        schoolTotals = {columnTitle : 0 for columnTitle in columnTitles}
        schoolTotalPeople = 0
        worksheet.write(currentRow + STARTROW, 0, "Year", self.cell_formatTITLE)
        worksheet.write(currentRow + STARTROW, 1, "Class", self.cell_formatTITLE)
        for i in range(len(columnTitles)):
            worksheet.write(currentRow + STARTROW, i+2, columnTitles[i], self.cell_formatTITLE)
            worksheet.write(currentRow + STARTROW, i+len(columnTitles) + 2, columnTitles[i] + " %", self.cell_formatTITLE)
        currentRow += 1
        for year in classesByYear.keys():
            tempRow = currentRow
            currentRow +=1
            yearTotals = {columnTitle : 0 for columnTitle in columnTitles}    
            yearTotalPeople = 0
            for classname in classesByYear[year]:
                worksheet.write(currentRow + STARTROW, 1, classname, self.cell_format)
                biggestStyle = self.cell_formatBIGGER
                otherStyle = self.cell_format
                biggest = getBiggestKey(fullAnswers[classname])
                for i in range(len(columnTitles)):
                    if columnTitles[i] == biggest or biggest == TWOSAME:
                        worksheet.write(currentRow + STARTROW, i+2, fullAnswers[classname][columnTitles[i]], biggestStyle)
                        worksheet.write(currentRow + STARTROW, i+2 + len(columnTitles), round(fullAnswers[classname][columnTitles[i]]/fullPeople[classname]* 100), biggestStyle)
                    else:
                        worksheet.write(currentRow + STARTROW, i+2, fullAnswers[classname][columnTitles[i]], otherStyle)
                        worksheet.write(currentRow + STARTROW, i+2 + len(columnTitles), round(fullAnswers[classname][columnTitles[i]]/fullPeople[classname] * 100), otherStyle)
                    yearTotals[columnTitles[i]] += fullAnswers[classname][columnTitles[i]]
                yearTotalPeople += fullPeople[classname]
                currentRow+=1
            biggestStyle = self.cell_formatYEARBIGGER
            otherStyle = self.cell_formatYEAR
            biggest = getBiggestKey(yearTotals)
            worksheet.write(tempRow + STARTROW, 0,"Year " + str(year), self.cell_formatYEAR)
            worksheet.write(tempRow + STARTROW, 1, "Total ", self.cell_formatYEAR)
            for i in range(len(columnTitles)):
                if columnTitles[i] == biggest or biggest == TWOSAME:
                    worksheet.write(tempRow + STARTROW, i+2, yearTotals[columnTitles[i]], biggestStyle)
                    worksheet.write(tempRow + STARTROW, i+2 + len(columnTitles), round(yearTotals[columnTitles[i]]/yearTotalPeople * 100), biggestStyle)
                else:
                    worksheet.write(tempRow + STARTROW, i+2, yearTotals[columnTitles[i]], otherStyle)
                    worksheet.write(tempRow + STARTROW, i+2 + len(columnTitles), round(yearTotals[columnTitles[i]]/yearTotalPeople * 100), otherStyle)
                schoolTotals[columnTitles[i]] += yearTotals[columnTitles[i]]
            schoolTotalPeople += yearTotalPeople
        biggestStyle = self.cell_formatYEARBIGGER
        otherStyle = self.cell_formatYEAR
        worksheet.write(currentRow + STARTROW, 0, "Total", self.cell_formatYEAR)
        biggest = getBiggestKey(schoolTotals)
        for i in range(len(columnTitles)):
            if columnTitles[i] == biggest or biggest == TWOSAME:
                worksheet.write(currentRow + STARTROW, i+2, schoolTotals[columnTitles[i]], biggestStyle)
                worksheet.write(currentRow + STARTROW, i+2 + len(columnTitles), round(schoolTotals[columnTitles[i]]/schoolTotalPeople * 100), biggestStyle)
            else:
                worksheet.write(currentRow + STARTROW, i+2, schoolTotals[columnTitles[i]], otherStyle)
                worksheet.write(currentRow + STARTROW, i+2 + len(columnTitles), round(schoolTotals[columnTitles[i]]/schoolTotalPeople * 100), otherStyle)

####################Survey file handling

###########Offline surveys

#Uploads a complete survey file to the server
def importAndUpload():
    folder = tk.filedialog.askdirectory()
    os.chdir(folder)
    for filename in glob.glob("*.evs"):
        with open(filename, 'rb') as file:
            s = pickle.load(file)
        s.setInformation()

#Exports a survey to a file
def exportSurvey(surveyID):
    surveyName = getSurveyName(surveyID)
    fname = save(surveyName, defaultextension=".evs", filetypes = [("Survey File", ".evs")])
    s = Survey(surveyID, surveyName, getAllQuestions(surveyID))
    s.getInformation()
    with open(fname, 'wb') as file:
        pickle.dump(s, file)

#Saves the completed survey to a file
def saveSurvey(survey):
    fname = save(survey.name + " " + offlineclass, defaultextension=".evs", filetypes = [("Survey File", ".evs")])
    with open(fname, 'wb') as file:
        pickle.dump(survey, file)









#Changes the program version in the DB
def changeVersion(newVersion):
    sql = ("UPDATE Admin SET paramValue = " + str(newVersion) + " WHERE paramName = 'version'")
    csr.execute(sql)
    db.commit()


############################################################################################################################
############################################################################################################################
############################################################################################################################
############################################################ MAIN PROGRAM ##################################################
############################################################################################################################
############################################################################################################################
############################################################################################################################


#Connect db and assign a connection object and a cursor - comment out depending on db infrastructure:
if SERVERARCHITECTURE == MYSQL:
    db, csr = connectMySQLDatabase()
elif SERVERARCHITECTURE == MICROSOFTSQL:
    db, csr = connectMicrosoftSQLDatabase()
else:
    raise "Invalid server architecture settings"

#Check if connection was successful
if db == "False":

    #If not, display the offline message
    offline = True
    ctypes.windll.user32.MessageBoxW(0, "You are offline, you can still answer surveys, but you will need to download and upload surveys manually", "Offline", 0)

#Start the UI
start()

#Try to close the DB handles
try:
    db.close()
except:
    pass
try:
    csr.close()
except:
    pass