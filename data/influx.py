import os, warnings
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
from influxdb_client.client.warnings import MissingPivotFunction
from loguru import logger


load_dotenv()
warnings.simplefilter("ignore", MissingPivotFunction)

class InfluxDB:
  def __init__(self, bucket=None):
    logger.debug(os.getenv('INFLUX_URL'))
    self.bucket = bucket or os.getenv('INFLUX_BUCKET')
    self.client = InfluxDBClient(
      url   = os.getenv('INFLUX_URL'),
      token = os.getenv('INFLUX_TOKEN'),
      org   = os.getenv('INFLUX_ORG')
    )
    self.api = self.client.query_api()
  
  @property
  def start(self):
    return (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
  
  @property
  def end(self):
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
  
  def process_data(self, df):
    if isinstance(df, list) and df:
      df = pd.concat(df)
    if df.empty:
      return df
    processed = df.copy()
    if '_value' in df.columns:
      processed = processed.rename(columns={'_value': 'temperature', '_time': 'timestamp'})
    if '_time' in df.columns:
      processed['timestamp'] = pd.to_datetime(processed['timestamp'])
    return processed
  
  def get_data(self, start=None, end=None, measurement='DS18B20', dimension='temperature', field='value'):
    start_time = start or self.start
    end_time   = end or self.end
    
    query = f'''
    from(bucket: "{self.bucket}")
        |> range(start: {start_time}, stop: {end_time})
        |> filter(fn: (r) => r["_measurement"] == "{measurement}")
        |> filter(fn: (r) => r["dimension"] == "{dimension}")
        |> filter(fn: (r) => r["_field"] == "{field}")
    '''
    
    data = self.api.query_data_frame(query=query)
    return self.process_data(data)

  def run_query(self, query:str):
    try:
      data = self.api.query_data_frame(query=query)
      return data
    except Exception as e:
      logger.error(e)
      raise e
  
if __name__ == '__main__':
  db = InfluxDB()
  
  query = '''
  from(bucket: "thermometer")
    |> range(start: -1h, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "DS18B20")
    |> filter(fn: (r) => r["_field"] == "temperature")
    |> keep(columns: ["_time", "_value", "sensor_id", "unit"])
    |> rename(columns: {_value: "temperature_value"})
  '''
  
  df = db.run_query(query=query)
  logger.debug(df.head())
  
  # client = db.client

  # delete_api = client.delete_api()


  # tz = pytz.timezone('America/Los_Angeles')
  # stop      = datetime.utcnow()
  # start     = (stop - timedelta(days=2))
  # stop_str  = stop.strftime("%Y-%m-%dT%H:%M:%SZ")
  # start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")

  # print(start_str)
  # print(stop_str)

  # delete_api.delete(
  #     start  = start,
  #     stop   = stop,
  #     bucket = db.bucket
  # )

  # client.close()