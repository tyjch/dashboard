import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from components.chart import Chart

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

time_scales = ['day', 'week', 'month']
time_scale = st.segmented_control(
    key     = 'heatmap.time_scale',
    label   = 'Time Scale',
    options = time_scales,
    default = time_scales[-1]
)

weekday_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
weekday_abbr  = [weekday[:3] for weekday in weekday_order]
weekday_map   = dict(zip(weekday_order, weekday_abbr))


class Heatmap(Chart):
    
    def __init__(self):
        super().__init__()
        self.time_scale = st.session_state.get('heatmap.time_scale', 'month')
        self.min_temp   = st.session_state.get('settings.temperature.min', 95.0)
        self.window     = ts_config[self.time_scale]['window'] or '-1mo'
        
    @property
    def query(self):
     
        def get_range_query():
            if self.time_scale == 'day':
                q = '''
                start = date.truncate(t: now(), unit: 1d)
                stop  = date.add(d: -1s, to: date.add(d: 1d, to: start))
                r     = {start: start, stop: stop}
                '''
            elif self.time_scale == 'week':
                q = 'r = boundaries.week(start_sunday: true)'
            elif self.time_scale == 'month':
                q = 'r = boundaries.month()'
            else:
                q = ''
    
            return f'''
            import "date"
            import "experimental/date/boundaries"
            import "timezone"
            option location = timezone.location(name: "America/Los_Angeles") \n {q}
            '''
        
        return get_range_query() + f'''
        weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        months   = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        from(bucket: "{self.bucket}")
            |> range(start: r.start, stop: r.stop)
            |> filter(fn: (r) => r["_measurement"] == "DS18B20")
            |> filter(fn: (r) => r["_field"] == "value")
            // |> filter(fn: (r) => float(v: r["bias"]) >= 0.0)
            |> map(fn: (r) => ({{r with raw_temp: r._value, adjusted_temp: r._value + float(v: r.bias)}}))
            // |> filter(fn: (r) => r["adjusted_temp"] >= {self.min_temp})
            |> drop(columns: ["bias"])
            |> aggregateWindow(every: {self.window}, fn: mean, createEmpty: true, column: "adjusted_temp")
            |> keep(columns: ["_start", "_stop", "_time", "adjusted_temp"])
            |> map(fn: (r) => ({{
                r with 
                    hour     : date.hour(t: r._time),
                    month    : months[date.month(t: r._time)],
                    weekday  : weekdays[date.weekDay(t: r._time)],
                    day      : date.monthDay(t: r._time)
                }}))
            |> map(fn: (r) => ({{
                r with week: date.week(t: r._time)
            }}))
            |> map(fn: (r) => ({{
                r with state:
                    if r.adjusted_temp < {st.session_state.get('status.disconnected.limit')} then
                        "Disconnected"
                    else if r.adjusted_temp < {st.session_state.get('status.cold.limit')} then
                        "Cold"
                    else if r.adjusted_temp < {st.session_state.get('status.cool.limit')} then
                        "Cool"
                    else if r.adjusted_temp < {st.session_state.get('status.average.limit')} then
                        "Average"
                    else if r.adjusted_temp < {st.session_state.get('status.warm.limit')} then
                        "Warm"
                    else if r.adjusted_temp < {st.session_state.get('status.hot.limit')} then
                        "Hot"
                    else
                        ""
            }}))
        '''
    
    @property
    def title(self):
        return f'Heatmap ({self.time_scale.capitalize()})'

    def create_figure(self):
        reverse_scale = True
        fig = go.Figure(data=go.Heatmap(
            x = self.x,
            y = self.y,
            z = self.z,
            reversescale = reverse_scale
        ))
        fig.update_layout(
            title = self.title
        )
        return fig
    
    def show(self):
        df  = self.dataframe
        fig = self.create_figure()
        st.plotly_chart(
            figure_or_data      = fig, 
            use_container_width = True
        )










try:
    heatmap = Heatmap()
    heatmap.show()
except Exception as e:
    st.error(f"Error generating heatmap: {str(e)}")