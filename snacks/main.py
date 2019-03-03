#!/usr/bin/python
# Example using a character LCD connected to a Raspberry Pi
import time

import RPi.GPIO as GPIO
import SimpleMFRC522

import board
import digitalio
lcd_rs = digitalio.DigitalInOut(board.D26)
lcd_en = digitalio.DigitalInOut(board.D19)
lcd_d7 = digitalio.DigitalInOut(board.D27)
lcd_d6 = digitalio.DigitalInOut(board.D22)
lcd_d5 = digitalio.DigitalInOut(board.D24)
lcd_d4 = digitalio.DigitalInOut(board.D25)
lcd_backlight = digitalio.DigitalInOut(board.D4)

lcd_columns = 16
lcd_rows = 2

import adafruit_character_lcd.character_lcd as characterlcd
lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows, lcd_backlight)
lcd.backlight = False

lcd.message = 'Snacks @ EURid\nScan your badge'

reader = SimpleMFRC522.SimpleMFRC522()

try:
        id, text = reader.read()
        lcd.message = "Hello {}".format(id)
        print("Hello {}!".format(id))

finally:
        GPIO.cleanup()
        print("Out!")
