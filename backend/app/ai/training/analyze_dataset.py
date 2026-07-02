from pathlib import Path
import pandas as pd

DATASET = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "merged_dataset.csv"
)

df = pd.read_csv(DATASET)

print("=" * 70)
print("DATASET ANALYSIS")
print("=" * 70)

print(f"Total Samples   : {len(df)}")
print(f"Disease Classes : {df['disease'].nunique()}")

print("\nTop 30 diseases:\n")

print(df["disease"].value_counts().head(30))

print("\n")

print("=" * 70)

print("Diseases having only ONE sample:\n")

rare = df["disease"].value_counts()

print((rare == 1).sum())

print("=" * 70)