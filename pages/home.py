import streamlit as st
import pandas as pd
import pytz
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from data.influx import InfluxDB
from datetime import date, datetime, time, timedelta, timezone
from streamlit_autorefresh import st_autorefresh
from components.metrics import latest_temperature_metric, last_measurement_metric

#count = st_autorefresh(interval=20000, key='refresh_count')

db = InfluxDB()


def get_influx_data():
  def get_aggregate_window():
    scalar = st.session_state.get('aggregation.scalar')
    period = st.session_state.get('aggregation.period')
    return f"{scalar}{period}"
  
  def get_datetime_range():
    session_stop  = st.session_state.get('filters.date.stop')
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


# st.session_state.data = get_influx_data()

def line_chart():
  query = f'''
    import "math"
    
    roundFloat = (value, places) => {{
      multiplier = math.pow10(n: places)
      return math.round(x: value * multiplier) / multiplier 
    }}

    bias = from(bucket: "thermometer")
      |> range(start: -1h, stop: now())
      |> filter(fn: (r) => r["_measurement"] == "DS18B20")
      |> filter(fn: (r) => r["_field"] == "bias")
      |> keep(columns: ["_time", "_value", "sensor_id", "unit"])
      |> rename(columns: {{_value: "bias_value"}})
      
    temperature = from(bucket: "thermometer")
      |> range(start: -1h, stop: now())
      |> filter(fn: (r) => r["_measurement"] == "DS18B20")
      |> filter(fn: (r) => r["_field"] == "temperature")
      |> keep(columns: ["_time", "_value", "sensor_id", "unit"])
      |> rename(columns: {{_value: "temperature_value"}})
      
    // Join and create the combined value
    join(
      tables : {{bias: bias, temperature: temperature}},
      on     : ["_time", "sensor_id", "unit"]
    )
    |> map(fn: (r) => ({{
        _time     : r._time,
        _value    : roundFloat(value: r.bias_value + r.temperature_value, places: 1),
        sensor_id : r.sensor_id,
        unit      : r.unit
    }}))
    // |> difference()
    |> derivative(unit: 1m, nonNegative: false, columns: ["_value"], timeColumn: "_time")
  '''
  df = db.run_query(query=query)
  st.code(len(df))
  st.dataframe(df.head())
  
  st.line_chart(data=df, x='_time', y='_value')
  

def connection_state(
  measurement            : str = 'DS18B20',
  time_range             : str = '-24h',
  derivative_window      : str = '5s',
  connected_threshold    : int = 2,
  disconnected_threshold : int = -1  
):
  db = InfluxDB()
  
  
  
  query = f'''
  import "math"
  
  data = from(bucket: "thermometer")
    |> range(start: -24h, stop: now())
    |> filter(fn: (r) => r._measurement == "{measurement}")
    |> filter(fn: (r) => r._field == "temperature")
    
  derivatives = data
    |> derivative(unit: {derivative_window})
    |> map(fn: (r) => ({{
      _time      : r._time,
      derivative : r._value,
      magnitude  : math.abs(x: r._value)
    }}))
    |> filter(fn: (r) => r.magnitude > 0)
    |> tail(n: 500)
    
  joined = join(
    tables: {{
      data: data,
      derivatives: derivatives
    }},
    on: ["_time"]
  )
    |> map(fn: (r) => ({{r with direction: 
      if r.derivative > 0 then "positive"
      else if r.derivative < 0 then "negative"
      else " "
      }}))
    |> stateTracking(fn: (r) => r.direction == "positive", countColumn: "positiveCount")
    |> stateTracking(fn: (r) => r.direction == "negative", countColumn: "negativeCount")
    |> map(fn: (r) => ({{r with count: math.mMax(x: float(v: r.positiveCount), y: float(v: r.negativeCount))}}))
    |> yield(name: "joined")
  
  '''

  
  
  query = query
  st.code(query, line_numbers=True)
  df = db.run_query(query=query)
  
  st.line_chart(
    data = df,
    x    = "_time",
    y    = ["derivative", "_value"]
  )
  st.dataframe(df)
  
  
  

  


st.header("Temperature Analysis")

c1, c2 = st.columns(2, vertical_alignment='top')
with c1:
  latest_temperature_metric()
with c2:
  last_measurement_metric()
  
connection_state()