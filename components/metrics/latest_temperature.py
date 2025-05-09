import streamlit as st
import pandas as pd
import pytz
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from data.influx import InfluxDB
from datetime import date, datetime, time, timedelta, timezone
from streamlit_autorefresh import st_autorefresh


def latest_temperature_metric():
  baseline_temp = st.session_state.get('settings.temperature.baseline', 97.5)
  query = '''
  bias = from(bucket: "thermometer")
    |> range(start: -1w, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "DS18B20")
    |> filter(fn: (r) => r["_field"] == "bias")
    |> sort(columns: ["_time"])
    |> last()
    |> keep(columns: ["_time", "_value", "sensor_id", "unit"])
    |> rename(columns: {_value: "bias_value"})
  temperature = from(bucket: "thermometer")
    |> range(start: -1w, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "DS18B20")
    |> filter(fn: (r) => r["_field"] == "temperature")
    |> sort(columns: ["_time"])
    |> last()
    |> keep(columns: ["_time", "_value", "sensor_id", "unit"])
    |> rename(columns: {_value: "temperature_value"})
  join(
    tables : {bias: bias, temperature: temperature},
    on     : ["_time", "sensor_id", "unit"]
  )
  |> map(fn: (r) => ({
      _time                 : r._time,
      bias                  : r.bias_value,
      temperature           : r.temperature_value,
      temperature_biased    : r.bias_value + r.temperature_value,
      sensor_id             : r.sensor_id,
      unit                  : r.unit
  }))
  '''
  db = InfluxDB()
  df = db.run_query(query)
  
  current_temp = float(df['temperature_biased'].iloc[-1]) or 0.0
  return st.metric(
    label = 'Latest Temperature',
    value = f'{current_temp:.1f} °F',
    delta = f'{current_temp-baseline_temp:.1f} °F'
  )