from pathlib import Path
import pandas as pd
import re

from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity

from transformers import AutoTokenizer, AutoModel
import joblib

import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

import torch.nn as nn

START_YEAR = 2019

model_name = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name).to(device)

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

cihr_path = "raw_data/CIHR/"
cihr_files = Path(cihr_path).glob("*.csv")

CIHR_DFS = [pd.read_csv(f) for f in cihr_files]
CIHR_DATA = pd.concat(CIHR_DFS, ignore_index=True)

grant_descriptors = [
    "FundingCode_CodeFinancement", "CompetitionFY_AFConcours", #"FundingStartDate_DatePremierVersement", "FundingEndDate_DateDernierVersement", 
    "ResearchInstitutionNameEN_NomEtablissementRechercheAN", "ResearchInstitutionNameFR_NomEtablissementRechercheFR",
    "TotalAmountAwarded_MontantTotalAccorde","ProgramNameEN_NomProgrammeAN", "ProgramTypeEN_TypeProgrammeAN", 
    "ApplicationTitle_TitreDemande", "PrimaryThemeEN_ThemePrincipalAN", "AllResearchCategoriesEN_TousCategoriesRechercheAN"
]

col_names = [
    'Unique_ID', 'CompetitionFY', 'Institution', 'Institution_FR',
    'Total_Amount', 'Program_Name', 'Program_Type', 'Title', 'Main_Discipline', 'Area_of_Research'
]

CIHR_DATA = CIHR_DATA[grant_descriptors]
CIHR_DATA.columns = col_names

CIHR_DATA.drop_duplicates(inplace=True)
CIHR_DATA.dropna(subset=["Total_Amount"], inplace=True)

CIHR_DATA['CompetitionFY'] = CIHR_DATA['CompetitionFY']//100 # convert to year (ex. 201920 -> 2019)
CIHR_DATA = CIHR_DATA[CIHR_DATA["CompetitionFY"] >= START_YEAR]
CIHR_DATA['CompetitionFY'] = CIHR_DATA['CompetitionFY'].astype(int)

CIHR_DATA['Institution'] = CIHR_DATA['Institution'].fillna(CIHR_DATA['Institution_FR'])
CIHR_DATA.drop(columns=["Institution_FR"], inplace=True)

CIHR_DATA["Institution"] = CIHR_DATA["Institution"].astype(str).apply(lambda x: re.sub(r'\([^)]*\)', '', x))
CIHR_DATA["Institution"] = CIHR_DATA["Institution"].astype(str).str.strip()

label_mapping = joblib.load("models/CIHR_MD_label_mapping.pkl")

input_dim = 384  # MiniLM embedding size
output_dim = len(label_mapping)

clf_model = Classifier(input_dim, output_dim).to(device)
clf_model.load_state_dict(torch.load("models/CIHR_MD.pt"))

# missing_df = CIHR_DATA[CIHR_DATA["Main_Discipline"].isna() | CIHR_DATA["Main_Discipline"] == "Not applicable/Specified"].copy()
CIHR_DATA['Main_Discipline'] = CIHR_DATA['Main_Discipline'].replace(['Not applicable/Specified', 'Not Applicable', ''], None)
missing_df = CIHR_DATA[CIHR_DATA['Main_Discipline'].isna()].copy()

X_missing = embed(missing_df['Title'].tolist())
with torch.no_grad():
    preds = clf_model(X_missing.to(device)).argmax(dim=1).cpu().numpy()
    pred_labels = [label_mapping[i] for i in preds]

CIHR_DATA.loc[missing_df.index, "Main_Discipline"] = pred_labels

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

nserc_path = "raw_data/NSERC/"
nserc_files = Path(nserc_path).glob("*.csv")

NSERC_DFS = [pd.read_csv(f) for f in nserc_files]
NSERC_DATA = pd.concat(NSERC_DFS, ignore_index=True)

grant_descriptors = [
    "ApplicationID", "CompetitionYear-Année de concours",
    "Institution-Établissement",
    "AwardAmount", "ProgramNameEN", "GroupEN",
    "ApplicationTitle", "AreaOfApplicationGroupEN", "ResearchSubjectGroupEN"
]

col_names = [
    'Unique_ID', 'CompetitionFY', 'Institution', 
    'Total_Amount', 'Program_Name', 'Program_Type', 'Title', 'Main_Discipline', 'Area_of_Research'
]

NSERC_DATA = NSERC_DATA[grant_descriptors]
NSERC_DATA.columns = col_names

NSERC_DATA.drop_duplicates(inplace=True)
NSERC_DATA.dropna(subset=["Total_Amount"], inplace=True)

NSERC_DATA = NSERC_DATA[NSERC_DATA["CompetitionFY"] >= START_YEAR]
NSERC_DATA['CompetitionFY'] = NSERC_DATA['CompetitionFY'].astype(int)

NSERC_DATA["Institution"] = NSERC_DATA["Institution"].astype(str).apply(lambda x: re.sub(r'\([^)]*\)', '', x))
NSERC_DATA["Institution"] = NSERC_DATA["Institution"].astype(str).str.strip()

label_mapping = joblib.load("models/NSERC_MD_label_mapping.pkl")

input_dim = 384  # MiniLM embedding size
output_dim = len(label_mapping)

clf_model = Classifier(input_dim, output_dim).to(device)
clf_model.load_state_dict(torch.load("models/NSERC_MD.pt"))

NSERC_DATA['Program_Type'] = NSERC_DATA['Program_Type'].replace(['DISCOVERY RESEARCH**', 'DISCOVERY RESEARCH'], 'Discovery Research')
NSERC_DATA['Program_Type'] = NSERC_DATA['Program_Type'].replace(['RESEARCH PARTNERSHIPS**', 'RESEARCH PARTNERSHIPS'], 'Research Partnerships')
NSERC_DATA['Program_Type'] = NSERC_DATA['Program_Type'].replace(['RESEARCH TRAINING AND TALENT DEVELOPMENT'], 'Research Training and Talent Development')

NSERC_DATA['Main_Discipline'] = NSERC_DATA['Main_Discipline'].replace(['Not available', 'Advancement of knowledge'], None)
missing_df = NSERC_DATA[NSERC_DATA['Main_Discipline'].isna()].copy()

X_missing = embed(missing_df["Title"].tolist())
with torch.no_grad():
    preds = clf_model(X_missing.to(device)).argmax(dim=1).cpu().numpy()
    pred_labels = [label_mapping[i] for i in preds]

NSERC_DATA.loc[missing_df.index, "Main_Discipline"] = pred_labels

label_mapping = joblib.load("models/NSERC_AR_label_mapping.pkl")

input_dim = 384  # MiniLM embedding size
output_dim = len(label_mapping)

clf_model = Classifier(input_dim, output_dim).to(device)
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

SSHRC_DFS = [pd.read_csv(f) for f in sshrc_files]
SSHRC_DATA = pd.concat(SSHRC_DFS, ignore_index=True)

grant_descriptors = [
    "cle", "Competition_Year-Année_du_concours",
    "Institution",
    "Amount-Montant", "Program",
    "Title-Titre", "Area_of_Research", "Main_Discipline"
]

col_names = [
    'Unique_ID', 'CompetitionFY', 'Institution',
    'Total_Amount', 'Program_Name', 'Title', 'Main_Discipline', 'Area_of_Research'
]


SSHRC_DATA = SSHRC_DATA[grant_descriptors]
SSHRC_DATA.columns = col_names

SSHRC_DATA.drop_duplicates(inplace=True)
SSHRC_DATA.dropna(subset=["Total_Amount"], inplace=True)

SSHRC_DATA = SSHRC_DATA[SSHRC_DATA["CompetitionFY"] >= START_YEAR]
SSHRC_DATA['CompetitionFY'] = SSHRC_DATA['CompetitionFY'].astype(int)

SSHRC_DATA["Institution"] = SSHRC_DATA["Institution"].astype(str).apply(lambda x: re.sub(r'\([^)]*\)', '', x))
SSHRC_DATA["Institution"] = SSHRC_DATA["Institution"].astype(str).str.strip()

label_mapping = joblib.load("models/SSHRC_MD_label_mapping.pkl")

input_dim = 384  # MiniLM embedding size
output_dim = len(label_mapping)

clf_model = Classifier(input_dim, output_dim).to(device)
clf_model.load_state_dict(torch.load("models/SSHRC_MD.pt"))

label_mapping = joblib.load("models/SSHRC_MD_label_mapping.pkl")

input_dim = 384  # MiniLM embedding size
output_dim = len(label_mapping)

clf_model = Classifier(input_dim, output_dim).to(device)
clf_model.load_state_dict(torch.load("models/SSHRC_MD.pt"))

label_mapping = joblib.load("models/SSHRC_AR_label_mapping.pkl")

input_dim = 384  # MiniLM embedding size
output_dim = len(label_mapping)

clf_model = Classifier(input_dim, output_dim).to(device)
clf_model.load_state_dict(torch.load("models/SSHRC_AR.pt"))

SSHRC_DATA['Area_of_Research'] = SSHRC_DATA['Area_of_Research'].replace(["Not Specified", "Not specified", "Not Applicable", "Multiple primary fields of research", "Interdisciplinary Studies"], None)
missing_df = SSHRC_DATA[SSHRC_DATA['Area_of_Research'].isna()].copy()

X_missing = embed(missing_df["Title"].tolist())
with torch.no_grad():
    preds = clf_model(X_missing.to(device)).argmax(dim=1).cpu().numpy()
    pred_labels = [label_mapping[i] for i in preds]

SSHRC_DATA.loc[missing_df.index, "Area_of_Research"] = pred_labels

## Export to clean

CIHR_DATA.to_csv("clean_data/CIHR_DATA.csv", index=False)
NSERC_DATA.to_csv("clean_data/NSERC_DATA.csv", index=False)
SSHRC_DATA.to_csv("clean_data/SSHRC_DATA.csv", index=False)

CIHR_DATA['Agency'] = "CIHR"
NSERC_DATA['Agency'] = "NSERC"
SSHRC_DATA['Agency'] = "SSHRC"

TRIAGENCY_DATA = pd.concat([CIHR_DATA, NSERC_DATA, SSHRC_DATA], ignore_index=True)

cols = list(TRIAGENCY_DATA.columns)
TRIAGENCY_DATA = TRIAGENCY_DATA[cols[-1:] + cols[:-1]]

TRIAGENCY_DATA.to_csv("clean_data/TRIAGENCY_DATA.csv", index=False)