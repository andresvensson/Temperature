#!/usr/bin/python
import time
import board
import adafruit_dht

import os
import logging

import secret as s

# CONFIG
developing = s.settings()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(BASE_DIR, "log.log")


class GetTemp:
    """Get local temperature and humidity status and store it to database"""
    def __init__(self) -> None:
        self.data = None
        # get new stats at start and for every last 3 minutes to even 15 minutes (ex 21:13, 21:14, 21:15)








if __name__ == "__main__":
    print("start")
    if developing:
        logging.basicConfig(level=logging.DEBUG, filename=log_path, filemode="w",
                            format="%(asctime)s - %(levelname)s - %(message)s")
    else:
        #TODO: change INFO -> WARNING
        logging.basicConfig(level=logging.WARNING, filename=log_path, filemode="w",
                            format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("read_temp.py stared")
    GetTemp()