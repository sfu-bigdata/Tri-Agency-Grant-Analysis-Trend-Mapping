from pathlib import Path
import pandas as pd
import numpy as np
import chardet
import sys
import re

from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity

# NLP and ML Libraries
from transformers import AutoTokenizer, AutoModel
from keybert import KeyBERT

import joblib

import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

import torch.nn as nn

START_YEAR = int(sys.argv[1])
END_YEAR = int(sys.argv[2])

# --- Load sentence-transformer model ---
model_name = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name).to(device)

# KeyBERT for keyword extraction
kw_model = KeyBERT()

# --- Custom classifier for predicting categories ---
class Classifier(nn.Module):
    def __init__(self, input_dim, output_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, output_dim)
        )

    def forward(self, x):
        return self.net(x)

# --- Function to embed batches of text using the sentence-transformer model ---
@torch.no_grad()
def embed(texts, batch_size=32):
    embeddings = []
    model.eval()
    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            encoded = tokenizer(batch, padding=True, truncation=True, return_tensors='pt').to(device)
            output = model(**encoded)
            cls_embeddings = output.last_hidden_state[:, 0, :]  # [CLS] token
            embeddings.append(cls_embeddings.cpu())
    return torch.cat(embeddings)


## CIHR DATA

# Load all CIHR Excel files into one DataFrame
cihr_path = "raw_data/CIHR/"
cihr_files = Path(cihr_path).glob("*.xlsx")

CIHR_DFS = [pd.read_excel(f) for f in cihr_files]
CIHR_DATA = pd.concat(CIHR_DFS, ignore_index=True)

# Select relevant columns and rename them for consistency
grant_descriptors = [
    "FundingCode_CodeFinancement", "FiscalYear_AnneeFinanciere", #"FundingStartDate_DatePremierVersement", "FundingEndDate_DateDernierVersement", 
    "ResearchInstitutionNameEN_NomEtablissementRechercheAN", "ResearchInstitutionNameFR_NomEtablissementRechercheFR",
    "AmountPaidFY_MontantPayeAF", "ProgramNameEN_NomProgrammeAN", "ProgramTypeEN_TypeProgrammeAN", 
    "ApplicationTitle_TitreDemande", "PrimaryThemeEN_ThemePrincipalAN", "AllResearchCategoriesEN_TousCategoriesRechercheAN",
    "ApplicationKeywords_MotsClesDemande", "ApplicationAbstract_ResumeDemande"
]

col_names = [
    'Unique_ID', 'FiscalYear', 'Institution', 'Institution_FR',
    'AmountPaid', 'Program_Name', 'Program_Type', 'Title', 'Main_Discipline', 'Area_of_Research',
    'Keywords', 'Summary'
]

CIHR_DATA = CIHR_DATA[grant_descriptors]
CIHR_DATA.columns = col_names

CIHR_DATA.dropna(subset=["AmountPaid"], inplace=True)

CIHR_DATA['FiscalYear'] = CIHR_DATA['FiscalYear']//100 # convert to year (ex. 201920 -> 2019)
CIHR_DATA['FiscalYear'] = CIHR_DATA['FiscalYear'].astype(int)
CIHR_DATA = CIHR_DATA[(CIHR_DATA["FiscalYear"] >= START_YEAR) & (CIHR_DATA["FiscalYear"] <= END_YEAR)]

CIHR_DATA['Institution'] = CIHR_DATA['Institution'].fillna(CIHR_DATA['Institution_FR'])
CIHR_DATA.drop(columns=["Institution_FR"], inplace=True)

# Clean up institution names (remove text in parentheses, strip spaces)
CIHR_DATA["Institution"] = CIHR_DATA["Institution"].astype(str).apply(lambda x: re.sub(r'\([^)]*\)', '', x))
CIHR_DATA["Institution"] = CIHR_DATA["Institution"].astype(str).str.strip()

# Normalize some known institution name variations
CIHR_DATA["Institution"] = CIHR_DATA["Institution"].replace(
    {
        "Universite Laval" : "Université Laval",
        "Universite de Montreal" : "Université de Montréal",
        "Western University" : "University of Western Ontario"
    }
)

# Standardize certain program names
CIHR_DATA["Program_Name"] = CIHR_DATA["Program_Name"].astype(str).apply(
    lambda x: "Operating Grant" if any(i in x for i in ["Operating Grant", "Operating Gr", "Op Grant", "Op. Grant", "Op Gr", "Op. Gr"]) else x)
CIHR_DATA["Program_Name"] = CIHR_DATA["Program_Name"].astype(str).apply(
    lambda x: "Project Grant" if any(i in x for i in ["Project Grant"]) else x)

# Normalize keywords to lowercase for frequency consistency
CIHR_DATA['Keywords'] = CIHR_DATA['Keywords'].str.lower()

# --- Predict missing Main_Discipline using a trained classifier ---
label_mapping = joblib.load("models/CIHR_MD_label_mapping.pkl")

clf_model = Classifier(384, len(label_mapping)).to(device)
clf_model.load_state_dict(torch.load("models/CIHR_MD.pt"))

CIHR_DATA['Main_Discipline'] = CIHR_DATA['Main_Discipline'].replace(['Not applicable/Specified', 'Not Applicable', ''], None)
missing_df = CIHR_DATA[CIHR_DATA['Main_Discipline'].isna()].copy()

X_missing = embed(missing_df['Title'].tolist())
with torch.no_grad():
    preds = clf_model(X_missing.to(device)).argmax(dim=1).cpu().numpy()
    pred_labels = [label_mapping[i] for i in preds]

CIHR_DATA.loc[missing_df.index, "Main_Discipline"] = pred_labels

# --- Fill missing Area_of_Research based on similarity to most frequent labels ---
CIHR_DATA['Area_of_Research'] = CIHR_DATA['Area_of_Research'].replace(['Not applicable/Specified', ''], None)
area_labels = CIHR_DATA['Area_of_Research'].dropna().apply(lambda x: [label.strip() for label in x.split(';') if label.strip()])

all_labels = [label for sublist in area_labels for label in sublist]

label_counts = Counter(all_labels)
most_freq_labels = [label for label, _ in label_counts.most_common(50)]

class_embeddings = embed(most_freq_labels)
clean_titles = CIHR_DATA['Title'].fillna('').astype(str).tolist()
input_embeddings = embed(clean_titles)

similarities = cosine_similarity(input_embeddings, class_embeddings)
CIHR_DATA['Area_of_Research'] = [most_freq_labels[i] for i in similarities.argmax(axis=1)]
CIHR_DATA['Area_of_Research'] = CIHR_DATA['Area_of_Research'].str.capitalize()


## NSERC DATA

# Load all NSERC CSV files into one DataFrame
nserc_path = "raw_data/NSERC/"
nserc_files = Path(nserc_path).glob("*.csv")

NSERC_DFS = []
for f in nserc_files:
    # Detect encoding using a sample of the file
    with open(f, 'rb') as file:
        raw_data = file.read(10000)  # Read first 10KB for detection
        result = chardet.detect(raw_data)
        enc = result['encoding']

    print(f"Reading {f} with encoding {enc}")
    df = pd.read_csv(f, encoding=enc)
    NSERC_DFS.append(df)
NSERC_DATA = pd.concat(NSERC_DFS, ignore_index=True)

# Select and rename relevant columns for consistency
grant_descriptors = [
    "ApplicationID", "FiscalYear-Exercice financier",
    "Institution-Établissement",
    "AwardAmount", "ProgramNameEN", "GroupEN",
    "ApplicationTitle", "AreaOfApplicationGroupEN", "ResearchSubjectGroupEN",
    "Keyword", "ApplicationSummary"
]

col_names = [
    'Unique_ID', 'FiscalYear', 'Institution', 
    'AmountPaid', 'Program_Name', 'Program_Type', 'Title', 'Main_Discipline', 'Area_of_Research',
    'Keywords', 'Summary'
]

NSERC_DATA = NSERC_DATA[grant_descriptors]
NSERC_DATA.columns = col_names

NSERC_DATA.dropna(subset=["AmountPaid"], inplace=True)

NSERC_DATA['FiscalYear'] = NSERC_DATA['FiscalYear'].astype(int)
NSERC_DATA = NSERC_DATA[(NSERC_DATA["FiscalYear"] >= START_YEAR) & (NSERC_DATA["FiscalYear"] <= END_YEAR)]

# Clean institution names (remove parentheses, drop "The " prefix, trim spaces)
NSERC_DATA["Institution"] = NSERC_DATA["Institution"].astype(str).apply(lambda x: re.sub(r'\([^)]*\)', '', x))
NSERC_DATA["Institution"] = NSERC_DATA["Institution"].astype(str).apply(lambda x: str.removeprefix(x, "The "))
NSERC_DATA["Institution"] = NSERC_DATA["Institution"].astype(str).str.strip()

# Standardize Program_Type values
NSERC_DATA['Program_Type'] = NSERC_DATA['Program_Type'].replace(['DISCOVERY RESEARCH**', 'DISCOVERY RESEARCH'], 'Discovery Research')
NSERC_DATA['Program_Type'] = NSERC_DATA['Program_Type'].replace(['RESEARCH PARTNERSHIPS**', 'RESEARCH PARTNERSHIPS'], 'Research Partnerships')
NSERC_DATA['Program_Type'] = NSERC_DATA['Program_Type'].replace(['RESEARCH TRAINING AND TALENT DEVELOPMENT'], 'Research Training and Talent Development')

# If summary is missing, use the title as the summary
mask = NSERC_DATA["Summary"] == "No summary - Aucun sommaire"
NSERC_DATA.loc[mask, "Summary"] = NSERC_DATA.loc[mask, "Title"]

# --- Extract keywords automatically using KeyBERT ---
def extract_keywords(text):
    keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 2), stop_words='english', top_n=5)
    keyword_list = [kw[0] for kw in keywords]  # Extract the keywords (ignore scores)
    return '; '.join(keyword_list)

NSERC_DATA['Keywords'] = NSERC_DATA['Summary'].astype(str).apply(extract_keywords)
NSERC_DATA['Keywords'] = NSERC_DATA['Keywords'].str.lower()

# --- Predict missing Main_Discipline using trained classifier ---
label_mapping = joblib.load("models/NSERC_MD_label_mapping.pkl")

clf_model = Classifier(384, len(label_mapping)).to(device)
clf_model.load_state_dict(torch.load("models/NSERC_MD.pt"))

NSERC_DATA['Main_Discipline'] = NSERC_DATA['Main_Discipline'].replace(['Not available', 'Advancement of knowledge'], None)
missing_df = NSERC_DATA[NSERC_DATA['Main_Discipline'].isna()].copy()
X_missing = embed(missing_df["Title"].tolist())
with torch.no_grad():
    preds = clf_model(X_missing.to(device)).argmax(dim=1).cpu().numpy()
    pred_labels = [label_mapping[i] for i in preds]

NSERC_DATA.loc[missing_df.index, "Main_Discipline"] = pred_labels

# --- Predict missing Area_of_Research using another trained classifier ---
label_mapping = joblib.load("models/NSERC_AR_label_mapping.pkl")

clf_model = Classifier(384, len(label_mapping)).to(device)
clf_model.load_state_dict(torch.load("models/NSERC_AR.pt"))

NSERC_DATA['Area_of_Research'] = NSERC_DATA['Area_of_Research'].replace(['Not available', 'The field of research available'], None)
missing_df = NSERC_DATA[NSERC_DATA['Area_of_Research'].isna()].copy()

X_missing = embed(missing_df["Title"].tolist())
with torch.no_grad():
    preds = clf_model(X_missing.to(device)).argmax(dim=1).cpu().numpy()
    pred_labels = [label_mapping[i] for i in preds]

NSERC_DATA.loc[missing_df.index, "Area_of_Research"] = pred_labels

## SSHRC DATA

sshrc_path = "raw_data/SSHRC/"
sshrc_files = Path(sshrc_path).glob("*.csv")

# Load all NSERC CSV files into one DataFrame
nserc_path = "raw_data/NSERC/"
nserc_files = Path(nserc_path).glob("*.csv")

SSHRC_DFS = []
for f in nserc_files:
    # Detect encoding using a sample of the file
    with open(f, 'rb') as file:
        raw_data = file.read(10000)  # Read first 10KB for detection
        result = chardet.detect(raw_data)
        enc = result['encoding']

    print(f"Reading {f} with encoding {enc}")
    df = pd.read_csv(f, encoding=enc)
    SSHRC_DFS.append(df)
SSHRC_DATA = pd.concat(SSHRC_DFS, ignore_index=True)

# Select and rename relevant columns for consistency
grant_descriptors = [
    "cle", "Fiscal_Year-Exercice_financier",
    "Institution",
    "Amount-Montant", "Program",
    "Title-Titre", "Area_of_Research", "Main_Discipline",
    "Keywords-Mots-clés", "Title-Titre"
]

col_names = [
    'Unique_ID', 'FiscalYear', 'Institution',
    'AmountPaid', 'Program_Name', 'Title', 'Main_Discipline', 'Area_of_Research',
    'Keywords', 'Summary'
]

SSHRC_DATA = SSHRC_DATA[grant_descriptors]
SSHRC_DATA.columns = col_names

SSHRC_DATA.dropna(subset=["AmountPaid"], inplace=True)

# Clean and convert amount to numeric
SSHRC_DATA["AmountPaid"] = SSHRC_DATA["AmountPaid"].astype(str).str.replace(",", "", regex=False).str.replace("$", "", regex=False).str.strip()
SSHRC_DATA["AmountPaid"] = pd.to_numeric(SSHRC_DATA["AmountPaid"])

SSHRC_DATA['FiscalYear'] = SSHRC_DATA['FiscalYear'].astype(int)
SSHRC_DATA = SSHRC_DATA[(SSHRC_DATA["FiscalYear"] >= START_YEAR) & (SSHRC_DATA["FiscalYear"] <= END_YEAR)]

# Clean institution names (remove parentheses, strip "The " prefix, trim spaces)
SSHRC_DATA["Institution"] = SSHRC_DATA["Institution"].astype(str).apply(lambda x: re.sub(r'\([^)]*\)', '', x))
SSHRC_DATA["Institution"] = SSHRC_DATA["Institution"].astype(str).apply(lambda x: str.removeprefix(x, "The "))
SSHRC_DATA["Institution"] = SSHRC_DATA["Institution"].astype(str).str.strip()

# Normalize keywords to lowercase
SSHRC_DATA['Keywords'] = SSHRC_DATA['Keywords'].str.lower()

# --- Predict missing Main_Discipline ---
label_mapping = joblib.load("models/SSHRC_MD_label_mapping.pkl")

clf_model = Classifier(384, len(label_mapping)).to(device)
clf_model.load_state_dict(torch.load("models/SSHRC_MD.pt"))

SSHRC_DATA['Main_Discipline'] = SSHRC_DATA['Main_Discipline'].replace(['Not Specified', 'Not specified', 'Not Subject to Research Classification', np.nan], None)
missing_df = SSHRC_DATA[SSHRC_DATA['Main_Discipline'].isna()].copy().dropna(subset=["Title"])

X_missing = embed(missing_df["Title"].tolist())
with torch.no_grad():
    preds = clf_model(X_missing.to(device)).argmax(dim=1).cpu().numpy()
    pred_labels = [label_mapping[i] for i in preds]

SSHRC_DATA.loc[missing_df.index, "Main_Discipline"] = pred_labels

# --- Predict missing Area_of_Research ---
label_mapping = joblib.load("models/SSHRC_AR_label_mapping.pkl")

clf_model = Classifier(384, len(label_mapping)).to(device)
clf_model.load_state_dict(torch.load("models/SSHRC_AR.pt"))

SSHRC_DATA['Area_of_Research'] = SSHRC_DATA['Area_of_Research'].replace(
    ["Not Specified", "Not specified", "Not Applicable", "Multiple primary fields of research", "Interdisciplinary Studies", np.nan], None)
missing_df = SSHRC_DATA[SSHRC_DATA['Area_of_Research'].isna()].copy().dropna(subset=["Title"])

X_missing = embed(missing_df["Title"].tolist())
with torch.no_grad():
    preds = clf_model(X_missing.to(device)).argmax(dim=1).cpu().numpy()
    pred_labels = [label_mapping[i] for i in preds]

SSHRC_DATA.loc[missing_df.index, "Area_of_Research"] = pred_labels

## Export clean datasets

# Save individual cleaned datasets
CIHR_DATA.to_csv("clean_data/CIHR_DATA.csv", index=False)
NSERC_DATA.to_csv("clean_data/NSERC_DATA.csv", index=False)
SSHRC_DATA.to_csv("clean_data/SSHRC_DATA.csv", index=False)

# Add agency column for identification
CIHR_DATA['Agency'] = "CIHR"
NSERC_DATA['Agency'] = "NSERC"
SSHRC_DATA['Agency'] = "SSHRC"

TRIAGENCY_DATA = pd.concat([CIHR_DATA, NSERC_DATA, SSHRC_DATA], ignore_index=True)

# Move 'Agency' column to front
cols = list(TRIAGENCY_DATA.columns)
TRIAGENCY_DATA = TRIAGENCY_DATA[cols[-1:] + cols[:-1]]

# Save combined dataset
TRIAGENCY_DATA.to_csv("clean_data/TRIAGENCY_DATA.csv", index=False)