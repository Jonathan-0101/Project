import time
import sqlite3
import RPi.GPIO as GPIO

Relay_PIN = 4
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

conn = sqlite3.connect('System.db', check_same_thread=False)
conn.execute('''CREATE TABLE if not exists doorStatus (lockStatus INTEGER PRIMARY KEY);''')
conn.commit()

cursor = conn.execute("INSERT into doorStatus(lockStatus) VALUES (?)", [0])
conn.commit()

def main():
    while True:
        cursor = conn.execute("SELECT * FROM doorStatus").fetchall()
        if cursor[0][0] == 1:
            unlock()
            lock()
            time.sleep(0.25)
        else:
            time.sleep(0.25)
        
def unlock():
    GPIO.setup(Relay_PIN, GPIO.OUT)
    GPIO.output(Relay_PIN, GPIO.HIGH)
    print('Door unlocked')
    time.sleep(30)

def lock():
    GPIO.setup(Relay_PIN, GPIO.OUT)
    GPIO.output(Relay_PIN, GPIO.LOW)
    print('Door locked')

main()