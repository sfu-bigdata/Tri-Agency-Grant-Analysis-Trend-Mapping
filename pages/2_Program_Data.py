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

# Load data
TRIAGENCY_DATA = pd.read_csv("clean_data/TRIAGENCY_DATA.csv")

# Select Agency
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

# Program Data Trends
st.title(f"Program Trends for {dashboard_type}")

custom_labels = st.checkbox("Use custom labels")
if custom_labels: # Use Specific Programs
    program_labels = st.multiselect('Select programs', agency_data["Program_Name"].unique(), specifc_labels)
else: # Use given labels
    program_labels = specifc_labels

fig = plt.figure(figsize=(12, 6))
# Compute Program Data for each program
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

# Download plot
buf = io.BytesIO()
fig.savefig(buf, format="png", bbox_inches="tight")
buf.seek(0)
st.download_button(
    label="Export Plot",
    data=buf,
    file_name=f"{dashboard_type}_university_funding.png",
    mime="image/png"
)

# Heatmap displaying Market Share
st.title(f"Heatmap of Market Share for {dashboard_type}")
fig, ax = plt.subplots(figsize=(12, 6))
heatmap_data = agency_data[(agency_data["Program_Name"].isin(program_labels)) & (agency_data['Institution'].isin(["Simon Fraser University"] + U15))].groupby(['Program_Name', 'Institution'])['Total_Amount'].sum().reset_index()
sns.heatmap(heatmap_data.pivot_table(index='Program_Name', columns='Institution', values='Total_Amount', aggfunc='sum'), cmap="YlGnBu")
plt.title(f"Heatmap of Program Market Share for {dashboard_type}")
st.pyplot(fig)

# Select Program
label = st.selectbox("Select Program:", program_labels)
data_label = agency_data[agency_data["Program_Name"] == label]

# Helper Function to compute Single Year & Range of Years Funding
def compute_years(data, institutions, year1, year2):
    """Computes funding data for a given range of years and institutions."""
    total_amount = data[(data["Institution"].isin(institutions)) & (data['CompetitionFY'] >= year1) & (data['CompetitionFY'] <= year2)]["Total_Amount"].sum() / len(institutions)
    total_market_share = (total_amount / data[(data['CompetitionFY'] >= year1) & (data['CompetitionFY'] <= year2)]["Total_Amount"].sum()) * 100
    total_grants = data[(data["Institution"].isin(institutions)) & (data['CompetitionFY'] >= year1) & (data['CompetitionFY'] <= year2)]["Total_Amount"].count() / len(institutions)
    avg_grant = data[(data["Institution"].isin(institutions)) & (data['CompetitionFY'] >= year1) & (data['CompetitionFY'] <= year2)]["Total_Amount"].mean() if total_grants > 0 else 0

    return total_amount, total_market_share, total_grants, avg_grant

# Helper Function to Compute Funding Data
def compare_years(data, institutions, year1, year2):
    """ Compares the grant funding data for a specific institution between two years. """

    year1_data = data[(data["Institution"].isin(institutions)) & (data['CompetitionFY'] == year1)] / len(institutions)
    year2_data = data[(data["Institution"].isin(institutions)) & (data['CompetitionFY'] == year2)] / len(institutions)

    year1_marketshare = ((year1_data["Total_Amount"].sum() / data[(data['CompetitionFY'] == year1)]["Total_Amount"].sum()) * 100)
    year2_marketshare = ((year2_data["Total_Amount"].sum() / data[(data['CompetitionFY'] == year2)]["Total_Amount"].sum()) * 100)

    year1_total_grants = year1_data["Total_Amount"].count() / len(institutions)
    year2_total_grants = year2_data["Total_Amount"].count() / len(institutions)

    year1_avg_grant = year1_data["Total_Amount"].mean() if year1_total_grants > 0 else 0
    year2_avg_grant = year2_data["Total_Amount"].mean() if year2_total_grants > 0 else 0

    return year2_data - year1_data, year2_marketshare - year1_marketshare, year2_total_grants - year1_total_grants, year2_avg_grant - year1_avg_grant

table_data = []
years_list = agency_data['CompetitionFY'].unique()

# Select Year Mode
select_year_mode = st.selectbox("Select year range type:", ["Single Year", "Range of Years", "Compare Years"])
if select_year_mode == "Single Year":
    year = st.selectbox("Select Year:", sorted(years_list))

    # Compute SFU Program Data
    total_amount_sfu, market_share_sfu, num_grants_sfu, avg_grant_amount_sfu = compare_years(agency_data, ["Simon Fraser University"], year, year)
    table_data.append(["Simon Fraser University", millify(total_amount_sfu, precision=1), millify(market_share_sfu, precision=1), num_grants_sfu, millify(avg_grant_amount_sfu, precision=1)])
    
    # Compute U15 Program Data
    for u15 in U15:
        total_amount_u15, market_share_u15, num_grants_u15, avg_grant_amount_u15 = compare_years(agency_data, u15, year, year)
        table_data.append([u15, millify(total_amount_u15, precision=1), millify(market_share_u15, precision=1), num_grants_u15, millify(avg_grant_amount_u15, precision=1)])

    # Create & Display Table
    columns = ["Institution", "Total Amount ($)", "Market Share (%)", "Number of Awards", "Avg Award Amount ($)"]
    df = pd.DataFrame(table_data, columns=columns)
    st.table(df)

    # Export Table as CSV
    st.download_button(
        label="Export Table as CSV",
        data=pd.DataFrame(table_data, columns=columns).to_csv(index=False),
        file_name=f"{dashboard_type}_marketshare_data.csv",
        mime="text/csv"
    )

elif select_year_mode == "Range of Years":
    start_year = st.selectbox("Select Start Year:", sorted(years_list))
    end_year = st.selectbox("Select End Year:", sorted(years_list))

    # Compute SFU Program Data
    total_amount_sfu, market_share_sfu, num_grants_sfu, avg_grant_amount_sfu = compute_years(agency_data, ["Simon Fraser University"], start_year, end_year)
    table_data.append(["Simon Fraser University", millify(total_amount_sfu, precision=1), millify(market_share_sfu, precision=1), num_grants_sfu, millify(avg_grant_amount_sfu, precision=1)])
    
    # Compute U15 Program Data
    for u15 in U15:
        total_amount_u15, market_share_u15, num_grants_u15, avg_grant_amount_u15 = compute_years(agency_data, u15, start_year, end_year)
        table_data.append([u15, millify(total_amount_u15, precision=1), millify(market_share_u15, precision=1), num_grants_u15, millify(avg_grant_amount_u15, precision=1)])

    # Create & Display Table
    columns = ["Institution", "Total Amount ($)", "Market Share (%)", "Number of Awards", "Avg Award Amount ($)"]
    df = pd.DataFrame(table_data, columns=columns)
    st.table(df)

    # Export Table as CSV
    st.download_button(
        label="Export Table as CSV",
        data=pd.DataFrame(table_data, columns=columns).to_csv(index=False),
        file_name=f"{dashboard_type}_marketshare_data.csv",
        mime="text/csv"
    )

elif select_year_mode == "Compare Years":
    year1 = st.selectbox("Select Year1:", sorted(years_list))
    year2 = st.selectbox("Select Year2:", sorted(years_list))

    # Compute SFU Program Data
    amount_change_sfu, market_share_change_sfu, num_grants_change_sfu, avg_grant_change_sfu = compare_years(agency_data, ["Simon Fraser University"], year1, year2)
    table_data.append(["Simon Fraser University", amount_change_sfu, market_share_change_sfu, num_grants_change_sfu, avg_grant_change_sfu])  

    # Compute U15 Program Data
    for u15 in U15:
        amount_change_u15, market_share_change_u15, num_grants_change_u15, avg_grant_change_u15 = compare_years(agency_data, u15, year1, year2)
        table_data.append([u15, amount_change_sfu, market_share_change_u15, num_grants_change_u15, avg_grant_change_u15]) 

    # Create a DataFrame from the table data
    df = pd.DataFrame(table_data, columns=["University", "Total Amount Change ($)", "Market Share Change (%)", "Number of Grants Change", "Average Grant Amount Change ($)"])
    df["Total Amount Change ($)"] = df["Total Amount Change ($)"].apply(lambda x: f'<span style="color: red;">{millify(x, precision=1)}</span>' if x < 0 else f'<span style="color: green;">{millify(x, precision=1)}</span>')
    df["Market Share Change (%)"] = df["Market Share Change (%)"].apply(lambda x: f'<span style="color: red;">{millify(x, precision=1)}</span>' if x < 0 else f'<span style="color: green;">{millify(x, precision=1)}</span>')
    df["Number of Grants Change"] = df["Number of Grants Change"].apply(lambda x: f'<span style="color: red;">{millify(x, precision=1)}</span>' if x < 0 else f'<span style="color: green;">{millify(x, precision=1)}</span>')
    df["Average Grant Amount Change ($)"] = df["Average Grant Amount Change ($)"].apply(lambda x: f'<span style="color: red;">{millify(x, precision=1)}</span>' if x < 0 else f'<span style="color: green;">{millify(x, precision=1)}</span>')

    st.markdown(df.to_html(escape=False), unsafe_allow_html=True)

    # Export Table as CSV
    st.download_button(
        label="Export Table as CSV",
        data=pd.DataFrame(table_data, columns=["University", "Total Amount Change ($)", "Market Share Change (%)", "Number of Grants Change", "Average Grant Amount Change ($)"]).to_csv(index=False),
        file_name=f"{dashboard_type}_marketshare_data.csv",
        mime="text/csv"
    )

# Program Market Share Dashboard
st.title(f"Program Market Share for {dashboard_type}")

university = st.selectbox("Select University:", ["Simon Fraser University"] + U15)

fig = plt.figure(figsize=(12, 6))
# Compute market share for each program for the selected university
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

# Download plot
buf = io.BytesIO()
fig.savefig(buf, format="png", bbox_inches="tight")
buf.seek(0)
st.download_button(
    label="Export Plot",
    data=buf,
    file_name=f"{dashboard_type}_{university}_marketshare.png",
    mime="image/png"
)