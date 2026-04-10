import pandas as pd

# 1. Read the TSV file
# 'sep=\t' tells pandas to look for tabs as the separator
df = pd.read_csv('training_set/dataset.tsv', sep='\t')

# 2. Save it as a CSV
# 'index=False' prevents pandas from adding an extra column for row numbers
df.to_csv('dark_patterns_dataset.csv', index=False)

print("Conversion complete: 'dark_patterns_dataset.csv' is ready.")