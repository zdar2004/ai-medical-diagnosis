import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

INPUT = DATA_DIR / "merged_dataset.csv"
OUTPUT = DATA_DIR / "clean_dataset.csv"

df = pd.read_csv(INPUT)

print("Original samples:", len(df))
print("Original diseases:", df["disease"].nunique())

# Keep diseases having at least 10 samples
counts = df["disease"].value_counts()

valid = counts[counts >= 10].index

df = df[df["disease"].isin(valid)]

print("Remaining samples:", len(df))
print("Remaining diseases:", df["disease"].nunique())

df.to_csv(OUTPUT, index=False)

print("\nSaved:", OUTPUT)