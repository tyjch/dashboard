import streamlit as st
import pandas as pd
import pytz
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from data.influx import InfluxDB
from datetime import date, datetime, time, timedelta, timezone
from streamlit_autorefresh import st_autorefresh

count = st_autorefresh(interval=10000, key='refresh_count')

db = InfluxDB()


def get_influx_data():
  def get_aggregate_window():
    scalar = st.session_state.get('aggregation.scalar')
    period = st.session_state.get('aggregation.period')
    return f"{scalar}{period}"
  
  def get_datetime_range():
    session_stop = st.session_state.get('filters.date.stop')
    session_start = st.session_state.get('filters.date.start')
    
    tz = pytz.timezone('America/Los_Angeles')
    
    # Set specific times for start and end of day in local time
    start = datetime.combine(session_start, time(0, 0, 0)).replace(tzinfo=tz)
    stop = datetime.combine(session_stop, time(23, 59, 59)).replace(tzinfo=tz)
    
    # Format with timezone offset for Flux
    start_str = start.strftime("%Y-%m-%dT%H:%M:%S%z")
    stop_str = stop.strftime("%Y-%m-%dT%H:%M:%S%z")
    
    # Add colon in timezone offset as required by RFC3339
    start_str = start_str[:-2] + ":" + start_str[-2:]
    stop_str = stop_str[:-2] + ":" + stop_str[-2:]
    
    return start_str, stop_str
  
  start_str, stop_str = get_datetime_range()
  
  query = f'''
  from(bucket: "thermometer") 
    |> range(start: {start_str}, stop: {stop_str}) 
    |> aggregateWindow(every: {get_aggregate_window()}, fn: mean, createEmpty: false) 
    |> yield(name: "data")
  '''
  
  return db.run_query(query)


st.session_state.data = get_influx_data()
  
def temperature_metric():
  baseline_temp = st.session_state.get('settings.temperature.baseline', 97.5)
  # TODO: Filter and remove bias
  query = '''
  from(bucket: "thermometer")
    |> range(start: -7d, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "DS18B20")
    |> filter(fn: (r) => r["dimension"] == "temperature")
    |> filter(fn: (r) => r["unit"] == "degree_fahrenheit")
    |> filter(fn: (r) => r["_field"] == "value")
    |> filter(fn: (r) => r["sensor_id"] == "28-3c01f09622a2")
    |> map(fn: (r) => ({r with raw_temp: r._value, adjusted_temp: r._value + float(v: r.bias)}))
    |> drop(columns: ["bias"])
    |> last()
  '''
  df = db.run_query(query)
  current_temp = float(df['adjusted_temp'].iloc[-1])
  
  return st.metric(
    label = 'Current Temperature',
    value = f'{current_temp:.1f} °F',
    delta = f'{current_temp-baseline_temp:.1f} °F'
  )

def last_measurement_metric():
  query = '''
  from(bucket: "thermometer")
    |> range(start: -7d, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "DS18B20")
    |> filter(fn: (r) => r["dimension"] == "temperature")
    |> filter(fn: (r) => r["unit"] == "degree_fahrenheit")
    |> filter(fn: (r) => r["_field"] == "value")
    |> filter(fn: (r) => r["sensor_id"] == "28-3c01f09622a2")
    |> map(fn: (r) => ({r with raw_temp: r._value, adjusted_temp: r._value + float(v: r.bias)}))
    |> drop(columns: ["bias"])
    |> last()
  '''
  df = db.run_query(query)
  df
  
  if not df.empty:
    last_time = pd.to_datetime(df['_time'].iloc[-1])
    now = datetime.now(timezone.utc)
    
    if last_time > now:
      text = "Just now"
    else:
      delta = now - last_time
      total_seconds = delta.total_seconds()
      
      if total_seconds < 60:
        text = "Just now"
      elif total_seconds < 3600:
        text = f"{int(total_seconds // 60)}m ago"
      elif total_seconds < 86400:
        text = f"{int(total_seconds // 3600)}h ago"
      else:
        text = f"{int(total_seconds // 86400)}d ago"
    
    return st.metric(
      label = 'Last Measured',
      value = text
    )
  else:
    return st.metric(
      label = 'Last Measured',
      value = 'Unknown'
    )
  
# # TODO
# def temperature_state_metric():
#   pass

# # TODO
# def device_status_metric():
#   pass

def metrics():
  c1, c2 = st.columns(2, vertical_alignment='top')
  with c1:
    temperature_metric()
  with c2:
    last_measurement_metric()


st.header("Temperature Analysis")

metrics()


