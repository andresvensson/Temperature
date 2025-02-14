#!/usr/bin/python
import sys
import time
import board
import adafruit_dht
import datetime
import timeit

import os
import logging

import secret
import secret as s

# CONFIG
cfg = secret.settings()
developing = cfg['dev']
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

        # don´t save first time run to db
        save_values = False
        while self.loop:
            start_runtime = timeit.default_timer()
            # get_temp
            self.read_DHT22()
            # get dates for database
            self.getdates()
            self.data['sql']['code_runtime'] = timeit.default_timer() - start_runtime

            # TODO
            # if developing:
            #     print(self.data)
            #     break

            # TODO
            # save to db, or not
            # if it has an eta, save to db??

            # do not save values first run
            if save_values:
                print("save to db")

            # sleep
            sleep_time = self.sleep()
            print(self.data)  # <-- TODO, remove pls
            time.sleep(sleep_time)
            save_values = True

            #   store value

    def read_DHT22(self):
        # d = {}
        loop = True
        while loop:
            logging.debug("get temp")
            d = {}
            try:
                d['source'] = cfg['name']
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
        eta = self.get_eta()

        while eta < ts:
            # whole minute has to pass to get the new eta
            logging.debug("wait 10 sec to set next eta..")
            # print("wait 10 sec. TS:", ts, "ETA:", eta)
            time.sleep(10)
            ts = datetime.datetime.now()
            eta = self.get_eta()

        calc = eta - ts
        sec = calc.total_seconds()

        msg = f"sleep in {round(sec / 60)} min, get new value at: {eta}"
        self.data['sleep_msg'] = msg
        logging.debug(msg)

        return sec

    def get_eta(self) -> datetime:
        ts = datetime.datetime.now()

        if ts.minute <= 15:
            x = 15 - ts.minute
        elif 15 < ts.minute <= 30:
            x = 30 - ts.minute
        elif 30 < ts.minute <= 45:
            x = 45 - ts.minute
        else:
            x = 60 - ts.minute

        eta_min = ts + datetime.timedelta(minutes=x)
        eta = eta_min.replace(second=0, microsecond=0)

        return eta


if __name__ == "__main__":
    if developing:
        logging.basicConfig(level=logging.DEBUG, filename=log_path, filemode="w",
                            format="%(asctime)s - %(levelname)s - %(message)s")
    else:
        # TODO: change INFO -> WARNING Make filename for each week
        logging.basicConfig(level=logging.WARNING, filename=log_path, filemode="w",
                            format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("read_temp.py stared")
    GetTemp()
