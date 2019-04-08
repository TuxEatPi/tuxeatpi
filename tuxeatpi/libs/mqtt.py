import paho.mqtt.client as paho


class Client(paho.Client):

    def __init__(self, topics, logger):
        paho.Client.__init__(self)
        import ipdb;ipdb.set_trace()
        self.must_run = True
        self.topics = topics
        self.logger = logger

    def on_connect(self, mqttc, obj, flags, rc):
#        print("rc: "+str(rc))
        pass

    def on_message(self, mqttc, obj, msg):
        print("DDDDDDD")
        print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

    def on_publish(self, mqttc, obj, mid):
#        print("mid: "+str(mid))
        pass

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
#        print("Subscribed: "+str(mid)+" "+str(granted_qos))\
        pass

    def on_log(self, mqttc, obj, level, string):
#        print(string)
        pass

    def run(self):
        self.connect("127.0.0.1", 1883, 60)
        for topic in topics:
            self.subscribe(topic, 0)
            self.logger.info("subcription to topic %s", topic)

        while self.must_run:
            self.loop()
        return
