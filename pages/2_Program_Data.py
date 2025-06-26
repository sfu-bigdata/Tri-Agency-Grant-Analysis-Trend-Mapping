import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from millify import millify
import  io

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
    specifc_labels = ["CIHR Fellowship", "Canada Excellence Research Chair", "Project Grant"]
elif dashboard_type == "NSERC":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "NSERC"].copy()
    specifc_labels = ["Discovery Grants Program - Individual", "Alliance Grants", "Canada Research Chairs"]
elif dashboard_type == "SSHRC":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "SSHRC"].copy()
    specifc_labels = ["Canada Research Chairs", "Research Support Fund"]


st.title(f"Program Trends for {dashboard_type}")

custom_labels = st.checkbox("Use custom labels")
if custom_labels:
    program_labels = st.multiselect('Select programs', agency_data["Program_Name"].unique(), specifc_labels)
else:
    program_labels = specifc_labels

fig = plt.figure(figsize=(12, 6))
for label in program_labels:
    grouped_label = agency_data[agency_data["Program_Name"] == label].groupby('CompetitionFY')['Total_Amount'].sum().reset_index()
    plt.plot(grouped_label['CompetitionFY'], grouped_label['Total_Amount'], label=label, marker='o')
plt.title(f"Program Trends for {dashboard_type}")
plt.ylabel("Total Funding Amount")
plt.xlabel("CompetitionFY")
plt.grid(True)
plt.legend()
st.pyplot(fig)

buf = io.BytesIO()
fig.savefig(buf, format="png")
buf.seek(0)
st.download_button(
    label="Export Plot",
    data=buf,
    file_name=f"{dashboard_type}_university_funding.png",
    mime="image/png"
)
