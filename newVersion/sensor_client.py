import requests
import time
import random
import time
import RPi.GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

SERVER_URL = "http://10.208.48.165:5000"
RPI_ID = "rpi-001"

def get_city():
    try:
        resp = requests.get("https://ipinfo.io")
        if resp.status_code == 200:
            data = resp.json()
            return data.get("city", "Unknown")
        else:
            print(f"Failed to get location, status code {resp.status_code}")
            return "Unknown"
    except Exception as e:
        print(f"Error getting location: {e}")
        return "Unknown"

def read_light_sensor(mcp):
    lux_threshold = 80
    readings = []

    for i in range(2):
        lux = mcp.read_adc(0)
        readings.append(lux)
        print(lux)
        time.sleep(0.1)

    avg_lux = sum(readings) // len(readings)

    if avg_lux > lux_threshold:
        print("Bright")
    else:
        print("Dark")

    return avg_lux

def read_twists(mcp): 
    total_twists = 0
    last_twist = snd = mcp.read_adc(1)
    while total_twists < 500:
        snd = mcp.read_adc(1)
        print(snd)
        time.sleep(1)
        total_twists += abs(last_twist - snd)

    # not sure if needed
    if total_twists > 500:
      GPIO.output(11, GPIO.HIGH)
      time.sleep(0.1)
      GPIO.output(11, GPIO.LOW)
    return True


def main():
    # CODE FROM THE LIGHT SENSOR LAB
    #using physical pin 11 to blink an LED
    GPIO.setmode(GPIO.BOARD)
    chan_list = [11]
    GPIO.setup(chan_list, GPIO.OUT)
    # Hardware SPI configuration:
    SPI_PORT   = 0
    SPI_DEVICE = 0
    mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
    
    CITY = get_city()
    print(f"[RPI] Detected city: {CITY}")

    while True:
        light_value = read_light_sensor(mcp)
        print(f"[RPI] Light reading: {light_value}")

        try:
            if read_twists(mcp):
                # send light
                resp = requests.post(f"{SERVER_URL}/update_light", json={
                    "rpi_id": RPI_ID,
                    "light": light_value,
                    "city": CITY
                })
                if resp.status_code == 200:
                    print("[RPI] Light and city updated successfully.")
                else:
                    print(f"[RPI] Failed to update: {resp.status_code}")


                print("Sending gamble request...")
                # send 
                resp = requests.post(f"{SERVER_URL}/gamble", json={
                    "rpi_id": RPI_ID,
                    "light": light_value,
                    "city": CITY
                })
                if resp.status_code == 200:
                    print("[RPI] Gambled successfully.")
                else: 
                    print(f"[RPI] Failed to gamble: {resp.status_code}")
        except Exception as e:
            print(f"[RPI] Error: {e}")

        time.sleep(0.1)

if __name__ == "__main__":
    main()
