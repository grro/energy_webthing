import  logging
import json
import paho.mqtt.client as mqtt
from datetime import datetime


class PvMqtt:

    def __init__(self, host: str, port: int = 1883, topic: str = 'homeassistant/sensor/MSA-280425340053/quick/state'):
        self.is_running = True
        self.host = host
        self.port = port
        self.topic = topic
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.last_update = datetime.now()
        self.state_of_charge = 0
        self.__listeners = set()

    def add_listener(self,listener):
        self.__listeners.add(listener)

    def __notify_listeners(self):
        for listener in self.__listeners:
            listener()

    def start(self):
        try:
            self.client.connect(self.host, self.port)
            self.client.loop_start()
            logging.info("MQTT client started.")
        except Exception as e:
            logging.error(f"MQTT connection error: {e}", exc_info=True)


    def stop(self):
        self.client.disconnect()
        self.client.loop_stop()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info(f"Connected to MQTT broker at {self.host}:{self.port}")
            self.client.subscribe(self.topic)
            logging.info(f"topic {self.topic} subscribed")
        else:
            logging.warning(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            data = json.loads(payload)
            if 'soc' in data:
                soc = data.get("soc")
                if soc != self.state_of_charge:
                    self.last_update = datetime.now()
                    self.state_of_charge = soc
                    logging.info("level " + str(self.state_of_charge) + " %")
                    self.__notify_listeners()

        except json.JSONDecodeError:
            logging.info("Fehler beim Parsen der JSON-Daten.")