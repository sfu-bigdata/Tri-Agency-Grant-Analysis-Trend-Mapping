import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from millify import millify
import io
# import os
import subprocess


st.set_page_config(page_title="Data Management", page_icon="")

st.write("Add SSHRC data here")
uploaded_sshrc = st.file_uploader("Choose a CSV or Excel file to upload:", type=["csv"])

st.write("Add NSERC data here")
uploaded_nserc = st.file_uploader("Choose a CSV or Excel file to upload:", type=["csv"])

st.write("Add CIHR data here")
uploaded_cihr = st.file_uploader("Choose a CSV or Excel file to upload:", type=["csv"])

if uploaded_sshrc is not None:
    if st.button("Upload SSHRC Data"):

        with open(f'./raw_data/{uploaded_sshrc.name}', 'wb') as f:
            f.write(uploaded_sshrc.getbuffer())

if uploaded_nserc is not None:
    if st.button("Upload NSERC Data"):

        with open(f'./raw_data/{uploaded_nserc.name}', 'wb') as f:
            f.write(uploaded_nserc.getbuffer())

if uploaded_cihr is not None:
    if st.button("Upload CIHR Data"):
        
        with open(f'./raw_data/{uploaded_cihr.name}', 'wb') as f:
            f.write(uploaded_cihr.getbuffer())

# Create a button to run another Python script for data update/cleaning
if st.button("Update Data"):
    subprocess.run(['ipython', '-c', 'clean_data.ipynb'])
