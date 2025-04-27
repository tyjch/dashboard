import os
from dotenv import load_dotenv

load_dotenv()

INFLUX_URL    = os.getenv("INFLUX_URL")
INFLUX_TOKEN  = os.getenv("INFLUX_TOKEN")
INFLUX_ORG    = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")

REFRESH_INTERVAL   = int(os.getenv("REFRESH_INTERVAL", "60"))  # Seconds
DATE_RANGE_DEFAULT = os.getenv("DATE_RANGE_DEFAULT", "24h")  # Default time range
TEMPERATURE_UNIT   = os.getenv("TEMPERATURE_UNIT", "fahrenheit")

DEBUG = os.getenv("DEBUG", "False").lower() == "true"