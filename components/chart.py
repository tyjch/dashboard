from abc import ABC, abstractmethod, abstractproperty
from data.influx import InfluxDB
from config import INFLUX_BUCKET

class Chart:
  
  def __init__(self):
    self.db     = InfluxDB()
    self.bucket = INFLUX_BUCKET
  
  @abstractproperty
  def query(self):
    pass
  
  @property
  def dataframe(self):
    return self.db.run_query(self.query) 
  
  @abstractmethod
  def show(self):
    pass
  
  # def get_influx_datetime(dt):
  #   dt = dt.strftime("%Y-%m-%dT%H:%M:%S%z")
  #   return dt[:-2] + ":" + dt[-2:]


    