#!/usr/bin/python
import sys
import time
import board
import adafruit_dht
import datetime
import timeit
import pymysql
import os
import logging
import secret


# CONFIG
cfg = secret.settings()
if cfg['got_lamp']:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(cfg['lamp_pin'], GPIO.OUT)
# developer mode
developing = cfg['dev']
# Sensor data pin is connected to GPIO 4
sensor = adafruit_dht.DHT22(board.D4, use_pulseio=False)
# log path and name
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
tstamp = datetime.datetime.now()
dt = tstamp.date()
filename = f"logs/log_{str(dt)}.txt"
log_path = os.path.join(BASE_DIR, filename)


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
            if cfg['got_lamp']:
                GPIO.output(cfg['lamp_pin'], GPIO.HIGH)
            # get_temp
            self.read_DHT22()
            # get dates for database
            self.getdates()
            self.data['sql']['code_runtime'] = timeit.default_timer() - start_runtime

            # save to database (don´t save values at first run)
            if save_values:
                self.store_db()
            else:
                msg = f"Temp: {self.data['sql']['temperature']}, Humidity: {self.data['sql']['humidity']}"
                print(msg)

            # sleep
            if developing:
                print("-------------------dev mode-------------------")
                for d in self.data['sql']:
                    print(d, ":", self.data['sql'][d])
                print("exit code")
                print("----------------------------------------------")
                if cfg['got_lamp']:
                    GPIO.output(cfg['lamp_pin'], GPIO.LOW)
                logging.info("end of program for dev mode")
                break

            sleep_time = self.sleep()
            if cfg['got_lamp']:
                GPIO.output(cfg['lamp_pin'], GPIO.LOW)
            time.sleep(sleep_time)
            save_values = True

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
        eta, sec = self.get_eta()

        while eta < ts:
            logging.debug("wait 10 sec to set next eta..")
            time.sleep(10)
            ts = datetime.datetime.now()
            eta, sec = self.get_eta()

        msg = f"sleep in {round(sec / 60)} min, get new value at: {eta}"
        self.data['sleep_msg'] = msg
        logging.debug(msg)

        return sec

    def get_eta(self):
        ts = datetime.datetime.now()
        tot_sec = (ts.minute * 60) + ts.second

        if ts.minute <= 15:
            x = 15 - ts.minute
            y = 900 - tot_sec
        elif 15 < ts.minute <= 30:
            x = 30 - ts.minute
            y = 1800 - tot_sec
        elif 30 < ts.minute <= 45:
            x = 45 - ts.minute
            y = 2700 - tot_sec
        else:
            x = 60 - ts.minute
            y = 3600 - tot_sec

        eta_min = ts + datetime.timedelta(minutes=x)
        eta = eta_min.replace(second=0, microsecond=0)

        return eta, y

    # def sleep1(self) -> float:
    #     # TODO remove this backup if not needed
    #     ts = datetime.datetime.now()
    #     eta = self.get_eta1()
    #
    #     while eta < ts:
    #         # TODO make get_data in seconds instead of min. CaCalculate with sec and min.total sum?
    #         # whole minute has to pass to get the new eta
    #         logging.debug("wait 10 sec to set next eta..")
    #         # print("wait 10 sec. TS:", ts, "ETA:", eta)
    #         time.sleep(10)
    #         ts = datetime.datetime.now()
    #         eta = self.get_eta1()
    #
    #     calc = eta - ts
    #     sec = calc.total_seconds()
    #
    #     msg = f"sleep in {round(sec / 60)} min, get new value at: {eta}"
    #     self.data['sleep_msg'] = msg
    #     logging.debug(msg)
    #
    #     return sec
    #
    # def get_eta1(self) -> datetime:
    #     ts = datetime.datetime.now()
    #
    #     tot_sec = (ts.minute * 60) + ts.second + 1
    #
    #     if ts.minute <= 15:
    #         x = 15 - ts.minute
    #         y = 900 - tot_sec
    #     elif 15 < ts.minute <= 30:
    #         x = 30 - ts.minute
    #         y = 1800 - tot_sec
    #     elif 30 < ts.minute <= 45:
    #         x = 45 - ts.minute
    #         y = 2700 - tot_sec
    #     else:
    #         x = 60 - ts.minute
    #         y = 3600 - tot_sec
    #
    #     eta_min = ts + datetime.timedelta(minutes=x)
    #     eta = eta_min.replace(second=0, microsecond=0)
    #
    #     self.data['sleep'] = y
    #
    #     # print("TEST, wait tot sec:", y, "min:", (y / 60))
    #
    #     return eta

    def store_db(self):
        logging.debug("store to database")
        try:
            columns = []
            values = []

            for x in self.data['sql']:
                columns.append(x)
                values.append(self.data['sql'][x])

            h, u, p, d = cfg['sql']
            db = pymysql.connect(host=h, user=u, passwd=p, db=d)
            cursor = db.cursor()
            # create sql string
            sql_query = 'INSERT INTO weather_kitchen (' + ', '.join(columns) + ') VALUES (' + (
                    '%s, ' * (len(columns) - 1)) + '%s)'

            cursor.execute(str(sql_query), tuple(values))
            db.commit()
            db.close()
            logging.info("stored values to database")
        except Exception as f:
            msg = "could not save to remote db:\n{0}".format(f)
            logging.exception(msg)


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
