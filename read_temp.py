#!/usr/bin/python
import sys
import time
import board
import adafruit_dht
import datetime
import timeit

import os
import logging

import secret as s

# CONFIG
developing = s.settings()
# Sensor data pin is connected to GPIO 4
sensor = adafruit_dht.DHT22(board.D4)
# log path and name
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(BASE_DIR, "log.log")


class GetTemp:
    """Get local temperature and humidity status and store it to database"""

    def __init__(self) -> None:

        self.data = {}
        self.loop = True
        # TODO
        # Lamp behaviour? Make it work
        # THIS get values every 15th minute and retry until value is obtained

        while self.loop:
            start_runtime = timeit.default_timer()
            # get_temp
            self.read_DHT22()
            # get dates for database
            self.getdates()

            #
            # sleep
            sleep_time = self.sleep()
            # TODO
            # if developing:
            #     print(self.data)
            #     break
            print(self.data)

            time.sleep(sleep_time)

            #   store value
            self.data['sql']['code_runtime'] = timeit.default_timer() - start_runtime

    def read_DHT22(self):
        # d = {}
        loop = True
        while loop:
            logging.debug("get temp")
            d = {}
            try:
                d['source'] = "kitchen"
                d['temperature'] = float(sensor.temperature)
                d['humidity'] = float(sensor.humidity)

            except RuntimeError as error:
                # Errors happen fairly often, DHT's are hard to read, just keep going
                msg = error.args[0]
                print(msg)
                logging.error(msg)
                time.sleep(2.0)
                continue
            except Exception as error:
                logging.error(f"failed to read sensor: {error}")
                sensor.exit()
                raise error

            time.sleep(3.0)
            if d:
                loop = self.validate(d)
                self.data['sql'] = d
            else:
                loop = True

    def validate(self, d) -> bool:
        # print("Validate", d)

        if d['humidity'] > 100 or d['humidity'] < 0:
            logging.warning(f"Got arbitrary humidity value: {d['humidity']}, get new values")
            return True
        elif d['temperature'] > 80 or d['temperature'] < -40:
            logging.warning(f"Got arbitrary temperature value: {d['temp']}, get new values")
            return True

        else:
            logging.info(f"got values: {d}")
            return False

    def getdates(self):
        ts = datetime.datetime.now()
        d = {'time': ts, 'month': ts.month, 'year': ts.year, 'date': ts.date()}

        self.data['sql'].update(d)

    def sleep(self) -> float:
        ts = datetime.datetime.now()

        if ts.minute <= 15:
            x = 15 - ts.minute
            y = 900 - (ts.second + ts.minute)
        elif 15 < ts.minute <= 30:
            x = 30 - ts.minute
            y = 1800 - (ts.second + ts.minute)
        elif 30 < ts.minute <= 45:
            x = 45 - ts.minute
            y = 2700 - (ts.second + ts.minute)
        else:
            x = 60 - ts.minute
            y = 3600 - (ts.second + ts.minute)

        adjust_sec = 60 - ts.second
        eta_min = ts + datetime.timedelta(minutes=x)

        # THIS!
        eta = eta_min.replace(second=0, microsecond=0)

        #eta = ts + datetime.timedelta(minutes=x, seconds=y, microseconds=round(z))
        #msg = f"sleep in {ts.replace(microsecond=0, second=0) + datetime.timedelta(minutes=x)} min, get new value at: {eta}"


        # sec = (x * 60) - (60 - ts.second)

        # is it !?!?
        calc = eta - ts
        sec = calc.total_seconds()

        #dl = eta -

        #tminus = eta - ts
        #print("eta - ts =", tminus)
        #sec = tminus.total_seconds() + adjust_sec
        #sec = eta.total_seconds() + adjust_sec



        print("TS:", ts)
        print("ETA:", eta)
        print("seconds to sleep:", sec)
        print("min to sleep:", round(sec / 60))

        msg = f"sleep in {round(sec / 60)} min, get new value at: {eta}"
        self.data['sleep_msg'] = msg
        logging.debug(msg)

        # TODO does not work returns a negative value ( -code runtime), should be a easy fix
        return sec


if __name__ == "__main__":
    if developing:
        logging.basicConfig(level=logging.DEBUG, filename=log_path, filemode="w",
                            format="%(asctime)s - %(levelname)s - %(message)s")
    else:
        # TODO: change INFO -> WARNING
        logging.basicConfig(level=logging.WARNING, filename=log_path, filemode="w",
                            format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("read_temp.py stared")
    GetTemp()
