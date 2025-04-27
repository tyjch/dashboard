import os, warnings
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
from influxdb_client.client.warnings import MissingPivotFunction

load_dotenv()
warnings.simplefilter("ignore", MissingPivotFunction)

class InfluxDB:
  def __init__(self, bucket=None):
    self.bucket = bucket or os.getenv('INFLUX_BUCKET')
    self.client = InfluxDBClient(
      url   = os.getenv('INFLUX_URL'),
      token = os.getenv('INFLUX_TOKEN'),
      org   = os.getenv('INFLUX_ORG')
    )
    self.api = self.client.query_api()
  
  @property
  def start(self):
    return (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')  # Try 7 days instead of 1
  
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
    data = self.api.query_data_frame(query=query)
    return data