import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

#st.header("Settings")


def status_color():
  status_defaults = {
    'Off'     : {'color': '#969696', 'maximum': 95.0},
    'Cold'    : {'color': '#3278dc', 'maximum': 96.5},
    'Cool'    : {'color': '#82b4ff', 'maximum': 97.0},
    'Average' : {'color': '#ffffff', 'maximum': 98.5},
    'Warm'    : {'color': '#ffaa82', 'maximum': 99.0},
    'Hot'     : {'color': '#ff825a', 'maximum': 999.0}
  }
  
  with st.container(border=False):
    st.subheader('Temperature States')
    
    for name, settings in status_defaults.items():
      color = settings.get('color')
      limit = settings.get('maximum')
      
      with st.expander(name):
        color_col, limit_col = st.columns(2)
        
        with color_col:
          selected_color = st.color_picker(
          label            = 'Color',
          key              = f"color_{name}",
          value            = color, 
          label_visibility = 'visible'
        )
          
        with limit_col:
          selected_limit = st.number_input(
          label            = 'Upper Limit',
          key              = f'status_{name}',
          value            = limit,
          step             = 0.1,
          format           = '%0.1f',
          label_visibility = 'visible',
          disabled         = True if name == 'Hot' else False
        )
        
  
      
      
     
  



col1, col2 = st.columns(2, gap='large')

with col1:
  st.subheader('Minimum Temperature')
  min_temp = st.number_input(
    key    = 'minimum_temp',
    label  = 'Readings below this value will not be counted as valid; the device is powered but either the sensor is misplaced or it is still acclimating to body temperature.',
    value  = 95.0,
    step   = 0.1,
    format = '%0.1f',
    label_visibility = 'visible'
  )
  st.session_state.min_temp = min_temp
  
  st.subheader('Baseline Temperature')
  base_temp = st.number_input(
    key    = 'baseline_temp',
    label  = 'Set this to be around "average" body temperature. We can use this to display how far above or below sensor readings are from this value.',
    value  = 97.5,
    step   = 0.1,
    format = '%0.1f',
    label_visibility = 'visible'
  )
  st.session_state.base_temp = base_temp
  
  st.subheader('Auto-Refresh')
  st.subheader('Notifications')
  
  
  
with col2:
  status_color()