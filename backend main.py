# Importing requiered modules
import os
import ssl
import time
import mariadb
import smtplib
import RPi.GPIO as GPIO
from picamera import PiCamera
from datetime import datetime
from dotenv import load_dotenv
from mfrc522 import SimpleMFRC522
from email.mime.text import MIMEText
from email.message import EmailMessage
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader

load_dotenv()
dbIp = os.getenv("dbIp")
dbUserName = os.getenv('dbUserName')
dbPassword = os.getenv('dbPassword')

cur = mariadb.connect(host=dbIp, database='iSpy', user=dbUserName, password=dbPassword)

conn = cur.cursor()

# Seting up the Pins and devices connected to the Rasberry Pi
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
PIR_PIN = 14
reader = SimpleMFRC522()
GPIO.setup(PIR_PIN, GPIO.IN)  # Setup GPIO pin PIR as input
print('Sensor initializing . . .')
time.sleep(15)  # Give sensor time to start-up, 15 seconds
print('Active')
Relay_PIN = 4


def emailSummary():
    jinjaVar = {'entries': []}

    entryLog = conn.execute("SELECT * FROM entryLog WHERE authorised = 1 and dateTime > DATE_SUB(NOW(), INTERVAL 1 DAY)")
    entryLog = conn.fetchall()

    for entry in entryLog:
        details = conn.execute("SELECT * FROM idCards WHERE id = ?", (entry[2],))
        details = conn.fetchall()
        firstNmae = details[0][3]
        lastName = details[0][4]
        name = firstNmae + " " + lastName
        dateTime = entry[3].strftime("%H:%M:%S %d/%m/%Y")
        jinjaVar['entries'].append({'name': name, 'dateTime': dateTime})

    # Create a template Environment
    env = Environment(loader=FileSystemLoader('templates'))

    # Load the template from the Environment
    template = env.get_template('summaryTemplate.html')

    # Render the template with variables
    html = template.render(jinjaVar)

    # Write the template to an HTML file
    with open('email.html', 'w') as f:
        f.write(html)

    with open('email.html', 'r') as f:
        html = f.read()

    email = "jonathan.woolf.01@gmail.com"
    emails = conn.execute("SELECT email FROM appUsers")
    emails = conn.fetchall()
    recipients = []
    for email in emails:
        recipients.append(email[0])

    load_dotenv()
    gmail_user = os.getenv('emailAccount')
    gmail_password = os.getenv('emailPassword')

    # Create a MIMEMultipart class, and set up the From, To, Subject fields
    email_message = MIMEMultipart()
    email_message['From'] = gmail_user
    email_message['To'] = ", ".join(recipients)
    email_message['Subject'] = 'Daily activity summary'

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


def updateSendTime():
    print("Func run")
    baseTime = 210000
    sendDay = datetime.now()
    sendDay = sendDay + timedelta(days=1)
    sendDay = sendDay.strftime("%Y/%m/%d")
    sendDay = int(sendDay.replace("/", ""))*1000000
    sendTime = sendDay+baseTime
    print(sendTime)
    return sendTime


def lcLock():
    # Function for locking the door
    GPIO.setup(Relay_PIN, GPIO.OUT)
    GPIO.output(Relay_PIN, GPIO.LOW)
    print("Door locked")
    # Resseting value in db so that door can be unlocked again
    conn.execute("Update doorStatus set lockStatus = 0")
    cur.commit()


def lcUnlock():  # Function for unlocking the door and stopping the recording
    GPIO.setup(Relay_PIN, GPIO.OUT)
    GPIO.output(Relay_PIN, GPIO.HIGH)
    print('Door unlocked')
    time.sleep(30)
    lcLock()


def cameraStop(fileName, camera):
    time.sleep(10)
    camera.stop_recording()


def lock():  # Function for locking the door
    GPIO.setup(Relay_PIN, GPIO.OUT)
    GPIO.output(Relay_PIN, GPIO.LOW)
    print('Door locked')


def unlock():  # Function for unlocking the door and stopping the recording
    GPIO.setup(Relay_PIN, GPIO.OUT)
    GPIO.output(Relay_PIN, GPIO.HIGH)
    print('Door unlocked')
    time.sleep(30)


def lockMain(fileName, camera):  # Function for locking the door
    GPIO.setup(Relay_PIN, GPIO.OUT)
    GPIO.output(Relay_PIN, GPIO.LOW)
    print('Door locked')
    cameraStop(fileName, camera)


def unlockMain(fileName, camera):  # Function for unlocking the door and stopping the recording
    GPIO.setup(Relay_PIN, GPIO.OUT)
    GPIO.output(Relay_PIN, GPIO.HIGH)
    print('Door unlocked')
    time.sleep(10)
    lockMain(fileName, camera)


def pir(pin):  # Function for running the events when motion is detected
    now = datetime.now()  # Getting current date and time
    dateTime = now
    cursor = conn.execute("SELECT * FROM entryLog")
    cursor = conn.fetchall()

    # Naming the video file in relation to the event id
    if len(cursor) == 0:
        videoFileName = "1"

    else:
        videoFileName = str(len(cursor)+1)

    # Getting path to the file as will differ per computer
    path = os.getcwd()
    # Add the requiered video to the end of the path
    fileName = (path + "/Recordings/" + videoFileName + ".h264")
    camera.start_preview(alpha=200)
    time.sleep(0.1)  # Delay for camera preview to start up
    camera.start_recording(fileName)  # Starts the recording
    print('Motion Detected!')
    # Setting default values for cardId and cardName if they do not get written
    cardId = None
    cardName = None
    cardId, cardName = reader.read(timeout=20)  # Reading the card waiting for 20 seconds if no card is scanned
    cardId = cardId  # Hashing the cardId

    # Checks if the card is authorised
    cursor = conn.execute("SELECT * FROM idCards Where cardId = ? and cardName = ? and active = 1", (cardId, cardName,))
    cursor = conn.fetchall()
    cardCheck = cursor

    if len(cardCheck) == 1:
        print('Authorised')
        authorised = True
        userId = cursor[0][0]
        # Adds the event into the entry log
        conn.execute("INSERT INTO entryLog(authorised, userId, dateTime) VALUES (?,?,?)", (authorised, userId, dateTime,))
        cur.commit()
        # Create a template Environment
        cursor = conn.execute("SELECT * FROM idCards WHERE cardId = ?", (cardId,))
        cursor = conn.fetchall()
        firstname = cursor[0][3]
        lastname = cursor[0][4]
        entryTime = dateTime.strftime("%H:%M:%S %d/%m/%Y")
        cursor = conn.execute("SELECT * FROM appUsers WHERE userName = ?", ("security",))
        cursor = conn.fetchall()
        user = cursor[0][2]
        email_to = cursor[0][4]

        env = Environment(loader=FileSystemLoader('templates'))

        # Load the template from the Environment
        template = env.get_template('eventTemplate.html')

        # Render the template with variables
        html = template.render(
            user=user,
            firstName=firstname,
            lastName=lastname,
            entryTime=entryTime)

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
        email_message['To'] = email_to
        email_message['Subject'] = 'Activity has been detected'

        # Attach the html doc defined earlier, as a MIMEText html content type to the MIME message
        email_message.attach(MIMEText(html, "html"))
        # Convert it as a string
        email_string = email_message.as_string()

        # Connect to the Gmail SMTP server and Send Email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, email_to, email_string)
        os.remove("email.html")
        unlockMain(fileName, camera)  # Calls the function to unlock the door

    else:
        print("Not authorised")
        time.sleep(15)
        authorised = False
        camera.stop_recording()
        camera.stop_preview()
        # Adds the event to the events log
        conn.execute("INSERT INTO entryLog(authorised, dateTime) VALUES (?,?)", (authorised, dateTime,))
        cur.commit()


lock()  # Calling the lock function on statrup to lock the door incase there is a power loss
global camera
camera = PiCamera()  # Setting the camera that will be used
camera.resolution = (1920, 1080)
camera.framerate = 24  # Sets the frame rate of the camera
sendTime = 00000000000000  # Sets default value for send time - means that an email will be sent on startup

GPIO.add_event_detect(14, GPIO.FALLING, callback=pir, bouncetime=100)  # Checks for motion

try:
    while True:  # Loops the check for motion
        # Checks if it is time to send the summary out
        timeCheck = datetime.now()
        timeCheck = timeCheck.strftime("%Y/%m/%d %H:%M:%S")
        timeCheck = timeCheck.replace(":", "")
        timeCheck = timeCheck.replace("/", "")
        timeCheck = int(timeCheck.replace(" ", ""))
        if timeCheck > sendTime:
            sendTime = updateSendTime()
            print("Time to send")
            emailSummary()
        # Retriveing the doorStatus value from the table
        cursor = conn.execute("SELECT * FROM doorStatus")
        cursor = conn.fetchall()
        # Checks if the value is equal to 1 (whether it should open)
        if cursor[0][0] == 1:
            # Calls unlock function and then locking function
            lcUnlock()
        else:
            time.sleep(0.5)  # Adds a 0.5 second delay before the check is run agian

except KeyboardInterrupt:
    print("\nScript ended")
    camera.close()  # Closes the camera when the script ends

finally:
    GPIO.cleanup()  # Cleans up the GPIO connections
