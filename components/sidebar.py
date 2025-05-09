from datetime import date, datetime, time, timedelta
from functools import partial
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from data.influx import InfluxDB
import streamlit as st
import config


def date_range():
    stop  = datetime.now()
    start = stop - timedelta(days=7)
    start_col, stop_col = st.columns([1, 1])
    
    with start_col:
        start_date = st.date_input(
            key       = 'filters.date.start',
            label     = 'Start Date',
            value     = start,
            max_value = 'today',
            format    = 'MM/DD/YYYY',
            label_visibility = 'visible',
        )
        
    with stop_col:
        stop_date = st.date_input(
            key       = 'filters.date.stop',
            label     = 'Stop Date',
            value     = stop,
            max_value = 'today',
            format    = 'MM/DD/YYYY',
            label_visibility = 'visible'
        )
    
def temperature_range():
    return st.slider(
        key       = 'filters.temperature',
        label     = 'Temperature Range',
        value     = (95, 100),
        min_value = 80,
        max_value = 110,
        label_visibility = 'visible'
    )

def filters():
    st.header('Filters')
    date_range()
    temperature_range()
    
def aggregation_window():
    st.header('Aggregation Window')
    scalar_col, period_col = st.columns(2, vertical_alignment='center')
    
    with scalar_col:
        st.number_input(
            key       = 'aggregation.scalar',
            label     = 'Scalar',
            value     = 5,
            min_value = 1,
            max_value = 120,
            step      = 5,
            label_visibility = 'visible'
        )
    
    with period_col:
        st.selectbox(
            key     = 'aggregation.period',
            label   = 'Period',
            options = ['s', 'm', 'h', 'd'],
            index   = 1,
            label_visibility = 'visible'
        )
    
def status_settings():
    st.write(config.INFLUX_URL)
    client = InfluxDBClient(
        url   = 'https://influx.tyjch.dev',
        token = '0OeQuTI0APEe-XeD305hg3wzdONljk85XLjt57lmkj2SoX8ieOPK3m4lScmWpWW8qieLDnmwZHI_CwRPlWK-Gw==',
        org   = 'AspenCircle',
    )
    
    def on_change(state):
        limit = st.session_state.get(f'status.{state}.limit')
        point = Point('Threshold').tag(
            'state', state
        ).field('limit', round(limit, 2))
        
        write_api = client.write_api(write_options=SYNCHRONOUS)
        write_api.write(
            bucket = config.INFLUX_BUCKET,
            org    = config.INFLUX_ORG,
            record = point
        )
        
    status_defaults = {
        'disconnected' : {'color': '#969696', 'maximum': 95.0,  'icon': ':material/power_off:'},
        'cold'         : {'color': '#3278dc', 'maximum': 96.5,  'icon': ':material/severe_cold:'},
        'cool'         : {'color': '#82b4ff', 'maximum': 97.0,  'icon': ':material/mode_cool:'},
        'average'      : {'color': '#ffffff', 'maximum': 98.5,  'icon': ':material/mode_heat_cool:'},
        'warm'         : {'color': '#ffaa82', 'maximum': 99.0,  'icon': ':material/mode_heat:'},
        'hot'          : {'color': '#ff825a', 'maximum': 999.0, 'icon': ':material/emergency_heat:'}
    }
    
    query = f'''
    from(bucket: "{config.INFLUX_BUCKET}")
        |> range(start: -30d, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "Threshold")
        |> filter(fn: (r) => r["_field"] == "limit")
        |> last()
        |> keep(columns: ["state", "_value"])
    '''
    query_api = client.query_api()
    df = query_api.query_data_frame(query=query)
    
    if not df.empty:
        def process_row(row):
            state = row['state']
            limit = row['_value']
            st.session_state[f'status.{state}.limit'] = limit
        df.apply(process_row, axis=1)
  
    with st.container(border=False):
        st.subheader('Status Settings')
        
        for name, settings in status_defaults.items():
            with st.expander(name.capitalize(), icon=settings.get('icon')):
                color_col, limit_col = st.columns(2)
                
                with color_col:
                    selected_color = st.color_picker(
                        key              = f"status.{name}.color",
                        label            = 'Color',
                        value            = settings.get('color'),
                        label_visibility = 'visible'
                    )
                
                with limit_col:
                    selected_limit = st.number_input(
                        key              = f'status.{name}.limit',
                        label            = 'Upper Limit',
                        value            = st.session_state[f'status.{name}.limit'],
                        step             = 0.1,
                        format           = '%0.1f',
                        label_visibility = 'visible',
                        disabled         = True if name == 'Hot' else False,
                        on_change        = on_change,
                        kwargs           = {'state': name}
                    )

def settings():
    with st.expander('Settings', icon=':material/settings:'):
        min_temp = st.number_input(
            key    = 'settings.temperature.min',
            label  = 'Minimum Temperature',
            value  = 95.0,
            step   = 0.1,
            format = '%0.1f',
            label_visibility = 'visible'
        )
        
        base_temp = st.number_input(
            key    = 'settings.temperature.baseline',
            label  = 'Baseline Temperature',
            value  = 97.5,
            step   = 0.1,
            format = '%0.1f',
            label_visibility = 'visible'
        )
        
        #st.subheader('Auto-Refresh')
        #st.subheader('Notifications')

def sidebar():
    with st.sidebar:
        filters()
        aggregation_window()
        # status_settings()
        settings()
