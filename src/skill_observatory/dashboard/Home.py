import streamlit as st

from skill_observatory.dashboard.skill_dashboard import render_dashboard


st.set_page_config(
    page_title="Swedish Tech Skill Observatory",
    layout="wide",
)

render_dashboard()
