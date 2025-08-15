import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from millify import millify
import io

from collections import Counter

st.set_page_config(page_title="Keyword Frequency Dashboard", page_icon="")

# U15 + UVic
U15 = ["University of Alberta", "University of British Columbia", "University of Calgary", "Dalhousie University", "Université Laval", 
       "University of Manitoba", "McGill University", "McMaster University", "Université de Montréal", "University of Ottawa", 
       "Queen's University", "University of Saskatchewan", "University of Toronto", "University of Waterloo", "University of Western Ontario",
       "University of Victoria"]

# Keyword Frequency Dashboard
st.title("Keyword Frequency Dashboard")

# Load data
TRIAGENCY_DATA = pd.read_csv("clean_data/TRIAGENCY_DATA.csv", low_memory=False)
dashboard_type = st.selectbox("Select Agency:", ["All", "CIHR", "NSERC", "SSHRC"])

# Select Agency
if dashboard_type == "All":
    agency_data = TRIAGENCY_DATA.copy()
elif dashboard_type == "CIHR":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "CIHR"].copy()
    specifc_labels = ["Project Grant", "Operating Grant"]
elif dashboard_type == "NSERC":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "NSERC"].copy()
    specifc_labels = ["Discovery Grants Program - Individual", "Alliance Grants"]
elif dashboard_type == "SSHRC":
    agency_data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "SSHRC"].copy()
    specifc_labels = ["Insight Development Grant", "Insight Grants", "Partnership Grants"]

if dashboard_type != "All":
    program_type = st.selectbox("Select Program Type:", ["All"] + specifc_labels)
    if program_type != "All":
        agency_data = agency_data[agency_data["Program_Name"] == program_type]

# Compute Keyword Frequency
all_keywords = agency_data['Keywords'].dropna().str.split(';').explode()
keyword_counts = Counter(all_keywords)
keyword_freq_df = pd.DataFrame(keyword_counts.items(), columns=['Keyword', 'Frequency'])
keyword_freq_df = keyword_freq_df.sort_values(by='Frequency', ascending=False)

# Bar Chart: Top 20 Keywords**
st.subheader("Top 20 Keywords")
bar_chart_data = keyword_freq_df.nlargest(20, 'Frequency')[['Keyword', 'Frequency']]
plt.figure(figsize=(10,6))
plt.bar(bar_chart_data['Keyword'], bar_chart_data['Frequency'])
plt.xticks(bar_chart_data['Keyword'], rotation=45, ha='right')
plt.xlabel('Keyword')
plt.ylabel('Frequency')
plt.title('Top 20 Keywords by Frequency')
st.pyplot(plt.gcf())

# Save bar chart as image
buf = io.BytesIO()
plt.savefig(buf, format="png", bbox_inches="tight")
buf.seek(0)
st.download_button(
    label="Export Plot",
    data=buf,
    file_name=f"{dashboard_type}_keyword_freq.png",
    mime="image/png"
)
# Display & Export Table
if st.checkbox("Show Table"):
    st.markdown(bar_chart_data.style.hide(axis="index").to_html(), unsafe_allow_html=True)
    st.download_button(
        label="Export Table as CSV",
        data=keyword_freq_df.to_csv(index=False),
        file_name=f"{dashboard_type}_marketshare_data.csv",
        mime="text/csv"
    )

## Keyword Grant Data
st.title("Keyword Grant Data")

table_data = []
years_list = agency_data['FiscalYear'].unique()

# Split Keywords
data = agency_data.copy()
data['Keywords'] = data['Keywords'].str.split(';')
data = data.explode('Keywords')

# Select Year Mode
select_year_mode = st.selectbox("Select year range type:", ["Single Year", "Range of Years", "Compare Years"])
if select_year_mode == "Single Year":
    year = st.selectbox("Select Year:", sorted(years_list))

    # Select Top 10 Keywords by Frequency
    data = data[data["FiscalYear"] == year]
    keyword_labels = data['Keywords'].value_counts().nlargest(10).index

    # Compute Table Data for each Keyword
    for label in keyword_labels:
        label_data = data[data['Keywords'] == label]
        table_data.append([label, millify(label_data['AmountPaid'].sum(), precision=1), millify(label_data['AmountPaid'].sum()/data['AmountPaid'].sum()*100, precision=2),
                           millify(label_data['AmountPaid'].count(), precision=2), millify(label_data['AmountPaid'].mean(), precision=1)])
    columns = ['Keywords', 'Total Amount ($)', 'Market Share (%)', 'Number of Awards', 'Avg Award Amount ($)']

    df = pd.DataFrame(table_data, columns=columns)
    st.markdown(df.style.hide(axis="index").to_html(), unsafe_allow_html=True)

    # Export Table as CSV
    st.download_button(
        label="Export Table as CSV",
        data=df.to_csv(index=False),
        file_name=f"{dashboard_type}_keywords_marketshare_data.csv",
        mime="text/csv"
    )

elif select_year_mode == "Range of Years":
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.selectbox("Select Start Year:", sorted(years_list))
    with col2:
        end_year = st.selectbox("Select End Year:", sorted(years_list, reverse=True))

    data = data[(data['FiscalYear'] >= start_year) & (data['FiscalYear'] <= end_year)]
    # Select Top 10 Keywords by Frequency
    keyword_labels = data['Keywords'].value_counts().nlargest(10).index

    # Compute Table Data for each Keyword
    for label in keyword_labels:
        label_data = data[data['Keywords'] == label]
        table_data.append([label, millify(label_data['AmountPaid'].sum(), precision=1), millify(label_data['AmountPaid'].sum()/data['AmountPaid'].sum()*100, precision=2),
                           millify(len(label_data), precision=2), millify(label_data['AmountPaid'].mean(), precision=1)])
    columns = ['Keywords', 'Total Amount ($)', 'Market Share (%)', 'Number of Awards', 'Avg Award Amount ($)']

    df = pd.DataFrame(table_data, columns=columns)
    st.markdown(df.style.hide(axis="index").to_html(), unsafe_allow_html=True)

    # Export Table as CSV
    st.download_button(
        label="Export Table as CSV",
        data=df.to_csv(index=False),
        file_name=f"{dashboard_type}_keywords_marketshare_data.csv",
        mime="text/csv"
    )

elif select_year_mode == "Compare Years":
    col1, col2 = st.columns(2)
    with col1:
        year1 = st.selectbox("Select Year1:", sorted(years_list))
    with col2:
        year2 = st.selectbox("Select Year2:", sorted(years_list))

    year1_data = data[data['FiscalYear'] == year1]
    year2_data = data[data['FiscalYear'] == year2] 
    
    # Select Top 10 Keywords by Frequency
    keyword_labels = year2_data['Keywords'].value_counts().nlargest(10).index

    # Compute Table Data for each Keyword
    for label in keyword_labels:
        year1_label_data = year1_data[year1_data['Keywords'] == label]
        year2_label_data = year2_data[year2_data['Keywords'] == label]
        table_data.append([label, year2_label_data['AmountPaid'].sum() - year1_label_data['AmountPaid'].sum(),
                           year2_label_data['AmountPaid'].sum()/year1_data['AmountPaid'].sum()*100 - year1_label_data['AmountPaid'].sum()/year1_data['AmountPaid'].sum()*100,
                           year2_label_data['AmountPaid'].count() - year1_label_data['AmountPaid'].count(),
                           year2_label_data['AmountPaid'].mean() - year1_label_data['AmountPaid'].mean()])
    columns = ['Keywords', 'Change in Total Amount ($)', 'Change in Market Share (%)', 'Change in Num of Grants', 'Change in Avg Grant Amount ($)']

    # Create & Format Table
    market_share_table = pd.DataFrame(table_data, columns=columns)
    market_share_table["Change in Total Amount ($)"] = market_share_table["Change in Total Amount ($)"].apply(lambda x: f'<span style="color: red;">{millify(x, precision=2)}</span>' if x < 0 else f'<span style="color: green;">{millify(x, precision=2)}</span>')
    market_share_table["Change in Market Share (%)"] = market_share_table["Change in Market Share (%)"].apply(lambda x: f'<span style="color: red;">{x:.2f}%</span>' if x < 0 else f'<span style="color: green;">{x:.2f}%</span>')
    market_share_table["Change in Num of Grants"] = market_share_table["Change in Num of Grants"].apply(lambda x: f'<span style="color: red;">{x}</span>' if x < 0 else f'<span style="color: green;">{x}</span>')
    market_share_table["Change in Avg Grant Amount ($)"] = market_share_table["Change in Avg Grant Amount ($)"].apply(lambda x: f'<span style="color: red;">{millify(x, precision=2)}</span>' if x < 0 else f'<span style="color: green;">{millify(x, precision=2)}</span>')
    st.markdown(market_share_table.style.hide(axis="index").to_html(), unsafe_allow_html=True)

    # Export Table as CSV
    st.download_button(
        label="Export Table as CSV",
        data=market_share_table.to_csv(index=False),
        file_name=f"{dashboard_type}_keywords_marketshare_data.csv",
        mime="text/csv"
    )

# **Heatmap: Keyword Correlation Matrix**
# st.subheader("Keyword Correlation Matrix")
# keyword_corr_df = data.groupby('Keywords')['Agency'].nunique().reset_index()
# keyword_corr_df['Correlation'] = keyword_corr_df.apply(lambda row: abs(row[1] - 1), axis=1)
# plt.figure(figsize=(10,8))
# sns.heatmap(keyword_corr_df.pivot_table(index='Keywords', columns='Agency', values='Correlation'), cmap='coolwarm')
# st.pyplot(plt.gcf())

# # **Interactive Filter: Select Keyword to Display**
# st.subheader("Select Keyword to Display")
# selected_keyword = st.selectbox("Select a keyword:", keyword_freq_df['Keyword'].unique())
# keyword_filtered_data = agency_data[agency_data['Keywords'].str.contains(selected_keyword, case=False)]
# st.write(keyword_filtered_data)