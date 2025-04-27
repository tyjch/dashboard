import streamlit as st
import pandas as pd
import numpy as np
import pytz
import plotly.express as px
from data.influx import InfluxDB
from datetime import datetime, date, time, timedelta

db = InfluxDB()

st.session_state['heatmap.time_scale'] = 'month'
ts = st.session_state.get('heatmap.time_scale', 'day')

ts_config = {
    'day': {
        'range_start' : '-1d',
        'window'      : '1h',
        'title'       : 'Temperature Heatmap (Last 24 Hours)',
        'x_title'     : 'Hour',
        'y_title'     : 'Day'
    },
    'week': {
        'range_start': '-7d',
        'window'      : '1h',
        'title'       : 'Temperature Heatmap (Last 7 Days)',
        'x_title'     : 'Hour',
        'y_title'     : 'Day'
    },
    'month': {
        'range_start': '-30d',
        'window'      : '1d',
        'title'       : 'Temperature Heatmap (Last 30 Days)',
        'x_title'     : 'Hour',
        'y_title'     : 'Day'
    }
}

range_start = ts_config[ts]['range_start']
min_temp    = st.session_state.get('settings.temperature.min', 95.0)


def get_query():
    
    def get_influx_datetime(dt):
        dt = dt.strftime("%Y-%m-%dT%H:%M:%S%z")
        return dt[:-2] + ":" + dt[-2:]

    def get_range_query(time_scale):
        start_time  = time(0, 0, 0)
        end_time    = time(23, 59, 59)
        
        start, stop = None, None
        ts = time_scale
        
        if ts == 'day':
            q = '''
        start = date.truncate(t: now(), unit: 1d)
        stop  = date.add(d: -1s, to: date.add(d: 1d, to: start))
        r     = {start: start, stop: stop}'''
        if ts == 'week':
            q = 'r = boundaries.week(start_sunday: true)'
        if ts == 'month':
            q = 'r = boundaries.month()'
        
        return f'''
        import "date"
        import "experimental/date/boundaries"
        import "timezone"
        
        option location = timezone.location(name: "America/Los_Angeles")
        {q}
        '''

    def build_query():
        window = ts_config[ts]['window']
        return get_range_query(ts) + f'''
        from(bucket: "thermometer")
            |> range(start: r.start, stop: r.stop)
            |> filter(fn: (r) => r["_measurement"] == "DS18B20")
            |> filter(fn: (r) => r["_field"] == "value")
            // |> filter(fn: (r) => float(v: r["bias"]) >= 0.0)
            |> map(fn: (r) => ({{r with raw_temp: r._value, adjusted_temp: r._value + float(v: r.bias)}}))
            // |> filter(fn: (r) => r["adjusted_temp"] >= {min_temp})
            |> drop(columns: ["bias"])
            |> aggregateWindow(every: {window}, fn: mean, createEmpty: true, column: "adjusted_temp")
            |> keep(columns: ["_start", "_stop", "_time", "adjusted_temp"])
        '''

    return build_query() 


query = get_query()
st.code(query)
try:
    df = db.run_query(query=query)
    st.dataframe(df)
except Exception as e:
    st.warning("Error running query")
    st.code(e)
    

# try:
#     df = db.run_query(query=query)
#     if df.empty:
#         st.warning("No data available for the selected time period.")
        
#     # Make sure _time column is datetime type
#     df['_time'] = pd.to_datetime(df['_time'])
    
#     # Extract time components for the heatmap
#     if ts == 'day':
#         # For daily view, group by hour and create a pivot table
#         df['hour'] = df['_time'].dt.hour
#         df['date'] = df['_time'].dt.date
        
#         # Create pivot table with hours as columns and day as rows
#         pivot_df = df.pivot_table(
#             values  = '_value', 
#             index   = 'date',
#             columns = 'hour',
#             aggfunc = 'mean'
#         )
        
#         # Only keep the most recent day if there are multiple
#         if len(pivot_df) > 1:
#             pivot_df = pivot_df.iloc[-1:, :]
            
#     elif ts == 'week':
#         # For weekly view, extract day of week and hour
#         df['day_of_week'] = df['_time'].dt.day_name()
#         df['hour'] = df['_time'].dt.hour
        
#         # Create pivot table
#         pivot_df = df.pivot_table(
#             values  = '_value',
#             index   = 'day_of_week',
#             columns = 'hour',
#             aggfunc = 'mean'
#         )
        
#         # Set proper day of week order
#         day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
#         pivot_df = pivot_df.reindex(day_order)
        
#     else:  # month
#         # For monthly view, extract day of month and hour
#         df['day_of_month'] = df['_time'].dt.day
#         df['hour'] = df['_time'].dt.hour
        
#         # Create pivot table
#         pivot_df = df.pivot_table(
#             values='_value',
#             index='day_of_month',
#             columns='hour',
#             aggfunc='mean'
#         )
    
#     # Fill missing values with NaN for better visualization
#     pivot_df = pivot_df.astype(float)
    
#     # Display time scale selection
#     time_scale_options = ['day', 'week', 'month']
#     col1, col2 = st.columns([1, 3])
    
#     with col1:
#         selected_ts = st.selectbox(
#             "Time Scale", 
#             time_scale_options,
#             index=time_scale_options.index(ts)
#         )
        
#         # Update session state if time scale changes
#         if selected_ts != ts:
#             st.session_state['heatmap.time_scale'] = selected_ts
#             st.rerun()
    
#     # Get status colors and limits from session state
#     status_keys = ['disconnected', 'cold', 'cool', 'average', 'warm', 'hot']
    
#     # Create a list of colors and values for the discrete color scale
#     colors = [st.session_state.get(f'status.{s}.color') for s in status_keys]
#     values = [float(st.session_state.get(f'status.{s}.limit')) for s in status_keys]
    
#     # Function to determine status based on temperature
#     def get_status_color(val):
#         if pd.isna(val):
#             return st.session_state.get('status.disconnected.color')
            
#         for i, s in enumerate(status_keys):
#             if val <= float(st.session_state.get(f'status.{s}.limit')):
#                 return st.session_state.get(f'status.{s}.color')
#         return st.session_state.get('status.hot.color')  # Default to hot if above all limits
    
#     # Create custom colorscale for plotly
#     # Convert status limits to normalized values between 0 and 1
#     min_val = min(values)
#     max_val = max(values)
    
#     # Normalize values for plotly colorscale (values must be between 0 and 1)
#     normalized_values = []
#     for i, val in enumerate(values):
#         if i == 0:  # Handle the first value (disconnected)
#             normalized_values.append(0)
#         elif i == len(values) - 1:  # Handle the last value (hot)
#             normalized_values.append(1)
#         else:
#             # Normalize the value between 0 and 1
#             norm_val = (val - min_val) / (max_val - min_val)
#             normalized_values.append(norm_val)
    
#     # Create the colorscale as a list of [normalized_value, color] pairs
#     colorscale = []
#     for i in range(len(colors)):
#         colorscale.append([normalized_values[i], colors[i]])
    
    
#     # Create heatmap with Plotly - with x and y axes swapped and custom colorscale
#     fig = px.imshow(
#         pivot_df.T,  # Transpose the dataframe to swap x and y
#         labels=dict(
#             # Swap x and y titles
#             x=ts_config[ts]['y_title'],
#             y=ts_config[ts]['x_title'],
#             color="Temperature (°C)"
#         ),
#         x=pivot_df.index,  # Now this becomes the x-axis
#         y=pivot_df.columns,  # Now this becomes the y-axis
#         color_continuous_scale=colorscale,  # Custom color scale
#         title=ts_config[ts]['title'],
#         zmin=min(val for val in values if val > -999),  # Set min value excluding disconnected
#         zmax=max(val for val in values if val < 999)    # Set max value excluding hot limit
#     )
    
#     # Add custom color bar ticks for each status
#     tickvals = []
#     ticktext = []
#     for i, s in enumerate(status_keys):
#         if i > 0 and i < len(status_keys) - 1:  # Skip extreme values
#             tickvals.append(float(st.session_state.get(f'status.{s}.limit')))
#             ticktext.append(s.capitalize())
    
#     fig.update_layout(
#         coloraxis_colorbar=dict(
#             title="Status",
#             tickvals=tickvals,
#             ticktext=ticktext
#         )
#     )
    
#     # Update layout for better appearance
#     fig.update_layout(
#         height=500,
#         margin=dict(l=20, r=20, t=40, b=20),
#     )
    
#     # Add custom hover template to show temperature and status
#     fig.update_traces(
#         hovertemplate="<b>%{y}</b> hour<br><b>%{x}</b><br>Temperature: %{z:.1f}°C<extra></extra>"
#     )
    
#     # Display the heatmap
#     st.plotly_chart(fig, use_container_width=True)
    
#     # Display the data table (optional)
#     with st.expander("Show Raw Data"):
#         st.dataframe(pivot_df.T.round(1))  # Also transpose the data table to match the chart
        
# except Exception as e:
#     st.error(f"Error retrieving or processing data: {e}")
#     st.code(query, language="sql")
    
