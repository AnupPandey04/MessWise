import os
import streamlit as st

try:
    MONGO_URI = st.secrets["MONGO_URI"]
except (KeyError, FileNotFoundError):
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

DATABASE_NAME = "messwise_db"
