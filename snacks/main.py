#!/usr/bin/python
# Example using a character LCD connected to a Raspberry Pi
import time

import RPi.GPIO as GPIO
import SimpleMFRC522
import time
import board
import digitalio
from pad4pi import rpi_gpio
import adafruit_character_lcd.character_lcd as characterlcd

lcd_rs = digitalio.DigitalInOut(board.D26)
lcd_en = digitalio.DigitalInOut(board.D19)
lcd_d7 = digitalio.DigitalInOut(board.D27)
lcd_d6 = digitalio.DigitalInOut(board.D22)
lcd_d5 = digitalio.DigitalInOut(board.D24)
lcd_d4 = digitalio.DigitalInOut(board.D25)
lcd_backlight = digitalio.DigitalInOut(board.D4)

lcd_columns = 16
lcd_rows = 2

KEYPAD = [
    [1, 2, 3, "A"],
    [4, 5, 6, "B"],
    [7, 8, 9, "C"],
    ["*", 0, "#", "D"]
]

ROW_PINS = [12, 16, 20, 21]  # BCM numbering
COL_PINS = [4, 5, 6, 13]  # BCM numbering

code = ''
def print_key(key):
    global code
    code += "{}".format(key)
    lcd.message = code
    print(code)


def read_code():
    factory = rpi_gpio.KeypadFactory()
    keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS, col_pins=COL_PINS)

    keypad.registerKeyPressHandler(print_key)

    print("Press buttons on your keypad. Ctrl+C to exit.")
    while len(code) <= 4:
        time.sleep(1)

lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows,
                                      lcd_backlight)
lcd.backlight = False

lcd.message = 'Snacks @ EURid\nScan badge..'
lcd.blink = True

reader = SimpleMFRC522.SimpleMFRC522()

try:
    id, text = reader.read()
    lcd.clear()
    lcd.message = "Hello {}\nEnter code:".format(id)
    lcd.blink = True
    read_code()
    lcd.clear()
    lcd.message = "You typed {}".format(code)


finally:
    print('out')
#finally:
#    keypad.cleanup()
#    GPIO.cleanup()
#    print("Out!")
GPIO.cleanup()