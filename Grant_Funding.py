import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from millify import millify
import io

st.set_page_config(page_title="Grant Funding Dashboard", page_icon="")

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

data = TRIAGENCY_DATA.copy()

st.title("Grant Funding Dashboard")

total_funding = st.checkbox("Display Total Funding")
if total_funding:
    fig = plt.figure(figsize=(12, 6))
    total_funding = data.copy().groupby('CompetitionFY')['Total_Amount'].sum()
    plt.plot(total_funding.index, total_funding.values, marker='o', label="Total Funding")
else:
    agencies_selected = st.multiselect("Select Agencies", ["CIHR", "NSERC", "SSHRC"], ["CIHR", "NSERC", "SSHRC"])
    fig = plt.figure(figsize=(12, 6))
    for agency in agencies_selected:
        total_funding = data[data["Agency"] == agency].copy().groupby('CompetitionFY')['Total_Amount'].sum()
        plt.plot(total_funding.index, total_funding.values, marker='o', label=f"{agency} Funding")

plt.xlabel("CompetitionFY")
plt.xticks(data["CompetitionFY"].unique())
plt.ylabel("Funding Amount")
plt.title("Total Agency Funding Over Time")
plt.legend()
plt.grid(True)
st.pyplot(fig)

buf = io.BytesIO()
fig.savefig(buf, format="png", bbox_inches="tight")
buf.seek(0)
st.download_button(
    label="Export Plot",
    data=buf,
    file_name=f"agency_funding.png",
    mime="image/png"
)

dashboard_type = st.selectbox("Select Agency:", ["All", "CIHR", "NSERC", "SSHRC"])

data = TRIAGENCY_DATA.copy()

if dashboard_type == "All":
    data = TRIAGENCY_DATA
elif dashboard_type == "CIHR":
    data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "CIHR"]
elif dashboard_type == "NSERC":
    data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "NSERC"]
elif dashboard_type == "SSHRC":
    data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "SSHRC"]


st.subheader(f"University Funding Over Time for Agency: {dashboard_type}")
column1, column2, _, = st.columns(3)
with column1:
    specific_u15 = st.checkbox("Select U15 Universities")
with column2:
    display_market = st.checkbox("Display Market Share")


fig = plt.figure(figsize=(12, 6))
if specific_u15:
    u15_selected = st.multiselect("Select Universities", ["Simon Fraser University"] + U15)

    if display_market:
        years = sorted(data["CompetitionFY"].unique())
        for u15_uni in u15_selected:
            u15_funding = []
            for year in years:
                year_data = data[data["CompetitionFY"] == year]
                u15_funding.append((year_data[year_data["Institution"] == u15_uni]["Total_Amount"].sum() / year_data["Total_Amount"].sum()) * 100)
            plt.plot(years, u15_funding, label=u15_uni, marker='o')
    
    else:
        for u15_uni in u15_selected:
            u15_by_year = (data[data["Institution"] == u15_uni].groupby('CompetitionFY')['Total_Amount'].sum())
            plt.plot(u15_by_year.index, u15_by_year.values, label=u15_uni, marker='o')
    
else:
    if display_market:
        years = sorted(data["CompetitionFY"].unique())
        sfu_funding = []
        u15_mean_funding = []

        for year in years:
            year_data = data[data["CompetitionFY"] == year]
            sfu_funding.append((year_data[year_data["Institution"] == "Simon Fraser University"]["Total_Amount"].sum() / year_data["Total_Amount"].sum()) * 100)
            u15_mean_funding.append(((year_data[year_data["Institution"].isin(U15)]["Total_Amount"].sum() / len(U15)) / year_data["Total_Amount"].sum()) * 100)
        plt.plot(years, sfu_funding, label='SFU', marker='o')
        plt.plot(years, u15_mean_funding, label="U15 Mean", marker='o')

    else:
        sfu_by_year = data[data["Institution"] == "Simon Fraser University"].groupby('CompetitionFY')['Total_Amount'].sum()
        u15_by_year = (data[data["Institution"].isin(U15)].groupby('CompetitionFY')['Total_Amount'].sum()/len(U15))
        plt.plot(sfu_by_year.index, sfu_by_year.values, label='SFU', marker='o')
        plt.plot(u15_by_year.index, u15_by_year.values, label="U15 Mean", marker='o')

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

buf = io.BytesIO()
fig.savefig(buf, format="png", bbox_inches="tight")
buf.seek(0)
st.download_button(
    label="Export Plot",
    data=buf,
    file_name=f"{dashboard_type}_university_funding.png",
    mime="image/png"
)

st.title("Table Dashboard")

agency_market_share = []
select_year_mode = st.selectbox("Select year range type:", ["Single Year", "Range of Years", "Compare Years"])
if select_year_mode == "Single Year":
    year = st.selectbox("Select Year:", sorted(data['CompetitionFY'].unique()))

    st.write(f"Total Agency Funding: {millify(data[(data['CompetitionFY'] == year)]['Total_Amount'].sum(), precision=2)}")

    sfu_total_amount = (data[(data["Institution"] == "Simon Fraser University") & (data['CompetitionFY']== year)]["Total_Amount"].sum())
    sfu_market_share = ((sfu_total_amount / data[(data['CompetitionFY'] == year)]["Total_Amount"].sum()) * 100)
    agency_market_share.append({"University": "Simon Fraser University", "Grant Amount": f"{millify(sfu_total_amount, precision=2)}", "Market Share (%)": f"{sfu_market_share:.2f}%"})

    for u15_university in U15:
        total_u15_amount = (data[(data["Institution"] == u15_university) & (data['CompetitionFY'] == year)]["Total_Amount"].sum())
        market_share = ((total_u15_amount / data[(data['CompetitionFY'] == year)]["Total_Amount"].sum()) * 100)
        agency_market_share.append({"University": u15_university, "Grant Amount": f"{millify(total_u15_amount, precision=2)}", "Market Share (%)": f"{market_share:.2f}%"})
    

elif select_year_mode == "Range of Years":
    column1, column2 = st.columns(2)

    with column1:
        from_year = st.selectbox("Select From Year:", sorted(data['CompetitionFY'].unique()))
    with column2:
        to_year = st.selectbox("Select To Year:", sorted(data['CompetitionFY'].unique(), reverse=True))

    st.write(f"Total Agency Funding: {millify(data[(data['CompetitionFY'] >= from_year) & (data['CompetitionFY'] <= to_year)]['Total_Amount'].sum(), precision=2)}")

    sfu_total_amount = (data[(data["Institution"] == "Simon Fraser University") & (data['CompetitionFY'] >= from_year) & (data['CompetitionFY'] <= to_year)]["Total_Amount"].sum())
    sfu_market_share = ((sfu_total_amount / data[(data['CompetitionFY'] >= from_year) & (data['CompetitionFY'] <= to_year)]["Total_Amount"].sum()) * 100)
    agency_market_share.append({"University": "Simon Fraser University", "Grant Amount": f"{millify(sfu_total_amount, precision=2)}", "Market Share (%)": f"{sfu_market_share:.2f}%"})

    for u15_university in U15:
        total_u15_amount = (data[(data["Institution"] == u15_university) & (data['CompetitionFY'] >= from_year) & (data['CompetitionFY'] <= to_year)]["Total_Amount"].sum())
        market_share = ((total_u15_amount / data[(data['CompetitionFY'] >= from_year) & (data['CompetitionFY'] <= to_year)]["Total_Amount"].sum()) * 100)
        agency_market_share.append({"University": u15_university, "Grant Amount": f"{millify(total_u15_amount, precision=2)}", "Market Share (%)": f"{market_share:.2f}%"})

elif select_year_mode == "Compare Years":
    column1, column2 = st.columns(2)

    with column1:
        year1 = st.selectbox("Select Year 1:", sorted(data['CompetitionFY'].unique()))
    with column2:
        year2 = st.selectbox("Select Year 2:", sorted(data['CompetitionFY'].unique()))

    st.write(f"Difference in Agency Funding: {millify(data[(data['CompetitionFY'] == year2)]['Total_Amount'].sum() - data[(data['CompetitionFY'] == year1)]['Total_Amount'].sum(), precision=2)}")
    
    sfu_year1_total = (data[(data["Institution"] == "Simon Fraser University") & (data['CompetitionFY']== year1)]["Total_Amount"].sum())
    sfu_year2_total = (data[(data["Institution"] == "Simon Fraser University") & (data['CompetitionFY']== year2)]["Total_Amount"].sum())

    sfu_year1_market_share = ((sfu_year1_total / data[(data['CompetitionFY'] == year1)]["Total_Amount"].sum()) * 100)
    sfu_year2_market_share = ((sfu_year2_total / data[(data['CompetitionFY'] == year2)]["Total_Amount"].sum()) * 100)

    agency_market_share.append({"University": "Simon Fraser University", "Change in Grant Amount ($)": sfu_year2_total - sfu_year1_total, "Change in Market Share (%)": sfu_year2_market_share - sfu_year1_market_share})

    for u15_university in U15:
        u15_year1_total = (data[(data["Institution"] == u15_university) & (data['CompetitionFY']== year1)]["Total_Amount"].sum())
        u15_year2_total = (data[(data["Institution"] == u15_university) & (data['CompetitionFY']== year2)]["Total_Amount"].sum())

        u15_year1_market_share = ((u15_year1_total / data[(data['CompetitionFY'] == year1)]["Total_Amount"].sum()) * 100)
        u15_year2_market_share = ((u15_year2_total / data[(data['CompetitionFY'] == year2)]["Total_Amount"].sum()) * 100)

        agency_market_share.append({"University": u15_university, "Change in Grant Amount ($)": u15_year2_total - u15_year1_total, "Change in Market Share (%)": u15_year2_market_share - u15_year1_market_share})

if select_year_mode == "Compare Years":
    # Display the market share list in a table
    market_share_table = pd.DataFrame(agency_market_share)
    market_share_table["Change in Grant Amount ($)"] = market_share_table["Change in Grant Amount ($)"].apply(lambda x: f'<span style="color: red;">{millify(x)}</span>' if x < 0 else f'<span style="color: green;">{millify(x)}</span>')
    # market_share_table["Change in Grant Amount ($)"] = market_share_table["Change in Grant Amount ($)"].apply(lambda x: millify(x))
    market_share_table["Change in Market Share (%)"] = market_share_table["Change in Market Share (%)"].apply(lambda x: f'<span style="color: red;">{x:.2f}%</span>' if x < 0 else f'<span style="color: green;">{x:.2f}%</span>')
    
    st.markdown(market_share_table.to_html(escape=False), unsafe_allow_html=True)
    
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

    st.download_button(
        label="Export Table as CSV",
        data=market_share_table.to_csv(index=False),
        file_name=f"{dashboard_type}_market_share_data.csv",
        mime="text/csv"
    )

