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

# Total Agency Funding Dashboard
st.title("Keyword Frequency Dashboard")

# Load data
TRIAGENCY_DATA = pd.read_csv("clean_data/TRIAGENCY_DATA.csv", low_memory=False)
dashboard_type = st.selectbox("Select Agency:", ["All", "CIHR", "NSERC", "SSHRC"])

if dashboard_type == "All":
    data = TRIAGENCY_DATA.copy()
elif dashboard_type == "CIHR":
    data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "CIHR"].copy()
elif dashboard_type == "NSERC":
    data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "NSERC"].copy()
elif dashboard_type == "SSHRC":
    data = TRIAGENCY_DATA[TRIAGENCY_DATA["Agency"] == "SSHRC"].copy()


# Step 1: Split all keywords in the column
all_keywords = data['Keywords'].str.split(';')

# Step 2: Flatten the list and strip whitespace
flattened_keywords = [
    kw.strip()
    for sublist in all_keywords
    if isinstance(sublist, list)  # Skip NaN or non-list entries
    for kw in sublist
    if isinstance(kw, str)        # In case of weird non-string entries
]

# Step 3: Count frequency
keyword_counts = Counter(flattened_keywords)

# Step 4: Convert to a DataFrame for easy viewing
keyword_freq_df = pd.DataFrame(keyword_counts.items(), columns=['Keyword', 'Frequency'])
keyword_freq_df = keyword_freq_df.sort_values(by='Frequency', ascending=False)

# Display top 10 most frequent keywords
top_10_freq = keyword_freq_df.nlargest(10, 'Frequency')
st.write(top_10_freq)

# TEMPORARY CODE

# **Bar Chart: Top 20 Keywords**
st.subheader("Top 20 Keywords")
bar_chart_data = keyword_freq_df.nlargest(20, 'Frequency')[['Keyword', 'Frequency']]
plt.figure(figsize=(10,6))
plt.bar(bar_chart_data['Keyword'], bar_chart_data['Frequency'])
plt.xlabel('Keyword')
plt.ylabel('Frequency')
plt.title('Top 20 Keywords by Frequency')
st.pyplot(plt.gcf())

# **Heatmap: Keyword Correlation Matrix**
# st.subheader("Keyword Correlation Matrix")
# keyword_corr_df = data.groupby('Keywords')['Agency'].nunique().reset_index()
# keyword_corr_df['Correlation'] = keyword_corr_df.apply(lambda row: abs(row[1] - 1), axis=1)
# plt.figure(figsize=(10,8))
# sns.heatmap(keyword_corr_df.pivot_table(index='Keywords', columns='Agency', values='Correlation'), cmap='coolwarm')
# st.pyplot(plt.gcf())

# **Word Cloud: Most Frequent Keywords**
# st.subheader("Most Frequent Keywords")
# wordcloud_data = keyword_freq_df.nlargest(50, 'Frequency')[['Keyword', 'Frequency']]
# from wordcloud import WordCloud
# wc = WordCloud(max_words=100).generate_from_frequencies(wordcloud_data.set_index('Keyword')['Frequency'])
# plt.figure(figsize=(10,6))
# plt.imshow(wc, interpolation='bilinear')
# plt.axis('off')
# st.pyplot(plt.gcf())

# # **Interactive Filter: Select Keyword to Display**
# st.subheader("Select Keyword to Display")
# selected_keyword = st.selectbox("Select a keyword:", keyword_freq_df['Keyword'].unique())
# keyword_filtered_data = data[data['Keywords'].str.contains(selected_keyword, case=False)]
# st.write(keyword_filtered_data)