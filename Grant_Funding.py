import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from millify import millify

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

st.title("Grant Funding Dashboard")

# Add button to switch between dashboards
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

# Show metrics
sfu_revenue = millify(data[data["Institution"] == "Simon Fraser University"]["Total_Amount"].sum(), precision=2)
u15_avg_revenue = millify((data[data["Institution"].isin(U15)]["Total_Amount"].sum()/len(U15)), precision=2)

# Use Markdown to format the metrics string
metrics_string = f"SFU Revenue: {sfu_revenue}, Average U15 Revenue: {u15_avg_revenue}"
st.markdown(f"#### Metrics\n{metrics_string}")

# Create a graph
sfu_by_year = data[data["Institution"] == "Simon Fraser University"].groupby('CompetitionFY')['Total_Amount'].sum()
u15_by_year = (data[data["Institution"].isin(U15)].groupby('CompetitionFY')['Total_Amount'].sum()/len(U15))
fig = plt.figure(figsize=(12, 6))
plt.plot(sfu_by_year.index, sfu_by_year.values, label='SFU', marker='o')
plt.plot(u15_by_year.index, u15_by_year.values, label="U15 Mean", marker='o')
plt.title("Grant Funding Over Time")
plt.xlabel("CompetitionFY")
plt.ylabel("Total Funding Amount")
plt.legend()
plt.grid(True)
st.pyplot(fig)

st.title("Market Share Dashboard")

agency_market_share = []
select_year_mode = st.selectbox("Select year range type:", ["Single Year", "Range of Years", "Compare Years"])
if select_year_mode == "Single Year":
    year = st.selectbox("Select Year:", sorted(data['CompetitionFY'].unique()))

    sfu_total_amount = (data[(data["Institution"] == "Simon Fraser University") & (data['CompetitionFY']== year)]["Total_Amount"].sum())
    sfu_market_share = ((sfu_total_amount / data[(data['CompetitionFY'] == year)]["Total_Amount"].sum()) * 100)
    agency_market_share.append({"University": "Simon Fraser University", "Grant Amount": f"{millify(sfu_total_amount)}", "Market Share (%)": f"{sfu_market_share:.2f}"})

    for u15_university in U15:
        total_u15_amount = (data[(data["Institution"] == u15_university) & (data['CompetitionFY'] == year)]["Total_Amount"].sum())
        market_share = ((total_u15_amount / data[(data['CompetitionFY'] == year)]["Total_Amount"].sum()) * 100)
        agency_market_share.append({"University": u15_university, "Grant Amount": f"{millify(total_u15_amount)}", "Market Share (%)": f"{market_share:.2f}"})
    

elif select_year_mode == "Range of Years":
    column1, column2 = st.columns(2)

    with column1:
        from_year = st.selectbox("Select From Year:", sorted(data['CompetitionFY'].unique()))
    with column2:
        to_year = st.selectbox("Select To Year:", sorted(data['CompetitionFY'].unique(), reverse=True))

    sfu_total_amount = (data[(data["Institution"] == "Simon Fraser University") & (data['CompetitionFY'] >= from_year) & (data['CompetitionFY'] <= to_year)]["Total_Amount"].sum())
    sfu_market_share = ((sfu_total_amount / data[(data['CompetitionFY'] >= from_year) & (data['CompetitionFY'] <= to_year)]["Total_Amount"].sum()) * 100)
    agency_market_share.append({"University": "Simon Fraser University", "Grant Amount": f"{millify(sfu_total_amount)}", "Market Share (%)": f"{sfu_market_share:.2f}"})

    for u15_university in U15:
        total_u15_amount = (data[(data["Institution"] == u15_university) & (data['CompetitionFY'] >= from_year) & (data['CompetitionFY'] <= to_year)]["Total_Amount"].sum())
        market_share = ((total_u15_amount / data[(data['CompetitionFY'] >= from_year) & (data['CompetitionFY'] <= to_year)]["Total_Amount"].sum()) * 100)
        agency_market_share.append({"University": u15_university, "Grant Amount": f"{millify(total_u15_amount)}", "Market Share (%)": f"{market_share:.2f}"})

elif select_year_mode == "Compare Years":
    column1, column2 = st.columns(2)

    with column1:
        year1 = st.selectbox("Select Year 1:", sorted(data['CompetitionFY'].unique()))
    with column2:
        year2 = st.selectbox("Select Year 2:", sorted(data['CompetitionFY'].unique()))
    
    sfu_year1_total = (data[(data["Institution"] == "Simon Fraser University") & (data['CompetitionFY']== year1)]["Total_Amount"].sum())
    sfu_year2_total = (data[(data["Institution"] == "Simon Fraser University") & (data['CompetitionFY']== year2)]["Total_Amount"].sum())

    sfu_year1_market_share = ((sfu_year1_total / data[(data['CompetitionFY'] == year1)]["Total_Amount"].sum()) * 100)
    sfu_year2_market_share = ((sfu_year2_total / data[(data['CompetitionFY'] == year2)]["Total_Amount"].sum()) * 100)

    agency_market_share.append({"University": "Simon Fraser University", "Change in Grant Amount": f"{millify(sfu_year2_total - sfu_year1_total)}", "Change in Market Share (%)": f"{sfu_year2_market_share - sfu_year1_market_share :.2f}"})

    for u15_university in U15:
        u15_year1_total = (data[(data["Institution"] == u15_university) & (data['CompetitionFY']== year1)]["Total_Amount"].sum())
        u15_year2_total = (data[(data["Institution"] == u15_university) & (data['CompetitionFY']== year2)]["Total_Amount"].sum())

        u15_year1_market_share = ((u15_year1_total / data[(data['CompetitionFY'] == year1)]["Total_Amount"].sum()) * 100)
        u15_year2_market_share = ((u15_year2_total / data[(data['CompetitionFY'] == year2)]["Total_Amount"].sum()) * 100)

        agency_market_share.append({"University": u15_university, "Change in Grant Amount": f"{millify(u15_year2_total - u15_year1_total)}", "Change in Market Share (%)": f"{u15_year2_market_share - u15_year1_market_share:.2f}"})

# Display the market share list in a table
st.markdown(f"#### Market Share by University Given Agency: {dashboard_type}")
market_share_table = pd.DataFrame(agency_market_share)
st.write(market_share_table.style.set_properties(**{'text-align': 'left'}))

