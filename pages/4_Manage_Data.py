import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from millify import millify
import io
import os
import subprocess

st.set_page_config(page_title="Data Management", page_icon="")

st.title("Upload Data")

# Upload CIHR Dataset
uploaded_cihr = st.file_uploader("Upload CIHR CSV Data:", type=["xlsx"])
if uploaded_cihr is not None:
    if st.button("Upload CIHR Data"):
        with open(f'./raw_data/CIHR/{uploaded_cihr.name}', 'wb') as f:
            f.write(uploaded_cihr.getbuffer())

# Display Current CIHR Files
display_cihr = st.checkbox("Display Current CIHR Files")
if display_cihr:
    files_list = []
    for file in os.listdir("./raw_data/CIHR"):
        files_list.append(file)
    st.write(files_list)

# Upload NSERC Dataset
uploaded_nserc = st.file_uploader("Upload NSERC CSV Data:", type=["csv"])
if uploaded_nserc is not None:
    if st.button("Upload NSERC Data"):
        with open(f'./raw_data/NSERC/{uploaded_nserc.name}', 'wb') as f:
            f.write(uploaded_nserc.getbuffer())

# Display Current NSERC Files
display_nserc = st.checkbox("Display Current NSERC Files")
if display_nserc:
    files_list = []
    for file in os.listdir("./raw_data/NSERC"):
        files_list.append(file)
    st.write(files_list)

# Upload SSHRC Dataset
uploaded_sshrc = st.file_uploader("Upload SSHRC CSV Data:", type=["csv"])
if uploaded_sshrc is not None:
    if st.button("Upload SSHRC Data"):
        with open(f'./raw_data/SSHRC/{uploaded_sshrc.name}', 'wb') as f:
            f.write(uploaded_sshrc.getbuffer())

# Display Current SSHRC Files
display_sshrc = st.checkbox("Display Current SSHRC Files")
if display_sshrc:
    files_list = []
    for file in os.listdir("./raw_data/SSHRC"):
        files_list.append(file)
    st.write(files_list)

# Delete a File
st.title("Delete Data")
select_agency = st.selectbox("Select Agency:", [None, "CIHR", "NSERC", "SSHRC"])
# After selecting an agency, display the files in that agency's folder
if select_agency: 
    files_list = []
    for file in os.listdir(f"./raw_data/{select_agency}"):
        files_list.append(file)
    
    # Select a file to delete, display a delete button
    select_file = st.selectbox("Select File to Delete:", files_list)
    if st.button(f"Delete {select_file} File"):
        os.remove(f"./raw_data/{select_agency}/{select_file}")

st.title("Update Data")

# Select range of years for Cleaning
col1, col2 = st.columns(2)
with col1:
    start_year = st.number_input('Select start Year', value=2019, step=1)
with col2:
    end_year = st.number_input('Select end year:', value=2023, step=1)

# Re-run cleaning script w/ selected years
if st.button("Update Data"): 
    subprocess.run(['python', 'clean_data.py', str(start_year), str(end_year)])
