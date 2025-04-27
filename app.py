import streamlit as st
from components.sidebar import sidebar
from components.header import header
from components.footer import footer


st.set_page_config(
    page_title            = "Temperature Monitoring Dashboard",
    page_icon             = "🌡️",
    initial_sidebar_state = "expanded"
)

def navigation():
    return st.navigation(
        pages = [
            st.Page(title='Home', page='pages/home.py'), 
            st.Page(title='Settings', page='pages/settings.py'),
            st.Page(title='Heatmap', page='pages/heatmap.py'),
        ],
        position = 'sidebar',
        expanded = True
    )
    


current_page = navigation()

sidebar()
current_page.run()
footer()