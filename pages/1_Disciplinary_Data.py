import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from millify import millify

st.set_page_config(page_title="Disiplinary Data", page_icon="")

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

field_type = st.selectbox("Select Field:", ["Main Discipline", "Area of Research"])
if field_type == "Main Discipline":
    field = "Main_Discipline"
elif field_type == "Area of Research":
    field = "Area_of_Research"


if dashboard_type == "CIHR":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "CIHR"].copy()
elif dashboard_type == "NSERC":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "NSERC"].copy()
elif dashboard_type == "SSHRC":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "SSHRC"].copy()

table_data = []

st.title(f"{field_type} Trends for {dashboard_type}")

# discipline_revenue = agency_data.groupby(field)['Total_Amount'].sum().nlargest(10).reset_index()
custom_labels = st.checkbox("Use custom labels")
if custom_labels:
    discipline_revenue = agency_data.groupby(field)['Total_Amount'].sum()
    discipline_labels = st.multiselect('Select disciplines', sorted(discipline_revenue.reset_index()[field].unique()), default=discipline_revenue.nlargest(10).reset_index()[field])
else:
    discipline_revenue = agency_data.groupby(field)['Total_Amount'].sum().nlargest(10).reset_index()
    discipline_labels = sorted(discipline_revenue[field].unique())

fig = plt.figure(figsize=(12, 6))
for label in discipline_labels:
    grouped_label = agency_data[agency_data[field] == label].groupby('CompetitionFY')['Total_Amount'].sum().reset_index()
    plt.plot(grouped_label['CompetitionFY'], grouped_label['Total_Amount'], label=label, marker='o')
plt.title(f"{field_type} Trends for {dashboard_type}")
plt.ylabel("Total Funding Amount")
plt.xlabel("CompetitionFY")
plt.grid(True)
plt.legend()

st.pyplot(fig)


st.title(f"{field_type} Market Share")

select_year_mode = st.selectbox("Select year range type:", ["Single Year", "Range of Years", "Compare Years"])
years_list = agency_data['CompetitionFY'].unique()

if select_year_mode == "Single Year":
    year = st.selectbox("Select Year:", sorted(years_list))
    data = agency_data[agency_data["CompetitionFY"] == year]
    
    # Main Discipline
    data = data.groupby(field)['Total_Amount'].sum().nlargest(10).reset_index()
    discipline_labels = sorted(data[field].unique())

    for label in discipline_labels:
        md_label_data = data[data[field] == label]
        table_data.append([label, millify(md_label_data['Total_Amount'].sum(), precision=1), millify(md_label_data['Total_Amount'].sum()/data['Total_Amount'].sum()*100, precision=1)])
    columns = [field_type, 'Year Amount ($)', 'Market Share (%)']

    data = data.groupby(field)['Total_Amount'].sum().nlargest(10) # should be a faster way to do this

elif select_year_mode == "Range of Years":
    column1, column2 = st.columns(2)

    with column1:
        year1 = st.selectbox("Select Year1:", sorted(years_list))
    with column2:
        year2 = st.selectbox("Select Year2:", sorted(years_list))
    data = agency_data[(agency_data["CompetitionFY"] >= year1) & (agency_data["CompetitionFY"] <= year2)]

    # Main Discipline
    data = data.groupby(field)['Total_Amount'].sum().nlargest(10).reset_index()
    discipline_labels = sorted(data[field].unique())

    for label in discipline_labels:
        md_label_data = data[data[field] == label]
        table_data.append([label, millify(md_label_data['Total_Amount'].sum(), precision=1), millify(md_label_data['Total_Amount'].sum()/data['Total_Amount'].sum()*100, precision=1)])
    columns = [field_type, 'Year Amount ($)', 'Market Share (%)']

    data = data.groupby(field)['Total_Amount'].sum().nlargest(10)

elif select_year_mode == "Compare Years":
    column1, column2 = st.columns(2)

    with column1:
        year1 = st.selectbox("Select Year1:", sorted(years_list))
    with column2:
        year2 = st.selectbox("Select Year2:", sorted(years_list))

    data_year1 = agency_data[agency_data["CompetitionFY"] == year1]
    data_year2 = agency_data[agency_data["CompetitionFY"] == year2]

    data = agency_data[agency_data["CompetitionFY"] == year2]

    # Main Discipline
    data_year1 = data_year1.groupby(field)['Total_Amount'].sum().reset_index()
    data_year2 = data_year2.groupby(field)['Total_Amount'].sum().nlargest(10).reset_index()

    discipline_labels = sorted(data_year2[field].unique())

    for label in discipline_labels:
        data_label_year1 = data_year1[data_year1[field] == label]
        data_label_year2 = data_year2[data_year2[field] == label]

        change = ((data_label_year2["Total_Amount"].sum() - data_label_year1["Total_Amount"].sum()) / data_label_year1["Total_Amount"].sum()) * 100
        color = "red" if change > 0 else "green"
        table_data.append([label, millify(data_label_year1['Total_Amount'].sum(), precision=1), millify(data_label_year2['Total_Amount'].sum(), precision=1), change])
    columns = [field_type, 'Year1 Amount ($)', 'Year2 Amount ($)', 'Change (%)']

    data = data.groupby(field)['Total_Amount'].sum().nlargest(10)

if select_year_mode == "Compare Years":
    st.write(f"{field_type} Market Share Table")
    
    df = pd.DataFrame(table_data, columns=columns)
    df["Change (%)"] = df["Change (%)"].apply(lambda x: f'<span style="color: red;">{x:.2f}%</span>' if x < 0 else f'<span style="color: green;">{x:.2f}%</span>')
    st.markdown(df.to_html(escape=False), unsafe_allow_html=True)

else:
    st.write(f"{field_type} Market Share Pie Chart")

    fig, ax = plt.subplots()
    colors_mpl = plt.cm.tab20.colors[:len(data.index)]
    ax.pie(data.values, colors=colors_mpl, labels=None, autopct='%1.1f%%', startangle=90)
    plt.legend(labels=data.index, loc="center left", bbox_to_anchor=(1.0, 0.8))
    st.pyplot(fig)

    display_table = st.checkbox("Display Table")
    if display_table:
        st.write(f"{field_type} Market Share Table")
        df = pd.DataFrame(table_data, columns=columns)
        st.markdown(df.to_html(escape=False), unsafe_allow_html=True)

selected_university = st.selectbox("Select University:", ["Simon Fraser University"] + U15)
university_data = agency_data[agency_data['Institution'] == selected_university]

# Main Discipline
discipline_revenue = university_data.groupby(field)['Total_Amount'].sum()
discipline_labels = st.multiselect('Select disciplines', discipline_revenue.reset_index()[field].unique(), default=discipline_revenue.nlargest(10).reset_index()[field])

fig = plt.figure(figsize=(12, 6))
for label in discipline_labels:
    grouped_label = university_data[university_data[field] == label].groupby('CompetitionFY')['Total_Amount'].sum().reset_index()
    plt.plot(grouped_label['CompetitionFY'], grouped_label['Total_Amount'], label=label, marker='o')
plt.title(f"Disciplinary Funding for {selected_university}")
plt.ylabel("Total Funding Amount")
plt.xlabel("CompetitionFY")
plt.grid(True)
plt.legend()

st.pyplot(fig)