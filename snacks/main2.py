#!/usr/bin/python
import sys

import logging
import time

import RPi.GPIO as GPIO
import SimpleMFRC522
import time
import board
import digitalio
from pad4pi import rpi_gpio
import adafruit_character_lcd.character_lcd as characterlcd


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

class VendingMachine(object):

    def __init__(self, rfid_reader, lcd, keypad):
        self.rfid_reader = rfid_reader
        self.lcd = lcd
        self.keypad = keypad
        self.code = ""
        self.confirmed = False
        self.rfid_id = 0
        self.rfid_text = ""
        self.keypad.clearKeyPressHandlers()

    def receive_key(self, key):
        log.debug("Read {} on keypad".format(key))
        self.code += "{}".format(key)
        self.set_lcd_message("Hello {}\nEnter code:{}".format(self.rfid_id, self.code))
        log.debug("Current code is: {}".format(self.code))

    def set_lcd_message(self, message):
        self.lcd.clear()
        self.lcd.message = message

    def receive_star(self, key):
        if key == "*":
            self.confirmed = True

    def read_code(self):
        self.keypad.registerKeyPressHandler(self.receive_key)
        while len(self.code) < 4:
            time.sleep(1)

    def read_star(self):
        self.keypad.registerKeyPressHandler(self.receive_star)
        while len(self.code) < 4:
            time.sleep(1)

    def cleanup(self):
        log.debug("Cleaning up GPIO")
        GPIO.cleanup()

    def get_user(self, id):
        return {566428238497: 'Math'}.get(id, 'Unknown')

    def main_loop(self):

        self.set_lcd_message('Snacks \nScan badge..')
        self.lcd.blink = True
        self.rfid_id, self.rfid_text = self.rfid_reader.read()
        self.lcd.clear()
        self.set_lcd_message("Hello {}\nEnter code:".format(self.get_user(self.rfid_id)))
        self.read_code()
        self.lcd.clear()
        self.set_lcd_message('You entered {}\nConfirm with *'.format(self.code))
        log.debug("Asking confirmation")
        self.read_star()
        timeout = 0
        self.lcd.blink = False
        while not self.confirmed and timeout < 5:
            time.sleep(1)
            timeout += 1
        if self.confirmed:
            log.debug("Confirmed!")
            self.set_lcd_message('Thank you!\nCome again!')
        else:
            self.set_lcd_message('No confirmation received\nOperation cancelled')
            log.debug("Not confirmed")
        time.sleep(3)

if __name__ == "__main__":

    # lcd definition
    lcd_rs = digitalio.DigitalInOut(board.D26)
    lcd_en = digitalio.DigitalInOut(board.D19)
    lcd_d7 = digitalio.DigitalInOut(board.D27)
    lcd_d6 = digitalio.DigitalInOut(board.D22)
    lcd_d5 = digitalio.DigitalInOut(board.D24)
    lcd_d4 = digitalio.DigitalInOut(board.D25)
    lcd_backlight = digitalio.DigitalInOut(board.D4)
    lcd_columns = 16
    lcd_rows = 2
    lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6,
                                               lcd_d7, lcd_columns, lcd_rows,
                                               lcd_backlight)

    # keypad definition
    keypad_layout = [
        [1, 2, 3, "A"],
        [4, 5, 6, "B"],
        [7, 8, 9, "C"],
        ["*", 0, "#", "D"]
    ]
    row_pins = [12, 16, 20, 21]  # BCM numbering
    col_pins = [4, 5, 6, 13]  # BCM numbering
    factory = rpi_gpio.KeypadFactory()
    keypad = factory.create_keypad(keypad=keypad_layout, row_pins=row_pins, col_pins=col_pins)

    # rfid reader
    rfid_reader = SimpleMFRC522.SimpleMFRC522()

    try:
        exited = False
        while not exited:
            try:
                log.debug('Starting vending machine...')
                vm = VendingMachine(rfid_reader, lcd, keypad)
                vm.main_loop()
                log.debug('Vending machine terminated')
            except KeyboardInterrupt:
                exited = True
                log.debug('Asked to exit')
    finally:
        vm.cleanup()