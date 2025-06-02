# dashboard/app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from millify import millify

U15 = ["University of Alberta", "University of British Columbia", "University of Calgary", "Dalhousie University", "Université Laval", 
       "University of Manitoba", "McGill University", "McMaster University", "Université de Montréal", "University of Ottawa", 
       "Queen's University", "University of Saskatchewan", "University of Toronto", "University of Waterloo", "University of Western Ontario"]

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
plt.plot(u15_by_year.index, u15_by_year.values, label="U15 mean", marker='o')
plt.title("Grant Funding Over Time")
plt.xlabel("CompetitionFY")
plt.ylabel("Total Funding Amount")
plt.legend()
plt.grid(True)

st.pyplot(fig)
st.title("Market Share Dashboard")

# Add button to switch between dashboards
dashboard_type = st.selectbox("Select Agency (for market share):", ["All", "CIHR", "NSERC", "SSHRC"])

data = TRIAGENCY_DATA.copy()

if dashboard_type == "All":
    data = TRIAGENCY_DATA
elif dashboard_type == "CIHR":
    data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "CIHR"]
elif dashboard_type == "NSERC":
    data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "NSERC"]
elif dashboard_type == "SSHRC":
    data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "SSHRC"]

# Create a table of U15 universities and SFU's market share given the agency
from_year = st.selectbox("Select From Year:", sorted(data['CompetitionFY'].unique()))
to_year = st.selectbox("Select To Year:", sorted(data['CompetitionFY'].unique()))

agency_market_share = []
sfu_total_amount = (data[(data["Institution"] == "Simon Fraser University") & (data['CompetitionFY'] >= from_year) & (data['CompetitionFY'] <= to_year)]["Total_Amount"].sum())
sfu_market_share = ((sfu_total_amount / data[(data['CompetitionFY'] >= from_year) & (data['CompetitionFY'] <= to_year)]["Total_Amount"].sum()) * 100)
agency_market_share.append({"University": "Simon Fraser University", "Market Share (%)": f"{sfu_market_share:.2f}"})

for u15_university in U15:
    total_u15_amount = (data[(data["Institution"] == u15_university) & (data['CompetitionFY'] >= from_year) & (data['CompetitionFY'] <= to_year)]["Total_Amount"].sum())
    total_agency_amount = data[(data['CompetitionFY'] >= from_year) & (data['CompetitionFY'] <= to_year)]["Total_Amount"].sum()
    market_share = ((total_u15_amount / total_agency_amount) * 100)
    agency_market_share.append({"University": u15_university, "Market Share (%)": f"{market_share:.2f}"})
    

# Display the market share list in a table
st.markdown(f"#### Market Share by University Given Agency: {dashboard_type}")
market_share_table = pd.DataFrame(agency_market_share)
st.write(market_share_table.style.set_properties(**{'text-align': 'left'}))

st.title("Main Discipline Market Share")

dashboard_type = st.selectbox("Select Agency (for discipline share):", ["All", "CIHR", "NSERC", "SSHRC"])

data = TRIAGENCY_DATA.copy()

if dashboard_type == "All":
    data = TRIAGENCY_DATA
elif dashboard_type == "CIHR":
    data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "CIHR"]
elif dashboard_type == "NSERC":
    data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "NSERC"]
elif dashboard_type == "SSHRC":
    data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "SSHRC"]


# Create piecharts below
fig, ax = plt.subplots()
data = data.groupby('Main_Discipline')['Total_Amount'].sum().nlargest(10)
colors_mpl = plt.cm.tab20.colors[:len(data.index)]
ax.pie(data.values, colors=colors_mpl, labels=None, autopct='%1.1f%%', startangle=90)
# ax.pie(data.values, labels=None, autopct='%1.1f%%', startangle=90, pctdistance=0.85)

# Move the labels outside the pie chart by increasing the labeldistance
plt.legend(labels=data.index, loc="center left", bbox_to_anchor=(1.0, 0.8))

# plt.title('CIHR Funding Distribution')
st.pyplot(fig)