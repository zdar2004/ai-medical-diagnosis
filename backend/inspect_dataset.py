import pandas as pd

df = pd.read_csv(
    "app/risk_assessment/datasets/raw/diabetes/diabetes_prediction_dataset.csv"
)

print("=" * 50)
print("Shape:")
print(df.shape)

print("=" * 50)
print("Columns:")
print(df.columns.tolist())

print("=" * 50)
print("Info:")
df.info()

print("=" * 50)
print("Missing Values:")
print(df.isnull().sum())

print("=" * 50)
print("Target Distribution:")
print(df["diabetes"].value_counts())

print("=" * 50)
print(df.head())