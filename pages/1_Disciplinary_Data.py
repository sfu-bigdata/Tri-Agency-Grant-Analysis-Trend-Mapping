import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from millify import millify

st.set_page_config(page_title="Disiplinary Data", page_icon="")

U15 = ["University of Alberta", "University of British Columbia", "University of Calgary", "Dalhousie University", "Université Laval", 
       "University of Manitoba", "McGill University", "McMaster University", "Université de Montréal", "University of Ottawa", 
       "Queen's University", "University of Saskatchewan", "University of Toronto", "University of Waterloo", "University of Western Ontario"]

# Load and clean data
TRIAGENCY_DATA = pd.read_csv("clean_data/TRIAGENCY_DATA.csv")
U15_DATA = TRIAGENCY_DATA[TRIAGENCY_DATA["Institution"].isin(U15)]
SFU_DATA = TRIAGENCY_DATA[TRIAGENCY_DATA["Institution"] == "Simon Fraser University"]

dashboard_type = st.selectbox("Select Agency:", ["CIHR", "NSERC", "SSHRC"])

# if dashboard_type == "All":
#     agency_data = TRIAGENCY_DATA.copy()
if dashboard_type == "CIHR":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "CIHR"].copy()
elif dashboard_type == "NSERC":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "NSERC"].copy()
elif dashboard_type == "SSHRC":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "SSHRC"].copy()

select_year_mode = st.selectbox("Select year range type:", ["Single Year", "Range of Years", "Compare Years"])

years_list = agency_data['CompetitionFY'].unique()

md_table_data = []
ar_table_data = []
if select_year_mode == "Single Year":
    year = st.selectbox("Select Year:", sorted(years_list))
    data = agency_data[agency_data["CompetitionFY"] == year]
    
    # Main Discipline
    md_data = data.groupby('Main_Discipline')['Total_Amount'].sum().nlargest(10).reset_index()
    discipline_labels = sorted(md_data["Main_Discipline"].unique())

    for label in discipline_labels:
        md_label_data = md_data[md_data["Main_Discipline"] == label]
        md_table_data.append([label, millify(md_label_data['Total_Amount'].sum()), millify(md_label_data['Total_Amount'].sum()/md_data['Total_Amount'].sum()*100)])
    md_columns = ['Main Discipline', 'Year Amount ($)', 'Market Share (%)']

    md_data = data.groupby('Main_Discipline')['Total_Amount'].sum().nlargest(10) # should be a faster way to do this

    # Area of Research
    ar_data = data.groupby('Area_of_Research')['Total_Amount'].sum().nlargest(10).reset_index()
    research_labels = sorted(ar_data["Area_of_Research"].unique())

    for label in research_labels:
        ar_label_data = ar_data[ar_data["Area_of_Research"] == label]
        ar_table_data.append([label, millify(ar_label_data['Total_Amount'].sum()), millify(ar_label_data['Total_Amount'].sum()/ar_data['Total_Amount'].sum()*100)])
    ar_columns = ['Area of Research', 'Year Amount ($)', 'Market Share (%)']

    ar_data = data.groupby('Area_of_Research')['Total_Amount'].sum().nlargest(10) # should be a faster way to do this

elif select_year_mode == "Range of Years":
    year1 = st.selectbox("Select Year1:", sorted(years_list))
    year2 = st.selectbox("Select Year2:", sorted(years_list))
    data = agency_data[(agency_data["CompetitionFY"] >= year1) & (agency_data["CompetitionFY"] <= year2)]

    # Main Discipline
    md_data = data.groupby('Main_Discipline')['Total_Amount'].sum().nlargest(10).reset_index()
    discipline_labels = sorted(md_data["Main_Discipline"].unique())

    for label in discipline_labels:
        md_label_data = md_data[md_data["Main_Discipline"] == label]
        md_table_data.append([label, millify(md_label_data['Total_Amount'].sum()), millify(md_label_data['Total_Amount'].sum()/md_data['Total_Amount'].sum()*100)])
    md_columns = ['Main Discipline', 'Year Amount ($)', 'Market Share (%)']

    md_data = data.groupby('Main_Discipline')['Total_Amount'].sum().nlargest(10)

    # Area of Research
    ar_data = data.groupby('Area_of_Research')['Total_Amount'].sum().nlargest(10).reset_index()
    research_labels = sorted(ar_data["Area_of_Research"].unique())
    for label in research_labels:
        ar_label_data = ar_data[ar_data["Area_of_Research"] == label]
        ar_table_data.append([label, millify(ar_label_data['Total_Amount'].sum()), millify(ar_label_data['Total_Amount'].sum()/ar_data['Total_Amount'].sum()*100)])
    ar_columns = ['Area of Research', 'Year Amount ($)', 'Market Share (%)']

    ar_data = data.groupby('Area_of_Research')['Total_Amount'].sum().nlargest(10)

elif select_year_mode == "Compare Years":
    year1 = st.selectbox("Select Year1:", sorted(years_list))
    year2 = st.selectbox("Select Year2:", sorted(years_list))

    data_year1 = agency_data[agency_data["CompetitionFY"] == year1]
    data_year2 = agency_data[agency_data["CompetitionFY"] == year2]

    data = agency_data[agency_data["CompetitionFY"] == year2]

    # Main Discipline
    md_data_year1 = data_year1.groupby('Main_Discipline')['Total_Amount'].sum().nlargest(50).reset_index()
    md_data_year2 = data_year2.groupby('Main_Discipline')['Total_Amount'].sum().nlargest(10).reset_index()

    discipline_labels = sorted(md_data_year2["Main_Discipline"].unique())

    for label in discipline_labels:
        data_label_year1 = md_data_year1[md_data_year1["Main_Discipline"] == label]
        data_label_year2 = md_data_year2[md_data_year2["Main_Discipline"] == label]

        change = ((data_label_year2["Total_Amount"].sum() - data_label_year1["Total_Amount"].sum()) / data_label_year1["Total_Amount"].sum()) * 100
        color = "red" if change > 0 else "green"
        md_table_data.append([label, millify(data_label_year1['Total_Amount'].sum()), millify(data_label_year2['Total_Amount'].sum()), f"<style><font color='{color}'>{change:.2f}%</font></style>"])
    md_columns = ['Main Discipline', 'Year1 Amount ($)', 'Year2 Amount ($)', 'Change (%)']

    md_data = data.groupby('Main_Discipline')['Total_Amount'].sum().nlargest(10)

    # Area of Research
    ar_data_year1 = data_year1.groupby('Area_of_Research')['Total_Amount'].sum().nlargest(50).reset_index()
    ar_data_year2 = data_year2.groupby('Area_of_Research')['Total_Amount'].sum().nlargest(10).reset_index()

    research_labels = sorted(ar_data_year2["Area_of_Research"].unique())

    # ar_table_data = []
    for label in research_labels:
        data_label_year1 = ar_data_year1[ar_data_year1["Area_of_Research"] == label]
        data_label_year2 = ar_data_year2[ar_data_year2["Area_of_Research"] == label]

        change = ((data_label_year2["Total_Amount"].sum() - data_label_year1["Total_Amount"].sum()) / data_label_year1["Total_Amount"].sum()) * 100
        color = "red" if change > 0 else "green"
        ar_table_data.append([label, millify(data_label_year1['Total_Amount'].sum()), millify(data_label_year2['Total_Amount'].sum()), f"<style><font color='{color}'>{change:.2f}%</font></style>"])
    ar_columns = ['Area of Research', 'Year1 Amount ($)', 'Year2 Amount ($)', 'Change (%)']

    ar_data = data.groupby('Area_of_Research')['Total_Amount'].sum().nlargest(10)


st.title("Main Discipline Market Share")

st.write("Yearly Comparison")

st.write(pd.DataFrame(md_table_data, columns=md_columns).style.set_properties(**{'text-align': 'left'}))

if select_year_mode == "Compare Years":
    st.write(f"Discipline {year2} Market Share")
else:
    st.write(f"Discipline Market Share")
fig, ax = plt.subplots()

colors_mpl = plt.cm.tab20.colors[:len(md_data.index)]
ax.pie(md_data.values, colors=colors_mpl, labels=None, autopct='%1.1f%%', startangle=90)

plt.legend(labels=md_data.index, loc="center left", bbox_to_anchor=(1.0, 0.8))

st.pyplot(fig)

st.title("Top 10 Areas of Research")

st.write(pd.DataFrame(ar_table_data, columns=ar_columns).style.set_properties(**{'text-align': 'left'}))

if select_year_mode == "Compare Years":
    st.write(f"Research {year2} Market Share")
else:
    st.write(f"Research Market Share")
fig, ax = plt.subplots()

# Create piecharts below
fig, ax = plt.subplots()
colors_mpl = plt.cm.tab20.colors[:len(ar_data.index)]
ax.pie(ar_data.values, colors=colors_mpl, labels=None, autopct='%1.1f%%', startangle=90)
plt.legend(labels=ar_data.index, loc="center left", bbox_to_anchor=(1.0, 0.8))

st.pyplot(fig)