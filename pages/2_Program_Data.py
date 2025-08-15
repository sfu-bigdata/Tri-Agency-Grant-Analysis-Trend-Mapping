import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from millify import millify
import  io

st.set_page_config(page_title="Program Data", page_icon="")

# U15 + UVic
U15 = ["University of Alberta", "University of British Columbia", "University of Calgary", "Dalhousie University", "Université Laval", 
       "University of Manitoba", "McGill University", "McMaster University", "Université de Montréal", "University of Ottawa", 
       "Queen's University", "University of Saskatchewan", "University of Toronto", "University of Waterloo", "University of Western Ontario",
       "University of Victoria"] 

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

## Program Data Trends
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

# Select Program
label = st.selectbox("Select Program:", program_labels)

## University Funding by Program
st.title(f"Program Funding for {dashboard_type}")

# Select Universities
university = st.multiselect("Select University:", ["U15 (+UVic) Mean"] + ["U15 (+UVic) Median"] + ["Simon Fraser University"] + U15, default=["U15 (+UVic) Mean", "U15 (+UVic) Median", "Simon Fraser University"])

fig = plt.figure(figsize=(12, 6))
fiscal_years = sorted(agency_data["FiscalYear"].unique())
# Compute & Plot University Funding Trends for given Program
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

plt.title(f"{label} Funding for {dashboard_type}")
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
    """Compute funding stats for a given range of years and institutions.

    Returns:
        tuple: (total_amount, total_market_share, total_grants, avg_grant)
    """

    # Filter data for selected institutions & years
    df_filtered = data[
        (data["Institution"].isin(institutions)) &
        (data["FiscalYear"].between(year1, year2))
    ]
    df_all_years = data[
        data["FiscalYear"].between(year1, year2)
    ]

    # Group by institution
    grouped_amounts = df_filtered.groupby("Institution")["AmountPaid"].sum()
    grouped_counts = df_filtered.groupby("Institution")["AmountPaid"].count()

    if median:
        total_amount = grouped_amounts.median()
        total_grants = grouped_counts.median()
        avg_grant = df_filtered["AmountPaid"].median() if total_grants > 0 else None
    else:
        total_amount = grouped_amounts.mean()
        total_grants = grouped_counts.mean()
        avg_grant = df_filtered["AmountPaid"].mean() if total_grants > 0 else None

    # Market share is always based on total amount vs all funding in period
    total_market_share = (total_amount / df_all_years["AmountPaid"].sum()) * 100 if df_all_years["AmountPaid"].sum() > 0 else 0

    # Ensure no negative/invalid totals
    if not (total_amount > 0):
        total_amount, total_market_share, total_grants, avg_grant = 0, 0, 0, 0

    return total_amount, total_market_share, total_grants, avg_grant

# Helper Function to Compute Compare Years Funding
def compare_years(data, institutions, median, year1, year2):
    """Compare grant funding data for selected institutions between two years.

    Returns tuple:
      (Δ total amount, Δ market share, Δ number of grants, Δ avg grant amount)
    """
    # Compute total amounts by institution
    def safe_sum(df):
        if df.empty:
            return pd.Series(0, index=institutions)
        return df.groupby("Institution")["AmountPaid"].sum().reindex(institutions, fill_value=0)

    # Compute market share
    def safe_market_share(total, total_all):
        return (total / total_all) * 100 if total_all > 0 else 0

    # Filter data for selected institutions & years
    y1 = data[(data["Institution"].isin(institutions)) & (data["FiscalYear"] == year1)]
    y2 = data[(data["Institution"].isin(institutions)) & (data["FiscalYear"] == year2)]
    
    # Compute total amount for the program
    total_all_y1 = data[data["FiscalYear"] == year1]["AmountPaid"].sum()
    total_all_y2 = data[data["FiscalYear"] == year2]["AmountPaid"].sum()

    # Compute total amounts by institution
    totals_y1 = safe_sum(y1) 
    totals_y2 = safe_sum(y2)

    # Compute number of grants by institution
    grants_y1 = y1.groupby("Institution")["AmountPaid"].count().reindex(institutions, fill_value=0)
    grants_y2 = y2.groupby("Institution")["AmountPaid"].count().reindex(institutions, fill_value=0)

    # Compute average grant amount
    avg_grant_y1 = totals_y1 / grants_y1.replace(0, 1)
    avg_grant_y1[grants_y1 == 0] = 0
    avg_grant_y2 = totals_y2 / grants_y2.replace(0, 1)
    avg_grant_y2[grants_y2 == 0] = 0

    if not median: # Compute Mean across all institutions
        result = (
            totals_y2.mean() - totals_y1.mean(),
            safe_market_share(totals_y2.mean(), total_all_y2) - safe_market_share(totals_y1.mean(), total_all_y1),
            grants_y2.mean() - grants_y1.mean(),
            avg_grant_y2.mean() - avg_grant_y1.mean(),
        )
    else: # Compute Median across all institutions
        result = (
            (totals_y2 - totals_y1).median(),
            safe_market_share(totals_y2.median(), total_all_y2) - safe_market_share(totals_y1.median(), total_all_y1),
            (grants_y2 - grants_y1).median(),
            (avg_grant_y2 - avg_grant_y1).median(),
        )

    if any(pd.isna(val) for val in result):
        result = (0, 0, 0, 0)

    return result
    
table_data = []
years_list = sorted(agency_data['FiscalYear'].unique())

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
    st.write(f"Total Agency Funding: {millify(data_label[data_label['FiscalYear'] == year]['AmountPaid'].sum(), precision=2)}")
    st.markdown(df.style.hide(axis="index").to_html(), unsafe_allow_html=True)

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
        end_year = st.selectbox("Select End Year:", sorted(years_list, reverse=True))

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
    st.write(f"Total Agency Funding: {millify(data_label[(data_label['FiscalYear'] >= start_year) & (data_label['FiscalYear'] <= end_year)]['AmountPaid'].sum(), precision=2)}")
    st.markdown(df.style.hide(axis="index").to_html(), unsafe_allow_html=True)

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

    st.write(f"Difference in Agency Funding: {millify(data_label[(data_label['FiscalYear'] == year2)]['AmountPaid'].sum() - data_label[(data_label['FiscalYear'] == year1)]['AmountPaid'].sum(), precision=2)}")
    st.markdown(df.style.hide(axis="index").to_html(), unsafe_allow_html=True)

    # Export Table as CSV
    st.download_button(
        label="Export Table as CSV",
        data=pd.DataFrame(table_data, columns=["University", "Total Amount Change ($)", "Market Share Change (%)", "Number of Grants Change", "Average Grant Amount Change ($)"]).to_csv(index=False),
        file_name=f"{dashboard_type}_marketshare_data.csv",
        mime="text/csv"
    )
