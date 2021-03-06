# Importing the requiered libraries
import re
import os
import ssl
import time
import string
import random
import hashlib
import mariadb
import smtplib
import tkinter as tk
from tkinter import *
from mysqlx import Row
from tkinter import ttk
from datetime import datetime
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader

# Retreaving the database ip, username and password from the env file
load_dotenv()
dbIp = os.getenv("dbIp")
dbUserName = os.getenv('dbUserName')
dbPassword = os.getenv('dbPassword')

# Connecting to the database
cur = mariadb.connect(host=dbIp, database='iSpy', user=dbUserName, password=dbPassword)
conn = cur.cursor()


def closeWindow(currentWindow):
    currentWindow.destroy()


def popUpWindow(title, message, window):
    popUp = tk.Toplevel(window)
    popUp.geometry('250x100')
    currentWindow = popUp
    popUp.title(title)
    label = Label(popUp, text=message, font=normfont)
    label.pack(side="top", fill="x", pady=10)
    button = Button(popUp, text="Okay", command=lambda: [closeWindow(currentWindow)])
    button.pack()
    popUp.mainloop()


def accountValidation(acUserName, acFirstName, acLastName, acEmail, acAdminPrivileges, accountCreationWindow, window):
    # Retreaving the information from the users inputs for validation
    userName = acUserName.get()
    firstName = acFirstName.get()
    lastName = acLastName.get()
    email = acEmail.get()
    adminPrivileges = acAdminPrivileges.get()
    title = "Account Creation Error"

    # Regex for email validation
    emailCheck = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    now = datetime.now()  # Gets the current date and time
    timeCreated = now
    logInTimeForDB = now

    # Searches the database for all instances of the given username
    cursor = conn.execute("SELECT * FROM appUsers Where userName = ?", (userName,))
    cursor = conn.fetchall()

    if 0 in (len(userName), len(firstName), len(lastName), len(email)):
        message = 'Some fields are blank \n Please fill all of them in'
        popUpWindow(title, message, window)

    if len(cursor) == 1:  # Checks that the username is not taken
        message = 'Username is already taken, please try a different one'
        popUpWindow(title, message, window)

    if not re.fullmatch(emailCheck, email):  # Checks against the regex that the email is valid
        message = 'Email not valid, please try again'
        popUpWindow(title, message, window)

    # Making the first letter of the first and last name caplital
    firstName = firstName.capitalize()
    lastName = lastName.capitalize()

    # Making the characters of the email lowercase
    email = email.lower()

    # Generating a random password
    passwordToSend = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))

    # Encrypting the password
    password = passwordToSend.encode()
    password = hashlib.sha3_512(password).hexdigest()

    # Create a template Environment
    env = Environment(loader=FileSystemLoader('templates'))

    # Load the template from the Environment
    template = env.get_template('accountCreationTemplate.html')

    # Render the template with variables
    html = template.render(
        firstname=firstName,
        username=userName,
        password=passwordToSend,)

    # Write the template to an HTML file
    with open('email.html', 'w') as f:
        f.write(html)

    with open('email.html', 'r') as f:
        html = f.read()

    load_dotenv()
    gmail_user = os.getenv('emailAccount')
    gmail_password = os.getenv('emailPassword')

    # Create a MIMEMultipart class, and set up the From, To, Subject fields
    email_message = MIMEMultipart()
    email_message['From'] = gmail_user
    email_message['To'] = email
    email_message['Subject'] = 'Account created on iSpy'

    # Attach the html doc defined earlier, as a MIMEText html content type to the MIME message
    email_message.attach(MIMEText(html, "html"))
    # Convert it as a string
    email_string = email_message.as_string()

    # Connect to the Gmail SMTP server and Send Email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, email, email_string)
    os.remove("email.html")

    conn.execute("INSERT INTO appUsers(userName, hashedPassword, firstName, lastName, email, adminPrivlages, timeCreated, lastLogIn) VALUES (?,?,?,?,?,?,?,?)", (
                 userName, password, firstName, lastName, email, adminPrivileges, timeCreated, logInTimeForDB))  # Writes the information to the db
    cur.commit()
    accountCreationWindow.destroy()
    title = "Alert!"
    message = "User created successfully"
    popUpWindow(title, message, window)


def createAccount(window):
    accountCreationWindow = tk.Toplevel(window)
    accountCreationWindow.geometry('390x350')
    accountCreationWindow.title('Create account')
    currentWindow = accountCreationWindow

    spacer1 = Label(accountCreationWindow, text="").grid(row=0, column=0)

    acUserName = StringVar()
    userNameLabel = Label(accountCreationWindow, text="User Name", pady=10, width=22, anchor='w').grid(row=1, column=1)
    userNameEntry = Entry(accountCreationWindow, textvariable=acUserName, width=30).grid(row=1, column=2)

    acFirstName = StringVar()
    firstNameLabel = Label(accountCreationWindow, text="First name", pady=10, width=22, anchor='w').grid(row=2, column=1)
    firstNameEntry = Entry(accountCreationWindow, textvariable=acFirstName, width=30).grid(row=2, column=2)

    acLastName = StringVar()
    lastNameLable = Label(accountCreationWindow, text="Last name", pady=10, width=22, anchor='w').grid(row=3, column=1)
    lastNameEntry = Entry(accountCreationWindow, textvariable=acLastName, width=30).grid(row=3, column=2)

    acEmail = StringVar()
    emailLable = Label(accountCreationWindow, text="Email", pady=10, width=22, anchor='w').grid(row=4, column=1)
    emailEntry = Entry(accountCreationWindow, textvariable=acEmail, width=30).grid(row=4, column=2)

    acAdminPrivileges = IntVar()
    adminLable = Label(accountCreationWindow, text="Admin priveleges", pady=10, width=22, anchor='w').grid(row=5, column=1)
    Checkbutton(accountCreationWindow, text="                                                       ", variable=acAdminPrivileges).grid(row=5, column=2)

    spacer2 = Label(accountCreationWindow, text="").grid(row=6, column=1)
    loginButton = Button(accountCreationWindow, text="           Create account           ", command=lambda: [accountValidation(
        acUserName, acFirstName, acLastName, acEmail, acAdminPrivileges, accountCreationWindow, window)]).grid(row=7, column=2)
    spacer3 = Label(accountCreationWindow, text=" ").grid(row=8, column=2)
    exitButton = Button(accountCreationWindow, text="             Exit            ", command=lambda: [closeWindow(currentWindow)]).grid(row=9, column=2)
    accountCreationWindow.mainloop()


def sendEmail(subject, message, currentWindow, emailApp):
    print("Sending Email...")
    # Create a template Environment
    env = Environment(loader=FileSystemLoader('templates'))

    # Load the template from the Environment
    template = env.get_template('announcementTemplate.html')

    # Render the template with variables
    html = template.render(
        textInput=message,
        usersName=user,)

    # Write the template to an HTML file
    with open('email.html', 'w') as f:
        f.write(html)

    with open('email.html', 'r') as f:
        html = f.read()

    load_dotenv()
    gmail_user = os.getenv('emailAccount')
    gmail_password = os.getenv('emailPassword')

    emails = conn.execute("SELECT email FROM appUsers")
    emails = conn.fetchall()
    recipients = []
    for email in emails:
        recipients.append(email[0])

    # Create a MIMEMultipart class, and set up the From, To, Subject fields
    email_message = MIMEMultipart()
    email_message['From'] = gmail_user
    email_message['To'] = ", ".join(recipients)
    email_message['Subject'] = subject

    # Attach the html doc defined earlier, as a MIMEText html content type to the MIME message
    email_message.attach(MIMEText(html, "html"))
    # Convert it as a string
    email_string = email_message.as_string()

    # Connect to the Gmail SMTP server and Send Email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, email, email_string)
    os.remove("email.html")
    emailApp.destroy()
    currentWindow.destroy()


def emailConfirm(window, emailApp, subject, message):
    print("Sending Email...")
    subject = subject.get()
    message = message.get("1.0", END)
    confirmWindow = tk.Toplevel(window)
    confirmWindow.geometry('275x175')
    currentWindow = confirmWindow
    confirmWindow.title("Confirm Email")
    label = Label(confirmWindow, text="Do you want to send the email?", font=normfont).pack(side="top", fill="x", pady=10)
    button = Button(confirmWindow, text=" Yes ", command=lambda: [sendEmail(subject, message, currentWindow, emailApp)], pady=10, padx=9.5).pack(side="top")
    button = Button(confirmWindow, text=" No ", command=lambda: [closeWindow(currentWindow)], pady=10, padx=10.5).pack(side="top")
    confirmWindow.mainloop()


def appEmail(window):
    emailApp = Toplevel(window)
    emailApp.geometry("1050x720")
    emailApp.title("In-App Email")
    Label(emailApp, text="Email users", font=largefont, padx=10, pady=10).pack()
    Label(emailApp, text="Subject:", font=largefont).pack(padx=10, pady=10, anchor=NW)
    subject = StringVar()
    subjectEntry = Entry(emailApp, textvariable=subject, width=160, font=largefont).pack(padx=10, pady=10, anchor=NW)
    Label(emailApp, text="Message:", font=largefont).pack(padx=10, pady=10, anchor=NW)
    message = tk.Text(emailApp, height=22.5, width=160, font=largefont)
    scroll = tk.Scrollbar(emailApp)
    message.configure(yscrollcommand=scroll.set)
    message.pack(padx=10, pady=10, anchor=NW)
    scroll.config(command=message.yview)
    Button(emailApp, text="Send", font=largefont, width=10, command=lambda: emailConfirm(window, emailApp, subject, message)).pack(padx=10, pady=10)
    Button(emailApp, text="Exit", font=largefont, width=10, command=lambda: emailApp.destroy()).pack(padx=10, pady=10)
    emailApp.mainloop()


def showSelected(tree, entryLogList):
    # Retriving the row id of the event
    rowId = tree.selection()
    if len(rowId) == 0:
        return
    rowId = str(rowId[0])
    rowId = int(rowId.strip("I"))
    videoId = str(entryLogList[rowId-1][0])
    # Getting path to the file as will differ per computer
    path = os.getcwd()
    # Add the requiered video to the end of the path
    path = (path + "\\Recordings\\" + videoId + ".h264")
    # Start the video file in computers player
    os.startfile(path)
    # Add timeout to allow the file to open
    time.sleep(2)


def viewLogs(window):
    # Creating the windiow for the event display
    viewWindow = tk.Toplevel(window)
    viewWindow.geometry("1020x720")
    viewWindow.title("Event Logs")

    currentWindow = viewWindow

    Label(viewWindow, text="Event Log", font=largefont, padx=10, pady=10).pack()

    # Creating frame layer fo the tkinter tree view window
    frame = Frame(viewWindow)
    frame.pack(pady=20)

    # Fixing headings to the top of the table
    tree = ttk.Treeview(frame, columns=(1, 2, 3, 4, 5), show='headings', height=25)
    tree.pack(side=LEFT)

    # Adding the scroll bar for events
    sb = Scrollbar(frame, orient=VERTICAL)
    sb.pack(side=RIGHT, fill=Y)

    # Attatching the scrollbar to the side fo the table
    tree.config(yscrollcommand=sb.set)
    sb.config(command=tree.yview)

    # Creating headings for the table
    tree["columns"] = ("1", "2", "3", "4", "5")
    tree['show'] = 'headings'
    tree.column("1", width=100, anchor='c')
    tree.column("2", width=100, anchor='c')
    tree.heading("1", text="Event Id")
    tree.heading("2", text="Result")
    tree.heading("3", text="First Name")
    tree.heading("4", text="Last Name")
    tree.heading("5", text="Date Time")

    # Retriving information from the database
    entryLog = conn.execute("SELECT * FROM entryLog")
    entryLog = conn.fetchall()
    entryLog.reverse()
    entryLogList = []

    # Populating the table with events, with most recent events at the top
    loopNum = 0
    for event in entryLog:
        eventId = event[0]
        entry = event[1]
        if entry == 1:
            entry = "Entry"
            userId = event[2]
            userDetails = conn.execute("SELECT firstName, lastName FROM idCards WHERE id = ?", (userId,))
            userDetails = conn.fetchall()
            firstName = userDetails[0][0]
            lastName = userDetails[0][1]
        else:
            userId = None
            entry = "No entry"
            firstName = None
            lastName = None
        dateTime = event[3]
        logInfo = [eventId, entry, userId, firstName, lastName, dateTime]
        entryLogList.append(logInfo)
        loopNum += 1
        pos = ("L", (loopNum))
        tree.insert("", "end", text=pos, values=(eventId, entry, firstName, lastName, dateTime))

    style = ttk.Style()
    style.theme_use("default")
    style.map("Treeview")

    # Creating button to view video and exit when done
    Button(viewWindow, text="Display event video", command=lambda: [showSelected(tree, entryLogList)], pady=10, padx=10).pack()
    Label(viewWindow, text=" ").pack()
    Button(viewWindow, text="              Exit              ", command=lambda: [closeWindow(currentWindow)], pady=10, padx=10).pack()

    viewWindow.mainloop()


def unlock(lockWindow, window):
    conn.execute("Update doorStatus set lockStatus = 1")
    cur.commit()
    title = "Alert!"
    message = "Door unlocked for 30 seconds"
    popUpWindow(title, message, window)
    time.sleep(10)
    lockWindow.destroy()


def unlockWindow(window):
    # Creating lock window
    lockWindow = tk.Toplevel(window)
    currentWindow = lockWindow
    # Sizeing the window
    lockWindow.geometry('150x160')
    lockWindow.title('Door lock')
    spacer1 = Label(lockWindow, text="", font=("Arial Bold", 50))
    spacer2 = Label(lockWindow, text="             ").grid(column=0, row=0)
    # Creating unlock button
    unlockButton = Button(lockWindow, text="\n  Unlock  \n", command=lambda: [unlock(lockWindow, window)]).grid(row=1, column=1)
    # Creating exit button
    exitButton = Button(lockWindow, text="\n     Exit     \n", command=lambda: [closeWindow(currentWindow)]).grid(row=3, column=1)
    spacer4 = Label(lockWindow, text="\n").grid(row=4, column=1)
    lockWindow.mainloop()


def delete(userName, currentWindow, window, tree, row):
    conn.execute("DELETE FROM appUsers WHERE userName = ?", (userName,))
    cur.commit()
    if user == userName:
        exit()
    else:
        tree.delete(row)
        closeWindow(currentWindow)
        popUpWindow("Account deleted", "Account has been deleted", window)


def deleteAccountConformation(title, message, window, userName, tree, row):
    confirmWindow = tk.Toplevel(window)
    confirmWindow.geometry('275x175')
    currentWindow = confirmWindow
    confirmWindow.title(title)
    label = Label(confirmWindow, text=message, font=normfont).pack(side="top", fill="x", pady=10)
    button = Button(confirmWindow, text=" Yes ", command=lambda: [delete(userName, currentWindow, window, tree, row)], pady=10, padx=9.5).pack(side="top")
    button = Button(confirmWindow, text=" No ", command=lambda: [closeWindow(currentWindow)], pady=10, padx=10.5).pack(side="top")
    confirmWindow.mainloop()


def deleteAccount(tree, userList, viewWindow, window):
    row = tree.selection()
    if len(row) == 0:
        return
    rowId = str(row[0])
    rowId = int(rowId.strip("I"))
    rowId = rowId - 1
    if rowId == 0:
        message = "Can not delete the admin account"
        title = "Alert!"
        popUpWindow(title, message, window)
        return
    userName = userList[rowId][0]
    if userName == user:
        message = ("You are about to delete " + userName + "\n As this is your account you will be logged out \n Please confirm account deleation")
        title = "Confirm account deletion"
        deleteAccountConformation(title, message, window, userName, tree, row)
    else:
        message = ("You are about to delete " + userName + "\n Please confirm account deleation")
        title = "Confirm account deletion"
        deleteAccountConformation(title, message, window, userName, tree, row)


def manageUsers(window):
    # Creating the windiow for the event display
    viewWindow = tk.Toplevel(window)
    viewWindow.geometry("1050x720")
    viewWindow.title("Manage app users")

    currentWindow = viewWindow

    Label(viewWindow, text="Manage app users", font=largefont, padx=10, pady=10).pack()

    # Creating frame layer fo the tkinter tree view window
    frame = Frame(viewWindow)
    frame.pack(pady=20)

    # Fixing headings to the top of the table
    tree = ttk.Treeview(frame, columns=(1, 2, 3, 4, 5), show='headings', height=25)
    tree.pack(side=LEFT)

    # Adding the scroll bar for events
    sb = Scrollbar(frame, orient=VERTICAL)
    sb.pack(side=RIGHT, fill=Y)

    # Attatching the scrollbar to the side fo the table
    tree.config(yscrollcommand=sb.set)
    sb.config(command=tree.yview)

    # Creating headings for the table
    tree["columns"] = ("1", "2", "3", "4", "5")
    tree['show'] = 'headings'
    tree.heading("1", text="Username")
    tree.heading("2", text="First name")
    tree.heading("3", text="Last Name")
    tree.heading("4", text="Email")
    tree.heading("5", text="Admin privlages")

    # Retriving information from the database
    entryLog = conn.execute("SELECT * FROM appUsers")
    entryLog = conn.fetchall()
    userList = []

    # Populating the table with events, with most recent events at the top
    loopNum = 0
    for event in entryLog:
        userName = event[0]
        firstName = event[2]
        lastName = event[3]
        email = event[4]
        adminPrivlages = event[5]
        if adminPrivlages == 1:
            adminPrivlages = "Yes"
        else:
            adminPrivlages = "No"
        logInfo = [userName, firstName, lastName, email, adminPrivlages]
        userList.append(logInfo)
        loopNum += 1
        pos = ("L", (loopNum))
        tree.insert("", "end", text=pos, values=(userName, firstName, lastName, email, adminPrivlages))

    style = ttk.Style(viewWindow)
    style.theme_use("default")
    style.map("Treeview")
    # Creating button to view video and exit when done
    Button(viewWindow, text="          Delete user        ", command=lambda: [deleteAccount(tree, userList, viewWindow, window)], pady=10, padx=10).pack()
    Label(viewWindow, text=" ").pack()
    Button(viewWindow, text="              Exit              ", command=lambda: [closeWindow(currentWindow)], pady=10, padx=10).pack()
    viewWindow.mainloop()


def changeStatus(tree, cardList, viewWindow):
    row = tree.focus()
    if len(row) == 0:
        return
    rowId = int(row.strip("I"))
    rowId = rowId - 1
    cardName = cardList[rowId][0]
    status = cardList[rowId][3]
    if status == 'Active':
        conn.execute("UPDATE idCards SET active = 0 WHERE cardName = ?", (cardName,))
        cur.commit()
        tree.set(row, column=4, value='Deactivated')

    else:
        conn.execute("UPDATE idCards SET active = 1 WHERE cardName = ?", (cardName,))
        cur.commit()
        tree.set(row, column=4, value='Active')

    popUpWindow("Success", "Card status has been updated", viewWindow)


def manageCard(window):
    # Creating the windiow for the event display
    viewWindow = tk.Toplevel(window)
    viewWindow.geometry("1050x720")
    viewWindow.title("Manage card holders")

    currentWindow = viewWindow

    Label(viewWindow, text="Manage cards", font=largefont, padx=10, pady=10).pack()

    # Creating frame layer fo the tkinter tree view window
    frame = Frame(viewWindow)
    frame.pack(pady=20)

    # Fixing headings to the top of the table
    tree = ttk.Treeview(frame, columns=(1, 2, 3, 4), show='headings', height=25)
    tree.pack(side=LEFT)

    # Adding the scroll bar for events
    sb = Scrollbar(frame, orient=VERTICAL)
    sb.pack(side=RIGHT, fill=Y)

    # Attatching the scrollbar to the side fo the table
    tree.config(yscrollcommand=sb.set)
    sb.config(command=tree.yview)

    # Creating headings for the table
    tree["columns"] = ("1", "2", "3", "4")
    tree['show'] = 'headings'
    tree.heading("1", text="Card name")
    tree.heading("2", text="First name")
    tree.heading("3", text="Last name")
    tree.heading("4", text="Status")

    # Retriving information from the database
    cardHolder = conn.execute("SELECT * FROM idCards")
    cardHolder = conn.fetchall()
    cardList = []

    # Populating the table with events, with most recent events at the top
    loopNum = 0
    for event in cardHolder:
        cardName = event[2]
        firstName = event[3]
        lastName = event[4]
        status = event[5]
        if status == 1:
            status = "Active"
        else:
            status = "Deactivated"
        cardInfo = [cardName, firstName, lastName, status]
        cardList.append(cardInfo)
        loopNum += 1
        pos = ("L", (loopNum))
        tree.insert("", "end", text=pos, values=(cardName, firstName, lastName, status))

    style = ttk.Style(viewWindow)
    style.theme_use("default")
    style.map("Treeview")
    # Creating button to view video and exit when done
    Button(viewWindow, text="Enable / Dissable user", command=lambda: [changeStatus(tree, cardList, viewWindow)], pady=10, padx=10).pack()
    Label(viewWindow, text=" ").pack()
    Button(viewWindow, text="              Exit              ", command=lambda: [closeWindow(currentWindow)], pady=10, padx=10).pack()
    viewWindow.mainloop()


def main(firstName, email, adminPrivalges, loginTime, lastLogIn):
    # Creating the user summary
    userSummary = ('Username: ' + user + '\nFirst name: ' + firstName + '\nEmail: ' + email + '\nLog in time: ' + loginTime + '\nLast Log In: ' + lastLogIn)
    window = tk.Tk()  # Creating window
    window.geometry('360x700')
    window.title('Main menu')
    userName = user
    # View logs button
    viewLogButton = Button(window, text="View Logs", width=20, font=largefont, command=lambda: [viewLogs(window)], pady=10, padx=10)
    # Unlock door button
    unlockDoorButton = Button(window, text="Unlock door", width=20, font=largefont, command=lambda: [unlockWindow(window)], pady=10, padx=10)
    # Change password button
    changePasswordButton = Button(window, text="Change password", width=20, font=largefont, command=lambda: [changePassword(window, userName)], pady=10, padx=10)
    # Exit button
    exitButton = Button(window, text="Log off", width=20, font=largefont, command=exit, pady=10, padx=10)
    # User summary displayed
    userSumarryDisplay = Label(window, text=userSummary, font=normfont, justify="left", pady=10, padx=10)
    userSumarryDisplay.place(relx=1.0, rely=0.0, anchor='ne')

    if adminPrivalges == True:  # Function that adds in the extra features for admin users
        # Create account button
        createAccountButton = Button(window, text="Create Account", width=20, font=largefont, command=lambda: [createAccount(window)], pady=10, padx=10)
        # Manage users button
        manageUsersButton = Button(window, text="Manage App Users", width=20, font=largefont, command=lambda: [manageUsers(window)], pady=10, padx=10)
        # Manage card button
        manageCardButton = Button(window, text="Manage Card Holders", width=20, font=largefont, command=lambda: [manageCard(window)], pady=10, padx=10)
        # Email users button
        emailUsersButton = Button(window, text="Email Users", width=20, font=largefont, command=lambda: [appEmail(window)], pady=10, padx=10)
        # Placing the buttons
        viewLogButton.place(relx=0.5, rely=0.2, anchor='center')
        unlockDoorButton.place(relx=0.5, rely=0.3, anchor='center')
        createAccountButton.place(relx=0.5, rely=0.4, anchor='center')
        changePasswordButton.place(relx=0.5, rely=0.5, anchor='center')
        manageUsersButton.place(relx=0.5, rely=0.6, anchor='center')
        manageCardButton.place(relx=0.5, rely=0.7, anchor='center')
        emailUsersButton.place(relx=0.5, rely=0.8, anchor='center')
        exitButton.place(relx=0.5, rely=0.9, anchor='center')

    else:  # Puts the buttons in their location if the user is not an admin
        viewLogButton.place(relx=0.5, rely=0.4, anchor='center')
        unlockDoorButton.place(relx=0.5, rely=0.5, anchor='center')
        changePasswordButton.place(relx=0.5, rely=0.6, anchor='center')
        exitButton.place(relx=0.5, rely=0.7, anchor='center')
    window.mainloop()


def updatePassword(window, updateWindow, password, confirmPassword, userName):
    password = password.get()
    confirmPassword = confirmPassword.get()
    # Checks that the password and confirm password fields have inputs
    if 0 in [len(password), len(confirmPassword)]:
        message = "Please fill the inputs"
        title = "Alert!"
        popUpWindow(title, message, window)
    # Checks that the password and confirm password fields are the same
    elif password != confirmPassword:
        message = "Passwords do not match"
        title = "Alert!"
        popUpWindow(title, message, window)
    # Checks if the passowrd meets minimum complexity requirements
    elif len(password) < 6:
        message = "Password must be at least 6 characters"
        title = "Alert!"
        popUpWindow(title, message, window)

    else:
        # Hashing passowrd and adding it to the database
        password = password.encode()
        password = hashlib.sha3_512(password).hexdigest()
        conn.execute("UPDATE appUsers set hashedPassword = ? WHERE userName = ?", (password, userName,))
        cur.commit()
        now = datetime.now()
        logInTimeForDB = now
        # Updating the last log in time so user can log in
        conn.execute("UPDATE appUsers SET lastLogIn = ? WHERE userName = ?", (logInTimeForDB, userName,))
        cur.commit()
        # Calling a popup window informing the user that the password has been changed
        message = "Password updated successfully \nPlease log in again"
        title = "Alert!"
        updateWindow.destroy()
        popUpWindow(title, message, window)


def changePassword(window, userName):
    # GUI for the user to change their password
    updateWindow = Toplevel(window)
    updateWindow.geometry('347x195')
    updateWindow.title('Update password')
    spacer1 = Label(updateWindow, text="").grid(row=0, column=0)
    password = StringVar()
    passwordLable = Label(updateWindow, text="New password", pady=10, padx=10, width=15, anchor='w').grid(row=1, column=1)
    passwordEntry = Entry(updateWindow, textvariable=password, show='*', width=30).grid(row=1, column=2)  # Username entry
    confirmPassword = StringVar()
    confirmPasswordLable = Label(updateWindow, text="Confirm password", pady=10, padx=10, width=15, anchor='w').grid(row=2, column=1)
    confirmPasswordLable = Entry(updateWindow, textvariable=confirmPassword, show='*', width=30).grid(row=2, column=2)  # Password entry
    loginButton = Button(updateWindow, text="          Update          ", command=lambda: [updatePassword(window, updateWindow, password, confirmPassword, userName)]).grid(row=3, column=2)
    spacer2 = Label(updateWindow, text=" ").grid(row=4, column=2)
    updateWindow.mainloop()


def login(username, password, window):
    # Retrieving the information from the GUI
    userName = username.get()
    passwordToEncode = password.get()
    passwordToHash = passwordToEncode.encode()
    password = hashlib.sha3_512(passwordToHash).hexdigest()

    # Checking if the inputs are empty
    if 0 in (len(userName), len(passwordToEncode)):
        message = 'Please fill in the inputs'
        loginError(message, window)

    # Checks if an account with the username exists
    cursor = conn.execute("SELECT * FROM appUsers Where userName = ?", (userName,))
    cursor = conn.fetchall()

    # Calls a pop up window if the account does not exist
    if len(cursor) == 0:
        message = 'Username or password incorrect'
        loginError(message, window)

    passwordToCheck = cursor[0][1]

    # Checks if the password is correct
    if password == passwordToCheck:
        global user
        user = userName
        firstName = cursor[0][2]
        email = cursor[0][4]
        adminPrivalges = cursor[0][5]
        timeCreated = cursor[0][6]
        lastLogIn = cursor[0][7]

        # Checks if the user needs to reset their password
        if timeCreated == lastLogIn:
            changePassword(window, userName)

        # Logs the user in
        else:
            lastLogIn = lastLogIn.strftime("%d/%m/%y")
            now = datetime.now()
            logInTimeForDB = now
            # Updates the last log in time
            conn.execute("UPDATE appUsers SET lastLogIn = ? WHERE userName = ?", (logInTimeForDB, userName,))
            cur.commit()
            loginTime = now.strftime("%H:%M")
            message = "Logged in successfully"

            if adminPrivalges == 1:
                adminPrivalges = True
                window.destroy()
                main(firstName, email, adminPrivalges, loginTime, lastLogIn)

            else:
                adminPrivalges = False
                window.destroy()
                main(firstName, email, adminPrivalges, loginTime, lastLogIn)

    # Calls a pop up window if the password is incorrect
    else:
        message = 'Username or password incorrect'
        loginError(message, window)


def resetPassword(userName, window):
    userName = userName.get()
    cursor = conn.execute("SELECT * FROM appUsers where userName = ?", (userName,))
    cursor = conn.fetchall()
    if len(cursor) == 0:
        message = "User not found"
        loginError(message, window)
    else:
        passwordToSend = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
        # Encrypting the password
        password = passwordToSend.encode()
        password = hashlib.sha3_512(password).hexdigest()
        email = cursor[0][4]
        timeToChange = cursor[0][6]
        conn.execute("UPDATE appUsers set hashedPassword = ? WHERE userName = ?", (password, userName,))
        cur.commit()
        conn.execute("UPDATE appUsers set lastLogIn = ? WHERE userName = ?", (timeToChange, userName,))
        cur.commit()

        # Create a template Environment
        env = Environment(loader=FileSystemLoader('templates'))

        # Load the template from the Environment
        template = env.get_template('forgotPasswordTemplate.html')

        # Render the template with variables
        html = template.render(
            firstname=cursor[0][2],
            username=userName,
            password=passwordToSend,)

        # Write the template to an HTML file
        with open('email.html', 'w') as f:
            f.write(html)

        with open('email.html', 'r') as f:
            html = f.read()

        load_dotenv()
        gmail_user = os.getenv('emailAccount')
        gmail_password = os.getenv('emailPassword')

        # Create a MIMEMultipart class, and set up the From, To, Subject fields
        email_message = MIMEMultipart()
        email_message['From'] = gmail_user
        email_message['To'] = email
        email_message['Subject'] = 'There has been a change to your account on iSpy'

        # Attach the html doc defined earlier, as a MIMEText html content type to the MIME message
        email_message.attach(MIMEText(html, "html"))
        # Convert it as a string
        email_string = email_message.as_string()

        # Connect to the Gmail SMTP server and Send Email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, email, email_string)
        os.remove("email.html")


def forgotPassword(window):
    forgotPasswordWindow = Toplevel(window)
    forgotPasswordWindow.geometry('340x100')
    usernameLabel = Label(forgotPasswordWindow, text="User Name", pady=10, padx=10, width=10, anchor='w').grid(row=1, column=1)
    usernameEntry = Entry(forgotPasswordWindow, textvariable=username,  width=30).grid(row=1, column=2)  # Username entry
    emailButton = Button(forgotPasswordWindow, text="     Send recovery password      ", command=lambda: [resetPassword(username, window)]).grid(row=2, column=2)
    forgotPasswordWindow.mainloop()


def loginError(message, window):
    popUp = tk.Toplevel(window)
    popUp.geometry('250x100')
    currentWindow = popUp
    popUp.title('Alert!')
    label = Label(popUp, text=message, font=normfont)
    label.pack(side="top", fill="x", pady=10)
    button = Button(popUp, text="Okay", command=lambda: [closeWindow(currentWindow)])
    button.pack()
    popUp.mainloop()


largefont = ("Verdana", 12)
normfont = ("Helvetica", 10)
smallfontd = ("Helvetica", 8)

window = tk.Tk()  # Creating window for login system
window.geometry('347x275')
window.title('Login')  # Setting the title for window
spacer1 = Label(window, text="").grid(row=0, column=0)
username = StringVar()
usernameLabel = Label(window, text="User Name", pady=10, padx=10, width=10, anchor='w').grid(row=1, column=1)
usernameEntry = Entry(window, textvariable=username,  width=30).grid(row=1, column=2)  # Username entry
password = StringVar()
passwordLabel = Label(window, text="Password", pady=10, padx=10, width=10, anchor='w').grid(row=2, column=1)
passwordEntry = Entry(window, textvariable=password, show='*', width=30).grid(row=2, column=2)  # Password entry
# Login button
loginButton = Button(window, text="Login", width=15, padx=5, pady=5, command=lambda: [login(username, password, window)]).grid(row=3, column=2)
spacer2 = Label(window, text=" ").grid(row=4, column=2)
# Forgot password button
forgotPasswordButton = Button(window, text="Forgot password", width=15, padx=5, pady=5, command=lambda: [forgotPassword(window)]).grid(row=5, column=2)
spacer3 = Label(window, text=" ").grid(row=6, column=2)
# Exit button
exitButton = Button(window, text="Exit", width=15, padx=5, pady=5, command=exit).grid(row=7, column=2)
spacer3 = Label(window, text=" ").grid(row=8, column=2)
window.mainloop()
