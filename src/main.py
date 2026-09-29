import json
import time
import random
import math
import paho.mqtt.client as mqtt

BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "ecte474/fleet/telemetry"

# Dubai base location (center point)
BASE_LAT = 25.1972
BASE_LON = 55.2744

FLEET_SIZE = 3
MOVE_STEP = 0.0005

ROUTE = [
    (25.1972, 55.2744),
    (25.1985, 55.2720),
    (25.2000, 55.2750),
    (25.1990, 55.2780),
    (25.1972, 55.2744)
]

client = mqtt.Client()
client.connect(BROKER, PORT, 60)
client.loop_start()

# Haversine distance (km)
def distance_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)

    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2

    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

class Truck:

    def __init__(self, name, idx):
        self.id = name
        self.i = idx
        self.lat, self.lon = ROUTE[idx]
        self.speed = random.randint(40,80)
        self.rpm = 1500
        self.temp = random.uniform(80,95)

    def move(self):

        ni = (self.i + 1) % len(ROUTE)
        tlat, tlon = ROUTE[ni]

        dlat = tlat - self.lat
        dlon = tlon - self.lon
        dist = math.sqrt(dlat**2 + dlon**2)

        if dist < MOVE_STEP:
            self.i = ni
        else:
            self.lat += dlat/dist * MOVE_STEP
            self.lon += dlon/dist * MOVE_STEP

        self.speed = random.randint(40,120)
        self.rpm = int(800 + self.speed * 25)
        self.temp += random.uniform(-1.5, 2.5)
        self.temp = max(75, min(self.temp,120))

    def payload(self):

        geo_dist = distance_km(self.lat, self.lon, BASE_LAT, BASE_LON)

        alert = ""

        if geo_dist > 100:
            alert = "GEO_OUT"

        if self.temp > 110:
            alert = "TEMP_HIGH"

        if self.speed > 100:
            alert = "OVER_SPEED"

        return {
            "truck": self.id,
            "lat": round(self.lat,6),
            "lon": round(self.lon,6),
            "speed": int(self.speed),
            "rpm": self.rpm,
            "temp": round(self.temp,1),
            "distance_km": round(geo_dist,1),
            "alert": alert,
            "time": time.time()
        }

trucks = [Truck(f"Truck_{i+1}", i) for i in range(FLEET_SIZE)]

print("Fleet simulator with GEO alerts started...")

while True:

    for t in trucks:
        t.move()
        data = json.dumps(t.payload())
        client.publish(TOPIC, data)
        print(data)

    time.sleep(2)
