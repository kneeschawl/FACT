import pandas as pd
import csv

# 1. Load your current dataset
# If you have the .xls file, convert it to CSV first or read it directly
df = pd.read_csv('/training_set/dark_pattern.csv') 

# 2. Clean the data (Remove any accidental existing quotes first)
df['text'] = df['text'].astype(str).str.replace('"', '', regex=False).str.strip()
df['category'] = df['category'].astype(str).str.replace('"', '', regex=False).str.strip()

# 3. Manually write the file to ensure only the 'text' is quoted
filename = "/training_set/cleaning_dataset/cleaned_dark_pattern_dataset.csv"

with open(filename, mode='w', encoding='utf-8', newline='') as f:
    # Write the header
    f.write('text,category\n')
    
    # Write the rows in the format: "text",category
    for _, row in df.iterrows():
        # Using f-string to wrap only the first column in double quotes
        f.write(f'"{row["text"]}",{row["category"]}\n')

print(f"Done! File saved as {filename}")