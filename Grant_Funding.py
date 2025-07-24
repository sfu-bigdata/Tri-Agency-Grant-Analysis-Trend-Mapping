import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from millify import millify
import io

st.set_page_config(page_title="Grant Funding Dashboard", page_icon="")

U15 = ["University of Alberta", "University of British Columbia", "University of Calgary", "Dalhousie University", "Université Laval", 
       "University of Manitoba", "McGill University", "McMaster University", "Université de Montréal", "University of Ottawa", 
       "Queen's University", "University of Saskatchewan", "University of Toronto", "University of Waterloo", "University of Western Ontario"]

# U15 + UVic
U15 = ["University of Alberta", "University of British Columbia", "University of Calgary", "Dalhousie University", "Université Laval", 
       "University of Manitoba", "McGill University", "McMaster University", "Université de Montréal", "University of Ottawa", 
       "Queen's University", "University of Saskatchewan", "University of Toronto", "University of Waterloo", "University of Western Ontario",
       "University of Victoria"] 

# Load data
TRIAGENCY_DATA = pd.read_csv("clean_data/TRIAGENCY_DATA.csv", low_memory=False)
data = TRIAGENCY_DATA.copy()

# Total Agency Funding Dashboard
st.title("Grant Funding Dashboard")

total_funding = st.checkbox("Display Total Funding") 
if total_funding: # Total Funding of All Agencies Combined
    fig = plt.figure(figsize=(12, 6))
    total_funding = data.groupby('CompetitionFY')['Total_Amount'].sum()
    plt.plot(total_funding.index, total_funding.values, marker='o', label="Total Funding")

else: # Total Funding of Each Agency
    agencies_selected = st.multiselect("Select Agencies", ["CIHR", "NSERC", "SSHRC"], ["CIHR", "NSERC", "SSHRC"])
    fig = plt.figure(figsize=(12, 6))
    for agency in agencies_selected:
        total_funding = data[data["Agency"] == agency].groupby('CompetitionFY')['Total_Amount'].sum()
        plt.plot(total_funding.index, total_funding.values, marker='o', label=f"{agency} Funding")

plt.xlabel("CompetitionFY")
plt.xticks(data["CompetitionFY"].unique())
plt.ylabel("Funding Amount")
plt.title("Total Agency Funding Over Time")
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
    file_name=f"agency_funding.png",
    mime="image/png"
)

# Select Agency for Data Analysis
dashboard_type = st.selectbox("Select Agency:", ["All", "CIHR", "NSERC", "SSHRC"])

if dashboard_type == "All":
    data = TRIAGENCY_DATA.copy()
elif dashboard_type == "CIHR":
    data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "CIHR"].copy()
elif dashboard_type == "NSERC":
    data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "NSERC"].copy()
elif dashboard_type == "SSHRC":
    data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "SSHRC"].copy()

# University Funding Over Time for given Agency(s)
st.subheader(f"University Funding Over Time for Agency: {dashboard_type}")
column1, column2, _, = st.columns(3)
with column1:
    specific_u15 = st.checkbox("Select U15 Universities")
with column2:
    display_market = st.checkbox("Display Market Share")


fig = plt.figure(figsize=(12, 6))
if specific_u15: # Select specific U15 Universities
    u15_selected = st.multiselect("Select Universities", ["Simon Fraser University"] + U15)

    if display_market: # Display Market Share (%)
        years = sorted(data["CompetitionFY"].unique())
        for u15_uni in u15_selected:
            u15_funding = []
            for year in years:
                year_data = data[data["CompetitionFY"] == year]
                u15_funding.append((year_data[year_data["Institution"] == u15_uni]["Total_Amount"].sum() / year_data["Total_Amount"].sum()) * 100)
            plt.plot(years, u15_funding, label=u15_uni, marker='o')
    
    else: # Display Funding Amount ($)
        for u15_uni in u15_selected:
            u15_by_year = (data[data["Institution"] == u15_uni].groupby('CompetitionFY')['Total_Amount'].sum())
            plt.plot(u15_by_year.index, u15_by_year.values, label=u15_uni, marker='o')
    
else: # Display SFU and all U15 + UVic
    if display_market: # Display Market Share (%)
        years = sorted(data["CompetitionFY"].unique())
        sfu_funding = []
        u15_mean_funding = []

        for year in years:
            year_data = data[data["CompetitionFY"] == year]
            sfu_funding.append((year_data[year_data["Institution"] == "Simon Fraser University"]["Total_Amount"].sum() / year_data["Total_Amount"].sum()) * 100)
            u15_mean_funding.append(((year_data[year_data["Institution"].isin(U15)]["Total_Amount"].sum() / len(U15)) / year_data["Total_Amount"].sum()) * 100)
        plt.plot(years, sfu_funding, label='SFU', marker='o')
        plt.plot(years, u15_mean_funding, label="U15 Mean", marker='o')

    else: # Display Funding Amount ($)
        sfu_by_year = data[data["Institution"] == "Simon Fraser University"].groupby('CompetitionFY')['Total_Amount'].sum()
        u15_by_year = (data[data["Institution"].isin(U15)].groupby('CompetitionFY')['Total_Amount'].sum()/len(U15))
        plt.plot(sfu_by_year.index, sfu_by_year.values, label='SFU', marker='o')
        plt.plot(u15_by_year.index, u15_by_year.values, label="U15 Mean", marker='o')

# Set title and labels depending on selection
if display_market:
    plt.title("University Market Share Over Time")
    plt.ylabel("Market Share (%)")

else:
    plt.title("University Funding Over Time")
    plt.ylabel("Funding Amount")
plt.xlabel("CompetitionFY")
plt.xticks(data["CompetitionFY"].unique())
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
    file_name=f"{dashboard_type}_university_funding.png",
    mime="image/png"
)

# Table displaying Funding & Grant data
st.title("Table Dashboard")

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
    
agency_market_share = []
# Select one of 3 analysis options
select_year_mode = st.selectbox("Select year range type:", ["Single Year", "Range of Years", "Compare Years"])
if select_year_mode == "Single Year": 
    year = st.selectbox("Select Year:", sorted(data['CompetitionFY'].unique()))

    st.write(f"Total Agency Funding: {millify(data[(data['CompetitionFY'] == year)]['Total_Amount'].sum(), precision=2)}")

    # Compute U15 mean funding data
    u15_mean_total_amount, u15_mean_market_share, u15_mean_total_grants, u15_mean_avg_grant = compute_years(data, U15, year, year)
    agency_market_share.append({"University": "U15 Mean", "Total Grant Amount": millify(u15_mean_total_amount, precision=2), 
                                "Market Share (%)": f"{u15_mean_market_share:.2f}%", "Num of Grants": int(u15_mean_total_grants), "Avg Grant Amount": millify(u15_mean_avg_grant, precision=2)})

    # Compute SFU funding data
    sfu_total_amount, sfu_market_share, sfu_total_grants, sfu_avg_grant = compute_years(data, ["Simon Fraser University"], year, year)
    agency_market_share.append({"University": "Simon Fraser University", "Total Grant Amount": millify(sfu_total_amount, precision=2), 
                                "Market Share (%)": f"{sfu_market_share:.2f}%", "Num of Grants": sfu_total_grants, "Avg Grant Amount": millify(sfu_avg_grant, precision=2)})

    # Compute each U15 funding data
    for u15_university in U15:
        total_u15_amount, market_share, total_grants, avg_grant = compute_years(data, [u15_university], year, year)
        agency_market_share.append({"University": u15_university, "Total Grant Amount": millify(total_u15_amount, precision=2),
                                    "Market Share (%)": f"{market_share:.2f}%", "Num of Grants": total_grants, "Avg Grant Amount": millify(avg_grant, precision=2)})
    

elif select_year_mode == "Range of Years":
    column1, column2 = st.columns(2)
    # Select range of years
    with column1:
        from_year = st.selectbox("Select From Year:", sorted(data['CompetitionFY'].unique()))
    with column2:
        to_year = st.selectbox("Select To Year:", sorted(data['CompetitionFY'].unique(), reverse=True))

    st.write(f"Total Agency Funding: {millify(data[(data['CompetitionFY'] >= from_year) & (data['CompetitionFY'] <= to_year)]['Total_Amount'].sum(), precision=2)}")

    # Compute U15 mean funding data
    u15_mean_total_amount, u15_mean_market_share, u15_mean_total_grants, u15_mean_avg_grant = compute_years(data, U15, from_year, to_year)
    agency_market_share.append({"University": "U15 Mean", "Total Grant Amount": millify(u15_mean_total_amount, precision=2), 
                                "Market Share (%)": f"{u15_mean_market_share:.2f}%", "Num of Grants": int(u15_mean_total_grants), "Avg Grant Amount": millify(u15_mean_avg_grant, precision=2)})

    # Compute SFU funding data
    sfu_total_amount, sfu_market_share, sfu_total_grants, sfu_avg_grant = compute_years(data, ["Simon Fraser University"], from_year, to_year)
    agency_market_share.append({"University": "Simon Fraser University", "Total Grant Amount": millify(sfu_total_amount, precision=2), 
                                "Market Share (%)": f"{sfu_market_share:.2f}%", "Num of Grants": sfu_total_grants, "Avg Grant Amount": millify(sfu_avg_grant, precision=2)})

    # Compute each U15 funding data
    for u15_university in U15:
        total_u15_amount, market_share, total_grants, avg_grant = compute_years(data, [u15_university], from_year, to_year)
        agency_market_share.append({"University": u15_university, "Total Grant Amount": millify(total_u15_amount, precision=2),
                                    "Market Share (%)": f"{market_share:.2f}%", "Num of Grants": total_grants, "Avg Grant Amount": millify(avg_grant, precision=2, drop_nulls=True)})

elif select_year_mode == "Compare Years":
    column1, column2 = st.columns(2)

    with column1:
        year1 = st.selectbox("Select Year 1:", sorted(data['CompetitionFY'].unique()))
    with column2:
        year2 = st.selectbox("Select Year 2:", sorted(data['CompetitionFY'].unique()))

    st.write(f"Difference in Agency Funding: {millify(data[(data['CompetitionFY'] == year2)]['Total_Amount'].sum() - data[(data['CompetitionFY'] == year1)]['Total_Amount'].sum(), precision=2)}")
    
    # Computer U15 mean funding data
    u15_mean_change_amount, u15_mean_change_market_share, u15_mean_change_total_grants, u15_mean_change_avg_grant = compare_years(data, U15, year1, year2)
    agency_market_share.append({"University": "U15 Mean", "Change in Grant Amount ($)": u15_mean_change_amount, "Change in Market Share (%)": u15_mean_change_market_share,
                                "Change in Num of Grants": u15_mean_change_total_grants, "Change in Avg Grant Amount ($)": u15_mean_change_avg_grant})

    # Compute SFU funding data
    sfu_change_amount, sfu_change_market_share, sfu_change_total_grants, sfu_change_avg_grant = compare_years(data, "Simon Fraser University", year1, year2)
    agency_market_share.append({"University": "Simon Fraser University", "Change in Grant Amount ($)": sfu_change_amount, "Change in Market Share (%)": sfu_change_market_share,
                                "Change in Num of Grants": sfu_change_total_grants, "Change in Avg Grant Amount ($)": sfu_change_avg_grant})
    
    # Compute each U15 funding data
    for u15_university in U15:
        u15_change_amount, u15_change_market_share, u15_change_total_grants, u15_change_avg_grant = compare_years(data, u15_university, year1, year2)
        agency_market_share.append({"University": u15_university, "Change in Grant Amount ($)": u15_change_amount, "Change in Market Share (%)": u15_change_market_share,
                                    "Change in Num of Grants": u15_change_total_grants, "Change in Avg Grant Amount ($)": u15_change_avg_grant})

if select_year_mode == "Compare Years":
    # Display the market share list in a table
    market_share_table = pd.DataFrame(agency_market_share)
    market_share_table["Change in Grant Amount ($)"] = market_share_table["Change in Grant Amount ($)"].apply(lambda x: f'<span style="color: red;">{millify(x)}</span>' if x < 0 else f'<span style="color: green;">{millify(x)}</span>')
    market_share_table["Change in Market Share (%)"] = market_share_table["Change in Market Share (%)"].apply(lambda x: f'<span style="color: red;">{x:.2f}%</span>' if x < 0 else f'<span style="color: green;">{x:.2f}%</span>')
    market_share_table["Change in Num of Grants"] = market_share_table["Change in Num of Grants"].apply(lambda x: f'<span style="color: red;">{x}</span>' if x < 0 else f'<span style="color: green;">{x}</span>')
    market_share_table["Change in Avg Grant Amount ($)"] = market_share_table["Change in Avg Grant Amount ($)"].apply(lambda x: f'<span style="color: red;">{millify(x)}</span>' if x < 0 else f'<span style="color: green;">{millify(x)}</span>')

    st.markdown(market_share_table.to_html(escape=False), unsafe_allow_html=True)
    
    # Download Table as CSV
    st.download_button(
        label="Export Table as CSV",
        data=pd.DataFrame(agency_market_share).to_csv(index=False),
        file_name=f"{dashboard_type}_market_share_data.csv",
        mime="text/csv"
    )

else:
    # Display the market share list in a table
    market_share_table = pd.DataFrame(agency_market_share)
    st.markdown(market_share_table.to_html(escape=False), unsafe_allow_html=True)

    # Download Table as CSV
    st.download_button(
        label="Export Table as CSV",
        data=market_share_table.to_csv(index=False),
        file_name=f"{dashboard_type}_market_share_data.csv",
        mime="text/csv"
    )
