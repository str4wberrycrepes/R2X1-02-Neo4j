import pandas as pd
from collections import Counter

# Load Excel file
file_path = "C:/Users/davep/Downloads/something.xlsx"
df = pd.read_excel(file_path)

# Ensure 'keywords' column exists (case-insensitive match)
keyword_col = next((col for col in df.columns if col.strip().lower() == "keywords"), None)
if not keyword_col:
    raise ValueError(f"'keywords' column not found in the spreadsheet. Columns available: {df.columns.tolist()}")

# Step 1: Extract keywords, split by comma, and clean
keywords = []
for cell in df[keyword_col].dropna():
    terms = str(cell).split(",")
    cleaned_terms = [term.strip().lower() for term in terms if term.strip()]
    keywords.extend(cleaned_terms)

# Step 2: Count frequencies
frequency = Counter(keywords)

# Step 3: Write to SymSpell format
output_file = './symspell_frequency_dictionary.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    for term, freq in frequency.items():
        if '\t' not in term:  # ensure no tab characters
            f.write(f"{term}|{freq}\n")

print(f"Dictionary written to {output_file}")
