#!/usr/bin/python
import os
import sys

import logging
import time

import requests

import RPi.GPIO as GPIO
import SimpleMFRC522
import time
import board
import digitalio
from pad4pi import rpi_gpio
import adafruit_character_lcd.character_lcd as characterlcd

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

SECRET = os.environ.get('SHARED_SECRET')
if SECRET is None:
    log.fatal("No secret set, shutting down!")
    sys.exit(1)


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
        self.set_lcd_message("Hello {}\nEnter code:{}".format(self.user, self.code))
        log.debug("Current code is: {}".format(self.code))

    def set_lcd_message(self, message, blink=False):
        self.lcd.blink = blink
        self.lcd.clear()
        self.lcd.message = message

    def receive_star(self, key):
        if key == "*":
            self.confirmed = True

    def read_code(self):
        self.keypad.registerKeyPressHandler(self.receive_key)
        while len(self.code) < 4:
            time.sleep(1)
        self.keypad.unregisterKeyPressHandler(self.receive_key)

    def read_star(self):
        self.keypad.registerKeyPressHandler(self.receive_star)

    def cleanup(self):
        log.debug("Cleaning up GPIO")
        GPIO.cleanup()

    def get_balance(self, id):
        try:
            r = requests.get(url='https://snacks.4lunch.eu/balance', params={'badge': id, 'secret': SECRET})
            r.raise_for_status()
            return r.json()
        except:
            return None

    def get_user(self, id):
        try:
            r = requests.get(url='https://snacks.4lunch.eu/user', params={'badge': id, 'secret': SECRET})
            r.raise_for_status()
            return r.json()
        except:
            return None

    def get_item(self, code):
        try:
            r = requests.get(url='https://snacks.4lunch.eu/item', params={'code': code, 'secret': SECRET})
            r.raise_for_status()
            return r.json()
        except:
            return None

    def pay(self):
        try:
            r = requests.post(url='https://snacks.4lunch.eu/pay', data={'code': self.code, 'badge': self.rfid_id}, params={'secret': SECRET})
            r.raise_for_status()
            return r.json()
        except:
            return None

    def main_loop(self):
        try:
            r = requests.get(url="https://snacks.4lunch.eu")
            # r = requests.get(url="https://httpstat.us/500")
            r.raise_for_status()
            log.debug("Network OK")
        except:
            self.set_lcd_message("Server error\nNetwork down ?", blink=False)
            log.debug("Can't reach server: {}".format(r))
            time.sleep(60)
        self.set_lcd_message('Snacks ?\nScan badge..', blink=True)
        self.lcd.blink = True
        self.rfid_id, self.rfid_text = self.rfid_reader.read()
        self.user = self.get_user(self.rfid_id)
        if self.user is None:
            self.set_lcd_message("Unknown badge\n{}".format(self.rfid_id), blink=False)
            time.sleep(10)
            return
        self.set_lcd_message("Hello {}\nEnter code:".format(self.user), blink=True)
        self.read_code()
        if self.code == '1A*D':
            log.debug("Special code received: 1A*D -> shutdown!")
            self.set_lcd_message("Shutting down!\nBye!")
            shutdown(None)
        self.item = self.get_item(self.code)
        if self.item is None:
            self.set_lcd_message("Invalid code", blink=False)
            time.sleep(3)
            return
        self.set_lcd_message('{} {}\nConfirm with *'.format(self.item['price'], self.item['name']), blink=True)
        log.debug("Asking confirmation")
        self.read_star()
        timeout = 0
        while not self.confirmed and timeout < 5:
            time.sleep(1)
            timeout += 1
        if self.confirmed:
            log.debug("Paying {} for user {}".format(self.code, self.user))
            if self.pay() is None:
                log.error("Payment error!")
            log.debug("Confirmed!")
            balance = self.get_balance(self.rfid_id)
            self.set_lcd_message('Thank you!\nBalance: {}'.format(balance), blink=False)
        else:
            self.set_lcd_message('No confirmation\nSale aborted :(', blink=False)
            log.debug("Not confirmed")
        time.sleep(3)


def restart(channel):
    log.debug("Restart requested via button")
    os.execl(sys.executable, *([sys.executable] + sys.argv))
    sys.exit(0)


def shutdown(channel):
    log.debug("Shutdown requested via button")
    os.system('systemctl poweroff')


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

    # reset button
    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(17, GPIO.RISING, callback=restart, bouncetime=500)

    # shutdown button - not working (too much noise from other button)
    # GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # GPIO.add_event_detect(7, GPIO.RISING, callback=shutdown, bouncetime=500)

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
