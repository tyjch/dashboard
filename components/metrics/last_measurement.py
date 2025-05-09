import streamlit as st
import pandas as pd
import pytz
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from data.influx import InfluxDB
from datetime import date, datetime, time, timedelta, timezone
from streamlit_autorefresh import st_autorefresh


def last_measurement_metric():
  query = '''
  from(bucket: "thermometer")
    |> range(start: -7d, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "DS18B20")
    |> filter(fn: (r) => r["_field"] == "temperature")
    |> filter(fn: (r) => r["sensor_id"] == "28-3c01f09622a2")
    |> drop(columns: ["bias"])
    |> sort(columns: ["_time"])
    |> last()
  '''
  
  db = InfluxDB()
  df = db.run_query(query)
  
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