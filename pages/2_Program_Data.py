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

label = st.selectbox("Select Program:", program_labels)

data_label = agency_data[agency_data["Program_Name"] == label]

select_year_mode = st.selectbox("Select year range type:", ["Single Year", "Range of Years", "Compare Years"])
years_list = agency_data['CompetitionFY'].unique()

table_data = []

if select_year_mode == "Single Year":
    year = st.selectbox("Select Year:", sorted(years_list))
    data = data_label[data_label["CompetitionFY"] == year]
    
    data_sfu = data[data['Institution'] == "Simon Fraser University"]
    total_amount_sfu = data_sfu['Total_Amount'].sum()
    market_share_sfu = total_amount_sfu / data['Total_Amount'].sum() * 100
    num_grants_sfu = data_sfu['Total_Amount'].count()
    avg_grant_amount_sfu = data_sfu['Total_Amount'].mean()

    table_data.append(["Simon Fraser University", millify(total_amount_sfu, precision=1), millify(market_share_sfu, precision=1), num_grants_sfu, millify(avg_grant_amount_sfu, precision=1)])
    
    for u15 in U15:
        data_u15 = data[data['Institution'] == u15]

        total_amount_u15 = data_u15['Total_Amount'].sum()
        market_share_u15 = total_amount_u15 / data['Total_Amount'].sum() * 100
        num_grants_u15 = data_u15['Total_Amount'].count()
        avg_grant_amount_u15 = data_u15['Total_Amount'].mean()

        table_data.append([u15, millify(total_amount_u15, precision=1), millify(market_share_u15, precision=1), num_grants_u15, millify(avg_grant_amount_u15, precision=1)])

    columns = ["Institution", "Total Amount ($)", "Market Share (%)", "Number of Awards", "Avg Award Amount ($)"]

    df = pd.DataFrame(table_data, columns=columns)
    st.table(df)

    st.download_button(
        label="Export Table as CSV",
        data=pd.DataFrame(table_data, columns=columns).to_csv(index=False),
        file_name=f"{dashboard_type}_{field_type}_marketshare_data.csv",
        mime="text/csv"
    )

elif select_year_mode == "Range of Years":
    start_year = st.selectbox("Select Start Year:", sorted(years_list))
    end_year = st.selectbox("Select End Year:", sorted(years_list))

    data = data_label[(data_label["CompetitionFY"] >= start_year) & (data_label["CompetitionFY"] <= end_year)]

    data_sfu = data[data['Institution'] == "Simon Fraser University"]
    total_amount_sfu = data_sfu['Total_Amount'].sum()
    market_share_sfu = total_amount_sfu / data['Total_Amount'].sum() * 100
    num_grants_sfu = data_sfu['Total_Amount'].count()
    avg_grant_amount_sfu = data_sfu['Total_Amount'].mean()

    table_data.append(["Simon Fraser University", millify(total_amount_sfu, precision=1), millify(market_share_sfu, precision=1), num_grants_sfu, millify(avg_grant_amount_sfu, precision=1)])
    
    for u15 in U15:
        data_u15 = data[data['Institution'] == u15]

        total_amount_u15 = data_u15['Total_Amount'].sum()
        market_share_u15 = total_amount_u15 / data['Total_Amount'].sum() * 100
        num_grants_u15 = data_u15['Total_Amount'].count()
        avg_grant_amount_u15 = data_u15['Total_Amount'].mean()

        table_data.append([u15, millify(total_amount_u15, precision=1), millify(market_share_u15, precision=1), num_grants_u15, millify(avg_grant_amount_u15, precision=1)])

    columns = ["Institution", "Total Amount ($)", "Market Share (%)", "Number of Awards", "Avg Award Amount ($)"]

    df = pd.DataFrame(table_data, columns=columns)
    st.table(df)

    st.download_button(
        label="Export Table as CSV",
        data=pd.DataFrame(table_data, columns=columns).to_csv(index=False),
        file_name=f"{dashboard_type}_{field_type}_marketshare_data.csv",
        mime="text/csv"
    )

elif select_year_mode == "Compare Years"
    year1 = st.selectbox("Select Year1:", sorted(years_list))
    year2 = st.selectbox("Select Year2:", sorted(years_list))

    data_year1 = data_label[data_label["CompetitionFY"] == year1]
    data_year2 = data_label[data_label["CompetitionFY"] == year2]

    data_sfu_year1 = data_year1[data_year1['Institution'] == "Simon Fraser University"]
    data_sfu_year2 = data_year2[data_year2['Institution'] == "Simon Fraser University"]

    total_amount_sfu_year1 = data_sfu_year1['Total_Amount'].sum()
    total_amount_sfu_year2 = data_sfu_year2['Total_Amount'].sum()

    market_share_sfu_year1 = total_amount_sfu_year1 / data_year1['Total_Amount'].sum() * 100
    market_share_sfu_year2 = total_amount_sfu_year2 / data_year2['Total_Amount'].sum() * 100

    num_grants_sfu_year1 = data_sfu_year1['Total_Amount'].count()
    num_grants_sfu_year2 = data_sfu_year2['Total_Amount'].count()

    avg_grant_amount_sfu_year1 = data_sfu_year1['Total_Amount'].mean()
    avg_grant_amount_sfu_year2 = data_sfu_year2['Total_Amount'].mean()

    table_data.append(["Simon Fraser University", data_sfu_year2 - data_sfu_year1, market_share_sfu_year2 - market_share_sfu_year1,
                       num_grants_sfu_year2 - num_grants_sfu_year1, avg_grant_amount_sfu_year2 - avg_grant_amount_sfu_year1])  

    for u15 in U15:
        data_u15_year1 = data_year1[data_year1['Institution'] == u15]
        data_u15_year2 = data_year2[data_year2['Institution'] == u15]

        total_amount_u15_year1 = data_u15_year1['Total_Amount'].sum()
        total_amount_u15_year2 = data_u15_year2['Total_Amount'].sum()

        market_share_u15_year1 = total_amount_u15_year1 / data_year1['Total_Amount'].sum() * 100        
        market_share_u15_year2 = total_amount_u15_year2 / data_year2['Total_Amount'].sum() * 100

        num_grants_u15_year1 = data_u15_year1['Total_Amount'].count()
        num_grants_u15_year2 = data_u15_year2['Total_Amount'].count()

        avg_grant_amount_u15_year1 = data_u15_year1['Total_Amount'].mean()
        avg_grant_amount_u15_year2 = data_u15_year2['Total_Amount'].mean()

        table_data.append([u15, total_amount_u15_year2 - total_amount_u15_year1, market_share_u15_year2 - market_share_u15_year1, num_grants_u15_year2 - num_grants_u15_year1, avg_grant_amount_u15_year2 - avg_grant_amount_u15_year1]) 

    # Create a DataFrame from the table data
    df = pd.DataFrame(table_data, columns=["University", "Total Amount Change ($)", "Market Share Change (%)", "Number of Grants Change", "Average Grant Amount Change ($)"])
    
    df["Total Amount Change ($)"] = df["Total Amount Change ($)"].apply(lambda x: f'<span style="color: red;">{millify(x, precision=1)}</span>' if x < 0 else f'<span style="color: green;">{millify(x, precision=1)}</span>')
    df["Market Share Change (%)"] = df["Market Share Change (%)"].apply(lambda x: f'<span style="color: red;">{millify(x, precision=1)}</span>' if x < 0 else f'<span style="color: green;">{millify(x, precision=1)}</span>')
    df["Number of Grants Change"] = df["Number of Grants Change"].apply(lambda x: f'<span style="color: red;">{millify(x, precision=1)}</span>' if x < 0 else f'<span style="color: green;">{millify(x, precision=1)}</span>')
    df["Average Grant Amount Change ($)"] = df["Average Grant Amount Change ($)"].apply(lambda x: f'<span style="color: red;">{millify(x, precision=1)}</span>' if x < 0 else f'<span style="color: green;">{millify(x, precision=1)}</span>')

    st.markdown(df.to_html(escape=False), unsafe_allow_html=True)
    st.download_button(
        label="Export Table as CSV",
        data=pd.DataFrame(table_data, columns=columns).to_csv(index=False),
        file_name=f"{dashboard_type}_{field_type}_marketshare_data.csv",
        mime="text/csv"
    )


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