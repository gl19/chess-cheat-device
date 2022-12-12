import RPi.GPIO as GPIO
import time
import socket

PIN = 17
IP_ADDRESS = ''
SOCKET = 8080

CODE = {'1': '.----',
        '2': '..---',
        '3': '...--',
        '4': '....-',
        '5': '.....',
        '6': '-....',
        '7': '--...',
        '8': '---..',
        'A': '.-',
        'B': '-...',
        'C': '-.-.',
        'D': '-..',
        'E': '.',
        'F': '..-.',
        'G': '--.',
        'H': '....'
    }
    

def dot():
	GPIO.output(PIN, 1)
	time.sleep(0.2)
	GPIO.output(PIN, 0)
	time.sleep(0.2)


def dash():
	GPIO.output(PIN, 1)
	time.sleep(0.5)
	GPIO.output(PIN, 0)
	time.sleep(0.2)


def try_upper(c):
    if c.isdigit():
        return c
    else:
        return c.upper()


GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.OUT)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((IP_ADDRESS, SOCKET))
sock.listen()
client_socket, client_address = sock.accept()

while True:
    data = client_socket.recv(1024).decode('ascii')
    print(data)
    for letter in data:
        for symbol in CODE[try_upper(letter)]:
            if symbol == '-':
                dash()
            elif symbol == '.':
                dot()
            else:
                time.sleep(0.5)
        time.sleep(0.5)

client_socket.close()
