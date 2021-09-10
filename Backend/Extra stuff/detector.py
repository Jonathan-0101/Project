import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
PIR_PIN = 14 # Assign GPIO4 pin 7 to PIR
GPIO.setup(PIR_PIN, GPIO.IN) # Setup GPIO pin PIR as input
print('Sensor initializing . . .')
time.sleep(15) # Give sensor time to start-up, 60 seconds
print('Active')
def pir(pin):
    print('Motion Detected!')
    time.sleep(10)
try:
    GPIO.add_event_detect(14, GPIO.FALLING, callback=pir, bouncetime=100)
