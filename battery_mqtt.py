import  logging
import json
import paho.mqtt.client as mqtt
from datetime import datetime


class PvMqtt:

    def __init__(self, host: str = "0.0.0.0", port: int = 1883):
        self.host = host
        self.port = port
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.last_update = datetime.now()
        self.level = 0

    def start(self):
        self.client.connect(self.host, self.port)
        self.client.subscribe("#")
        logging.info("wait for data...")

        # Start the network loop in a background thread
        # so the main thread isn't blocked and we can call stop() later.
        self.client.loop_start()

    def stop(self):
        """
        Gracefully stops the MQTT client and disconnects from the broker.
        """
        # Stop the background network loop
        self.client.loop_stop()

        # Disconnect from the MQTT broker cleanly
        self.client.disconnect()
        logging.info("MQTT connection stopped.")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            data = json.loads(payload)

            soc = data.get("soc")
            if soc is not None:
                self.last_update = datetime.now()
                self.level = soc

        except json.JSONDecodeError:
            logging.info("Fehler beim Parsen der JSON-Daten.")