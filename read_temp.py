#!/usr/bin/python
import time
import board
import adafruit_dht

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
        # TODO
        # Lamp behaviour? Make it work
        # NOT THIS? get new stats at start and for every last 3 minutes to even 15 minutes (ex 21:13, 21:14, 21:15)
        # THIS get values every 15th minute and retry until value is obtained

        # get_temp
        self.read_DHT22()
        print(self.data)
        #   validate <- add to self.read_DHT22
        #
        # sleep
        #   store value

    def read_DHT22(self):
        # d = {}
        loop = True
        while loop:
            logging.info("get temp")
            d = {}
            try:
                # Print the values to the serial port
                #temperature_c = sensor.temperature
                #temperature_f = temperature_c * (9 / 5) + 32
                #humidity = sensor.humidity

                d['source'] = "kitchen"
                d['temperature'] = float(sensor.temperature)
                d['humidity'] = float(sensor.humidity)

                # fail validate
                # d['humidity'] = d['humidity'] + 150

                #print("Temp={0:0.1f}ºC, Temp={1:0.1f}ºF, Humidity={2:0.1f}%".format(temperature_c, temperature_f, humidity))
                # for r in d:
                #     print(r, d[r], type(r))

            except RuntimeError as error:
                # Errors happen fairly often, DHT's are hard to read, just keep going
                print(error.args[0])
                time.sleep(2.0)
                continue
            except Exception as error:
                sensor.exit()
                raise error

            #self.validate()
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
            return False









if __name__ == "__main__":
    if developing:
        logging.basicConfig(level=logging.DEBUG, filename=log_path, filemode="w",
                            format="%(asctime)s - %(levelname)s - %(message)s")
    else:
        #TODO: change INFO -> WARNING
        logging.basicConfig(level=logging.WARNING, filename=log_path, filemode="w",
                            format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("read_temp.py stared")
    GetTemp()
