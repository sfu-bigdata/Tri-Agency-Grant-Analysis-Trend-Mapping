import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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
    specifc_labels = ["Project Grant"] # Many Operating Grant types
elif dashboard_type == "NSERC":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "NSERC"].copy()
    specifc_labels = ["Discovery Grants Program - Individual", "Alliance Grants"]
elif dashboard_type == "SSHRC":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "SSHRC"].copy()
    specifc_labels = ["Insight Development Grant", "Insight Grants", "Partnership Grants"]


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
plt.xticks(agency_data["CompetitionFY"].unique())
plt.grid(True)
plt.legend()
st.pyplot(fig)

buf = io.BytesIO()
fig.savefig(buf, format="png", bbox_inches="tight")
buf.seek(0)
st.download_button(
    label="Export Plot",
    data=buf,
    file_name=f"{dashboard_type}_university_funding.png",
    mime="image/png"
)

st.title(f"Heatmap of Market Share for {dashboard_type}")
fig, ax = plt.subplots(figsize=(12, 6))
heatmap_data = agency_data[(agency_data["Program_Name"].isin(program_labels)) & (agency_data['Institution'].isin(["Simon Fraser University"] + U15))].groupby(['Program_Name', 'Institution'])['Total_Amount'].sum().reset_index()
sns.heatmap(heatmap_data.pivot_table(index='Program_Name', columns='Institution', values='Total_Amount', aggfunc='sum'), cmap="YlGnBu")
plt.title(f"Heatmap of Program Market Share for {dashboard_type}")
st.pyplot(fig)

st.title(f"Program Market Share for {dashboard_type}")

university = st.selectbox("Select University:", ["Simon Fraser University"] + U15)

fig = plt.figure(figsize=(12, 6))
for label in program_labels:
    program_data = agency_data[(agency_data["Program_Name"] == label) & (agency_data['Institution'] == university)]
    market_share = (program_data.groupby('CompetitionFY')['Total_Amount'].sum() / agency_data[(agency_data["Program_Name"] == label)].groupby('CompetitionFY')['Total_Amount'].sum()).reset_index()
    plt.plot(market_share['CompetitionFY'], market_share['Total_Amount'] * 100, label=label, marker='o')


# Set title and labels
plt.title(f"Program Market Share for {dashboard_type} - {university}")
plt.xlabel("CompetitionFY")
plt.xticks(agency_data["CompetitionFY"].unique())
plt.ylabel("Market Share (%)")
plt.legend()
plt.grid(True)
plt.legend()
st.pyplot(fig)