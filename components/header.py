import streamlit as st
from datetime import datetime

def header():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Temperature Monitoring Dashboard")
    