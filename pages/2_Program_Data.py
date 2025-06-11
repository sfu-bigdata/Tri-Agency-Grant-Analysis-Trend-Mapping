import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from millify import millify

st.set_page_config(page_title="Program Data", page_icon="")

U15 = ["University of Alberta", "University of British Columbia", "University of Calgary", "Dalhousie University", "Université Laval", 
       "University of Manitoba", "McGill University", "McMaster University", "Université de Montréal", "University of Ottawa", 
       "Queen's University", "University of Saskatchewan", "University of Toronto", "University of Waterloo", "University of Western Ontario"]

U15 = ["University of Alberta", "University of British Columbia", "University of Calgary", "Dalhousie University", "Université Laval", 
       "University of Manitoba", "McGill University", "McMaster University", "Université de Montréal", "University of Ottawa", 
       "Queen's University", "University of Saskatchewan", "University of Toronto", "University of Waterloo", "University of Western Ontario",
       "University of Victoria"] # U15 + UVic

# Load and clean data
TRIAGENCY_DATA = pd.read_csv("clean_data/TRIAGENCY_DATA.csv")
U15_DATA = TRIAGENCY_DATA[TRIAGENCY_DATA["Institution"].isin(U15)]
SFU_DATA = TRIAGENCY_DATA[TRIAGENCY_DATA["Institution"] == "Simon Fraser University"]

dashboard_type = st.selectbox("Select Agency:", ["CIHR", "NSERC", "SSHRC"])

if dashboard_type == "CIHR":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "CIHR"].copy()
elif dashboard_type == "NSERC":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "NSERC"].copy()
elif dashboard_type == "SSHRC":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "SSHRC"].copy()
    agency_data["Program_Type"] = agency_data["Program_Name"] # Temporary Fix as SSHRC doesn't have Program_Type

st.title(f"Program Trends for {dashboard_type}")

program_revenue = agency_data.groupby("Program_Type")['Total_Amount'].sum().nlargest(10).reset_index()
custom_labels = st.checkbox("Use custom labels")
if custom_labels:
    program_labels = st.multiselect('Select programs', sorted(program_revenue["Program_Type"].unique()), program_revenue["Program_Type"].unique())
else:
    program_labels = sorted(program_revenue["Program_Type"].unique())

fig = plt.figure(figsize=(12, 6))
for label in program_labels:
    grouped_label = agency_data[agency_data["Program_Type"] == label].groupby('CompetitionFY')['Total_Amount'].sum().reset_index()
    plt.plot(grouped_label['CompetitionFY'], grouped_label['Total_Amount'], label=label, marker='o')
plt.title(f"Program Trends for {dashboard_type}")
plt.ylabel("Total Funding Amount")
plt.xlabel("CompetitionFY")
plt.grid(True)
plt.legend()

st.pyplot(fig)
