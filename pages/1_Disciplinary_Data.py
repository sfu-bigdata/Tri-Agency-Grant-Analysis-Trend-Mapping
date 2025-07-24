import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from millify import millify
import io

st.set_page_config(page_title="Disiplinary Data", page_icon="")

U15 = ["University of Alberta", "University of British Columbia", "University of Calgary", "Dalhousie University", "Université Laval", 
       "University of Manitoba", "McGill University", "McMaster University", "Université de Montréal", "University of Ottawa", 
       "Queen's University", "University of Saskatchewan", "University of Toronto", "University of Waterloo", "University of Western Ontario"]

U15 = ["University of Alberta", "University of British Columbia", "University of Calgary", "Dalhousie University", "Université Laval", 
       "University of Manitoba", "McGill University", "McMaster University", "Université de Montréal", "University of Ottawa", 
       "Queen's University", "University of Saskatchewan", "University of Toronto", "University of Waterloo", "University of Western Ontario",
       "University of Victoria"] # U15 + UVic

# Load data
TRIAGENCY_DATA = pd.read_csv("clean_data/TRIAGENCY_DATA.csv")

# Select Agency & update Data
dashboard_type = st.selectbox("Select Agency:", ["CIHR", "NSERC", "SSHRC"])
if dashboard_type == "CIHR":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "CIHR"].copy()
elif dashboard_type == "NSERC":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "NSERC"].copy()
elif dashboard_type == "SSHRC":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "SSHRC"].copy()

# Select Field type
field_type = st.selectbox("Select Field:", ["Main Discipline", "Area of Research"])
if field_type == "Main Discipline":
    field = "Main_Discipline"
elif field_type == "Area of Research":
    field = "Area_of_Research"

# Discipline Trends
st.title(f"{field_type} Trends for {dashboard_type}")

custom_labels = st.checkbox("Use custom labels")
if custom_labels: # Use Specific Disciplines
    discipline_revenue = agency_data.groupby(field)['Total_Amount'].sum()
    discipline_labels = st.multiselect('Select disciplines', sorted(discipline_revenue.reset_index()[field].unique()), default=discipline_revenue.nlargest(10).reset_index()[field])

else: # Use Top 10 Disciplines by Revenue
    discipline_revenue = agency_data.groupby(field)['Total_Amount'].sum().nlargest(10).reset_index()
    discipline_labels = sorted(discipline_revenue[field].unique())

fig = plt.figure(figsize=(12, 6))
for label in discipline_labels: # plot each discipline
    grouped_label = agency_data[agency_data[field] == label].groupby('CompetitionFY')['Total_Amount'].sum().reset_index()
    plt.plot(grouped_label['CompetitionFY'], grouped_label['Total_Amount'], label=label, marker='o')
plt.title(f"{field_type} Trends for {dashboard_type}")
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
    file_name=f"{dashboard_type}_{field_type}_funding.png",
    mime="image/png"
)

# Pie Chart / Table for Market Share data
st.title(f"{field_type} Market Share")

table_data = []
years_list = agency_data['CompetitionFY'].unique()

# Select Year Mode
select_year_mode = st.selectbox("Select year range type:", ["Single Year", "Range of Years", "Compare Years"])
if select_year_mode == "Single Year":
    year = st.selectbox("Select Year:", sorted(years_list))
    data = agency_data[agency_data["CompetitionFY"] == year]
    
    # Select Top 10 Disciplines by Revenue
    discipline_labels = sorted((data.groupby(field)['Total_Amount'].sum().nlargest(10).reset_index())[field].unique())

    # Compute Table Data for each Discipline
    for label in discipline_labels:
        md_label_data = data[data[field] == label]
        table_data.append([label, millify(md_label_data['Total_Amount'].sum(), precision=1), millify(md_label_data['Total_Amount'].sum()/data['Total_Amount'].sum()*100, precision=1),
                           md_label_data['Total_Amount'].count(), millify(md_label_data['Total_Amount'].mean(), precision=1)])
    columns = [field_type, 'Total Amount ($)', 'Market Share (%)', 'Number of Awards', 'Avg Award Amount ($)']

    # Pie Chart Data
    data = data.groupby(field)['Total_Amount'].sum().nlargest(10)

elif select_year_mode == "Range of Years":
    column1, column2 = st.columns(2)

    with column1:
        year1 = st.selectbox("Select Year1:", sorted(years_list))
    with column2:
        year2 = st.selectbox("Select Year2:", sorted(years_list))
    data = agency_data[(agency_data["CompetitionFY"] >= year1) & (agency_data["CompetitionFY"] <= year2)]

    # Select Top 10 Disciplines by Revenue
    discipline_labels = sorted((data.groupby(field)['Total_Amount'].sum().nlargest(10).reset_index())[field].unique())

    # Compute Table Data for each Discipline
    for label in discipline_labels:
        md_label_data = data[data[field] == label]
        table_data.append([label, millify(md_label_data['Total_Amount'].sum(), precision=1), millify(md_label_data['Total_Amount'].sum()/data['Total_Amount'].sum()*100, precision=1),
                           md_label_data['Total_Amount'].count(), millify(md_label_data['Total_Amount'].mean(), precision=1)])
    columns = [field_type, 'Total Amount ($)', 'Market Share (%)', 'Number of Awards', 'Avg Award Amount ($)']

    # Pie Chart Data
    data = data.groupby(field)['Total_Amount'].sum().nlargest(10)

elif select_year_mode == "Compare Years":
    column1, column2 = st.columns(2)

    with column1:
        year1 = st.selectbox("Select Year1:", sorted(years_list))
    with column2:
        year2 = st.selectbox("Select Year2:", sorted(years_list))

    data_year1 = agency_data[agency_data["CompetitionFY"] == year1]
    data_year2 = agency_data[agency_data["CompetitionFY"] == year2]

    # Select Top 10 Disciplines by Revenue
    discipline_labels = sorted((data_year2.groupby(field)['Total_Amount'].sum().nlargest(10).reset_index())[field].unique())

    # Compute Table Data for each Discipline
    for label in discipline_labels:
        data_label_year1 = data_year1[data_year1[field] == label]
        data_label_year2 = data_year2[data_year2[field] == label]

        label_year1_total = data_label_year1['Total_Amount'].sum()
        label_year2_total = data_label_year2['Total_Amount'].sum()

        label_year1_marketshare = label_year1_total/data_year1['Total_Amount'].sum() * 100
        label_year2_marketshare = label_year2_total/data_year2['Total_Amount'].sum() * 100

        label_year1_num_grants = data_label_year1['Total_Amount'].count()
        label_year2_num_grants = data_label_year2['Total_Amount'].count()

        label_year1_avg_grant = data_label_year1['Total_Amount'].mean()
        label_year2_avg_grant = data_label_year2['Total_Amount'].mean()

        table_data.append([label, label_year2_total - label_year1_total, label_year2_marketshare - label_year1_marketshare,
                           label_year2_num_grants - label_year1_num_grants, label_year2_avg_grant - label_year1_avg_grant])
    columns = [field_type, 'Change in Amount ($)', 'Change in Market Share (%)', 'Change in Num of Grants', 'Change in Avg Grant Amount ($)']

# Export Charts / Tables
if select_year_mode == "Compare Years":
    st.write(f"{field_type} Market Share Table")
    
    df = pd.DataFrame(table_data, columns=columns)
    df["Change in Amount ($)"] = df["Change in Amount ($)"].apply(lambda x: f'<span style="color: red;">{millify(x, precision=1)}</span>' if x < 0 else f'<span style="color: green;">{millify(x, precision=1)}</span>')
    df["Change in Market Share (%)"] = df["Change in Market Share (%)"].apply(lambda x: f'<span style="color: red;">{millify(x, precision=1)}</span>' if x < 0 else f'<span style="color: green;">{millify(x, precision=1)}</span>')
    df["Change in Num of Grants"] = df["Change in Num of Grants"].apply(lambda x: f'<span style="color: red;">{millify(x, precision=1)}</span>' if x < 0 else f'<span style="color: green;">{millify(x, precision=1)}</span>')
    df["Change in Avg Grant Amount ($)"] = df["Change in Avg Grant Amount ($)"].apply(lambda x: f'<span style="color: red;">{millify(x, precision=1)}</span>' if x < 0 else f'<span style="color: green;">{millify(x, precision=1)}</span>')
    st.markdown(df.to_html(escape=False), unsafe_allow_html=True)

    # Export Table as CSV
    st.download_button(
        label="Export Table as CSV",
        data=pd.DataFrame(table_data, columns=columns).to_csv(index=False),
        file_name=f"{dashboard_type}_{field_type}_marketshare_data.csv",
        mime="text/csv"
    )

else:
    st.write(f"{field_type} Market Share Pie Chart")

    # Display Pie Chart
    fig, ax = plt.subplots()
    colors_mpl = plt.cm.tab20.colors[:len(data.index)]
    ax.pie(data.values, colors=colors_mpl, labels=None, autopct='%1.1f%%', startangle=90)
    plt.legend(labels=data.index, loc="center left", bbox_to_anchor=(1.0, 0.8))
    st.pyplot(fig)

    # Export Pie Chart
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    st.download_button(
        label="Export Plot",
        data=buf,
        file_name=f"{dashboard_type}_{field_type}_marketshare.png",
        mime="image/png"
    )

    # Display Table
    display_table = st.checkbox("Display Table")
    if display_table:
        st.write(f"{field_type} Market Share Table")
        df = pd.DataFrame(table_data, columns=columns)
        st.markdown(df.to_html(escape=False), unsafe_allow_html=True)

        # Export Table as CSV
        st.download_button(
            label="Export Table as CSV",
            data=df.to_csv(index=False),
            file_name=f"{dashboard_type}_{field_type}_marketshare_data.csv",
            mime="text/csv"
        )

# Select University
selected_university = st.selectbox("Select University:", ["Simon Fraser University"] + U15)
university_data = agency_data[agency_data['Institution'] == selected_university]

# Main Discipline
discipline_revenue = university_data.groupby(field)['Total_Amount'].sum()
discipline_labels = st.multiselect('Select disciplines', discipline_revenue.reset_index()[field].unique(), default=discipline_revenue.nlargest(10).reset_index()[field])

fig = plt.figure(figsize=(12, 6))
# Plot Each Discipline data for given University
for label in discipline_labels:
    grouped_label = university_data[university_data[field] == label].groupby('CompetitionFY')['Total_Amount'].sum().reset_index()
    plt.plot(grouped_label['CompetitionFY'], grouped_label['Total_Amount'], label=label, marker='o')
plt.title(f"Disciplinary Funding for {selected_university}")
plt.ylabel("Total Funding Amount")
plt.xlabel("CompetitionFY")
plt.xticks(university_data["CompetitionFY"].unique())
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
    file_name=f"{dashboard_type}_university_{field_type}_marketshare.png",
    mime="image/png"
)