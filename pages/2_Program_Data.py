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
    specifc_labels = ["Project Grant", "Operating Grant"]
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
    grouped_label = agency_data[agency_data["Program_Name"] == label].groupby('FiscalYear')['AmountPaid'].sum().reset_index()
    plt.plot(grouped_label['FiscalYear'], grouped_label['AmountPaid'], label=label, marker='o')
plt.title(f"Program Trends for {dashboard_type}")
plt.ylabel("Total Funding Amount")
plt.xlabel("FiscalYear")
plt.xticks(agency_data["FiscalYear"].unique())
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

# # Heatmap displaying Market Share
# st.title(f"Heatmap of Total Funding for {dashboard_type}")
# fig, ax = plt.subplots(figsize=(12, 6))
# heatmap_data = agency_data[(agency_data["Program_Name"].isin(program_labels)) & (agency_data['Institution'].isin(["Simon Fraser University"] + U15))].groupby(['Program_Name', 'Institution'])['AmountPaid'].sum().reset_index()
# sns.heatmap(heatmap_data.pivot_table(index='Program_Name', columns='Institution', values='AmountPaid', aggfunc='sum'), cmap="YlGnBu")
# # plt.title(f"Heatmap of Program Market Share for {dashboard_type}")
# st.pyplot(fig)

# Select Program
label = st.selectbox("Select Program:", program_labels)

st.title(f"Program Market Share for {dashboard_type}")

university = st.multiselect("Select University:", ["U15 (+UVic) Mean"] + ["U15 (+UVic) Median"] + ["Simon Fraser University"] + U15, ["U15 (+UVic) Mean", "U15 (+UVic) Median", "Simon Fraser University"])

fig = plt.figure(figsize=(12, 6))
fiscal_years = agency_data["FiscalYear"].unique()
for uni in university:
    if uni == "U15 (+UVic) Mean":
        program_data = agency_data[(agency_data["Program_Name"] == label) & (agency_data['Institution'].isin(U15))]
        grouped_data = program_data.groupby(['Institution', 'FiscalYear'])['AmountPaid'].sum().reset_index()
        total_amounts_u15 = [grouped_data[grouped_data['FiscalYear'] == year]['AmountPaid'].mean() for year in fiscal_years]
        plt.plot(fiscal_years, total_amounts_u15, label=uni, marker='o')
    elif uni == "U15 (+UVic) Median":
        program_data = agency_data[(agency_data["Program_Name"] == label) & (agency_data['Institution'].isin(U15))]
        grouped_data = program_data.groupby(['Institution', 'FiscalYear'])['AmountPaid'].sum().reset_index()
        total_amounts_u15 = [grouped_data[grouped_data['FiscalYear'] == year]['AmountPaid'].median() for year in fiscal_years]
        plt.plot(fiscal_years, total_amounts_u15, label=uni, marker='o')
    else:
        program_data = agency_data[(agency_data["Program_Name"] == label) & (agency_data['Institution'] == uni)]
        total_amount_u15 = program_data.groupby('FiscalYear')['AmountPaid'].sum().reset_index()
        plt.plot(total_amount_u15['FiscalYear'], total_amount_u15['AmountPaid'], label=uni, marker='o')

plt.title(f"Program Market Share for {dashboard_type}")
plt.xlabel("FiscalYear")
plt.xticks(agency_data["FiscalYear"].unique())
plt.ylabel("Total Funding Amount")
plt.legend()
plt.grid(True)
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

data_label = agency_data[agency_data["Program_Name"] == label]

# Helper Function to compute Single Year & Range of Years Funding
def compute_years(data, institutions, median, year1, year2):
    """Computes funding data for a given range of years and institutions."""
    if not median:
        total_amount = data[(data["Institution"].isin(institutions)) & (data['FiscalYear'] >= year1) & (data['FiscalYear'] <= year2)].groupby("Institution")["AmountPaid"].sum().mean()
        total_market_share = (total_amount / data[(data['FiscalYear'] >= year1) & (data['FiscalYear'] <= year2)]["AmountPaid"].sum()) * 100
        total_grants = data[(data["Institution"].isin(institutions)) & (data['FiscalYear'] >= year1) & (data['FiscalYear'] <= year2)].groupby("Institution")["AmountPaid"].count().mean()
        avg_grant = data[(data["Institution"].isin(institutions)) & (data['FiscalYear'] >= year1) & (data['FiscalYear'] <= year2)]["AmountPaid"].mean() if total_grants > 0 else None

    else: # if median
        total_amount = data[(data["Institution"].isin(institutions)) & (data['FiscalYear'] >= year1) & (data['FiscalYear'] <= year2)].groupby("Institution")["AmountPaid"].sum().median()
        total_market_share = (total_amount / data[(data['FiscalYear'] >= year1) & (data['FiscalYear'] <= year2)]["AmountPaid"].sum()) * 100
        total_grants = data[(data["Institution"].isin(institutions)) & (data['FiscalYear'] >= year1) & (data['FiscalYear'] <= year2)].groupby("Institution")["AmountPaid"].count().median()
        avg_grant = data[(data["Institution"].isin(institutions)) & (data['FiscalYear'] >= year1) & (data['FiscalYear'] <= year2)]["AmountPaid"].median() if total_grants > 0 else None
    return total_amount, total_market_share, total_grants, avg_grant

# Helper Function to Compute Funding Data
def compare_years(data, institutions, median, year1, year2):
    """ Compares the grant funding data for a specific institution between two years. """

    year1_data = data[(data["Institution"].isin(institutions)) & (data['FiscalYear'] == year1)]
    year2_data = data[(data["Institution"].isin(institutions)) & (data['FiscalYear'] == year2)]

    if not median:
        year1_total_amount = year1_data.groupby("Institution")['AmountPaid'].sum().mean()
        year2_total_amount = year2_data.groupby("Institution")['AmountPaid'].sum().mean()

        year1_marketshare = ((year1_total_amount / data[(data['FiscalYear'] == year1)]["AmountPaid"].sum()) * 100)
        year2_marketshare = ((year2_total_amount / data[(data['FiscalYear'] == year1)]["AmountPaid"].sum()) * 100)

        year1_total_grants = year1_data.groupby("Institution")["AmountPaid"].count().mean()
        year2_total_grants = year2_data.groupby("Institution")["AmountPaid"].count().mean()

        year1_avg_grant = year1_data["AmountPaid"].mean() if year1_total_grants > 0 else None
        year2_avg_grant = year2_data["AmountPaid"].mean() if year2_total_grants > 0 else None

    else: # if median
        year1_total_amount = year1_data.groupby("Institution")['AmountPaid'].sum().median()
        year2_total_amount = year2_data.groupby("Institution")['AmountPaid'].sum().median()

        year1_marketshare = ((year1_total_amount / data[(data['FiscalYear'] == year1)]["AmountPaid"].sum()) * 100)
        year2_marketshare = ((year2_total_amount / data[(data['FiscalYear'] == year1)]["AmountPaid"].sum()) * 100)

        year1_total_grants = year1_data.groupby("Institution")["AmountPaid"].count().median()
        year2_total_grants = year2_data.groupby("Institution")["AmountPaid"].count().median()

        year1_avg_grant = year1_data["AmountPaid"].median() if year1_total_grants > 0 else None
        year2_avg_grant = year2_data["AmountPaid"].median() if year2_total_grants > 0 else None

    return year2_total_amount - year1_total_amount, year2_marketshare - year1_marketshare, year2_total_grants - year1_total_grants, year2_avg_grant - year1_avg_grant
    
table_data = []
years_list = agency_data['FiscalYear'].unique()

# Select Year Mode
select_year_mode = st.selectbox("Select year range type:", ["Single Year", "Range of Years", "Compare Years"])
if select_year_mode == "Single Year":
    year = st.selectbox("Select Year:", sorted(years_list))

    # Compute U15 + UVic mean Program Data
    total_amount_u15, market_share_u15, num_grants_u15, avg_grant_amount_u15 = compute_years(data_label, U15, False, year, year)
    table_data.append(["U15 + UVic Mean", millify(total_amount_u15, precision=1), millify(market_share_u15, precision=2), millify(num_grants_u15, precision=1), millify(avg_grant_amount_u15, precision=1)])

    # Compute U15 + UVic median Program Data
    total_amount_u15_median, market_share_u15_median, num_grants_u15_median, avg_grant_amount_u15_median = compute_years(data_label, U15, True, year, year)
    table_data.append(["U15 + UVic Median", millify(total_amount_u15_median, precision=1), millify(market_share_u15_median, precision=2), millify(num_grants_u15_median, precision=1), millify(avg_grant_amount_u15_median, precision=1)])

    # Compute SFU Program Data
    total_amount_sfu, market_share_sfu, num_grants_sfu, avg_grant_amount_sfu = compute_years(data_label, ["Simon Fraser University"], False, year, year)
    table_data.append(["Simon Fraser University", millify(total_amount_sfu, precision=1), millify(market_share_sfu, precision=2), millify(num_grants_sfu), millify(avg_grant_amount_sfu, precision=1)])
    
    # Compute U15 Program Data
    for u15 in U15:
        total_amount_u15, market_share_u15, num_grants_u15, avg_grant_amount_u15 = compute_years(data_label, [u15], False, year, year)
        table_data.append([u15, millify(total_amount_u15, precision=1), millify(market_share_u15, precision=2), millify(num_grants_u15), millify(avg_grant_amount_u15, precision=1)])

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
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.selectbox("Select Start Year:", sorted(years_list))
    with col2:
        end_year = st.selectbox("Select End Year:", sorted(years_list))

    # Compute U15 + UVic Mean Program Data
    total_amount_u15, market_share_u15, num_grants_u15, avg_grant_amount_u15 = compute_years(data_label, U15, False, start_year, end_year)
    table_data.append(["U15 + UVic Mean", millify(total_amount_u15, precision=1), millify(market_share_u15, precision=2), millify(num_grants_u15, precision=1), millify(avg_grant_amount_u15, precision=1)])

    # Compute U15 + UVic median Program Data
    total_amount_u15_median, market_share_u15_median, num_grants_u15_median, avg_grant_amount_u15_median = compute_years(data_label, U15, True, start_year, end_year)
    table_data.append(["U15 + UVic Median", millify(total_amount_u15_median, precision=1), millify(market_share_u15_median, precision=2), millify(num_grants_u15_median, precision=1), millify(avg_grant_amount_u15_median, precision=1)])

    # Compute SFU Program Data
    total_amount_sfu, market_share_sfu, num_grants_sfu, avg_grant_amount_sfu = compute_years(data_label, ["Simon Fraser University"], False, start_year, end_year)
    table_data.append(["Simon Fraser University", millify(total_amount_sfu, precision=1), millify(market_share_sfu, precision=2), millify(num_grants_sfu), millify(avg_grant_amount_sfu, precision=1)])
    
    # Compute U15 Program Data
    for u15 in U15:
        total_amount_u15, market_share_u15, num_grants_u15, avg_grant_amount_u15 = compute_years(data_label, [u15], False, start_year, end_year)
        table_data.append([u15, millify(total_amount_u15, precision=1), millify(market_share_u15, precision=2), millify(num_grants_u15), millify(avg_grant_amount_u15, precision=1)])

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
    col1, col2 = st.columns(2)
    with col1:
        year1 = st.selectbox("Select Year1:", sorted(years_list))
    with col2:
        year2 = st.selectbox("Select Year2:", sorted(years_list))

    # Compute U15 + UVic Mean Program Data
    amount_change_u15, market_share_change_u15, num_grants_change_u15, avg_grant_change_u15 = compare_years(data_label, U15, False, year1, year2)
    table_data.append(["U15 + UVic Mean", amount_change_u15, market_share_change_u15, num_grants_change_u15, avg_grant_change_u15])

    # Compute U15 + UVic median Program Data
    amount_change_u15, market_share_change_u15, num_grants_change_u15, avg_grant_change_u15 = compare_years(data_label, U15, True, year1, year2)
    table_data.append(["U15 + UVic Median", amount_change_u15, market_share_change_u15, num_grants_change_u15, avg_grant_change_u15])

    # Compute SFU Program Data
    amount_change_sfu, market_share_change_sfu, num_grants_change_sfu, avg_grant_change_sfu = compare_years(data_label, ["Simon Fraser University"], False, year1, year2)
    table_data.append(["Simon Fraser University", amount_change_sfu, market_share_change_sfu, num_grants_change_sfu, avg_grant_change_sfu])  

    # Compute U15 Program Data
    for u15 in U15:
        amount_change_u15, market_share_change_u15, num_grants_change_u15, avg_grant_change_u15 = compare_years(data_label, [u15], False, year1, year2)
        table_data.append([u15, amount_change_sfu, market_share_change_u15, num_grants_change_u15, avg_grant_change_u15]) 

    # Create a DataFrame from the table data
    df = pd.DataFrame(table_data, columns=["University", "Total Amount Change ($)", "Market Share Change (%)", "Number of Grants Change", "Average Grant Amount Change ($)"])
    df["Total Amount Change ($)"] = df["Total Amount Change ($)"].apply(lambda x: f'<span style="color: red;">{millify(x, precision=1)}</span>' if x < 0 else f'<span style="color: green;">{millify(x, precision=1)}</span>')
    df["Market Share Change (%)"] = df["Market Share Change (%)"].apply(lambda x: f'<span style="color: red;">{millify(x, precision=2)}</span>' if x < 0 else f'<span style="color: green;">{millify(x, precision=1)}</span>')
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
# st.title(f"Program Market Share for {dashboard_type}")

# university = st.selectbox("Select University:", ["U15 (+UVic) Mean"] + ["Simon Fraser University"] + U15)

# fig = plt.figure(figsize=(12, 6))
# if university == "U15 (+UVic) Mean":
#     for label in program_labels:
#         program_data = agency_data[(agency_data["Program_Name"] == label) & (agency_data['Institution'].isin(U15))]
#         market_share = (program_data.groupby('FiscalYear')['AmountPaid'].sum() / agency_data[(agency_data["Program_Name"] == label)].groupby('FiscalYear')['AmountPaid'].sum()).reset_index()
#         plt.plot(market_share['FiscalYear'], (market_share['AmountPaid'] / len(U15)) * 100, label=label, marker='o')
# else:
#     # Compute market share for each program for the selected university
#     for label in program_labels:
#         program_data = agency_data[(agency_data["Program_Name"] == label) & (agency_data['Institution'] == university)]
#         market_share = (program_data.groupby('FiscalYear')['AmountPaid'].sum() / agency_data[(agency_data["Program_Name"] == label)].groupby('FiscalYear')['AmountPaid'].sum()).reset_index()
#         plt.plot(market_share['FiscalYear'], market_share['AmountPaid'] * 100, label=label, marker='o')

# # Set title and labels
# plt.title(f"Program Market Share for {dashboard_type} - {university}")
# plt.xlabel("FiscalYear")
# plt.xticks(agency_data["FiscalYear"].unique())
# plt.ylabel("Market Share (%)")
# plt.legend()
# plt.grid(True)
# plt.legend()
# st.pyplot(fig)

# # Download plot
# buf = io.BytesIO()
# fig.savefig(buf, format="png", bbox_inches="tight")
# buf.seek(0)
# st.download_button(
#     label="Export Plot",
#     data=buf,
#     file_name=f"{dashboard_type}_{university}_marketshare.png",
#     mime="image/png"
# )