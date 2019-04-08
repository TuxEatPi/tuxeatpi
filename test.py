import paho.mqtt.client as paho



class MyMQTTClass(paho.Client):

    def on_connect(self, mqttc, obj, flags, rc):
#        print("rc: "+str(rc))
        pass

    def on_message(self, mqttc, obj, msg):
        print("DDDDDDD")
        print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

    def on_publish(self, mqttc, obj, mid):
        print("mid: "+str(mid))
        pass

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
#        print("Subscribed: "+str(mid)+" "+str(granted_qos))\
        pass

    def on_log(self, mqttc, obj, level, string):
#        print(string)
        pass

    def run(self):
        self.connect("127.0.0.1", 1883, 60)
#        self.subscribe("nlu/audio", 0)

        rc = 0
        while rc == 0:
            rc = self.loop()

            import time
            time.sleep(2)
            self.publish("nlu/audio", "FFFF")
            print("D")
        return rc


client = MyMQTTClass()
client.run()


