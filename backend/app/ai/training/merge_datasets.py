from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

OLD_DATASET = DATA_DIR / "disease_dataset.csv"
NEW_DATASET = DATA_DIR / "final_symptoms_to_disease.csv"

OUTPUT = DATA_DIR / "merged_dataset.csv"


def clean_symptoms(text: str) -> str:
    if pd.isna(text):
        return ""

    symptoms = []

    for s in str(text).split(","):
        s = s.strip().lower()
        s = s.replace("_", " ")

        if s and s not in symptoms:
            symptoms.append(s)

    return ", ".join(symptoms)


def clean_disease(text: str) -> str:
    return str(text).strip().lower()


def main():

    old_df = pd.read_csv(OLD_DATASET)
    new_df = pd.read_csv(NEW_DATASET)

    old_df.columns = ["disease", "symptoms"]
    new_df.columns = ["disease", "symptoms"]

    df = pd.concat([old_df, new_df], ignore_index=True)

    df["disease"] = df["disease"].apply(clean_disease)
    df["symptoms"] = df["symptoms"].apply(clean_symptoms)

    df = df.drop_duplicates()

    df = df[df["symptoms"] != ""]

    df.to_csv(OUTPUT, index=False)

    print("=" * 60)
    print("Merged dataset created successfully!")
    print("=" * 60)
    print(f"Total samples : {len(df)}")
    print(f"Disease classes : {df['disease'].nunique()}")
    print(f"Saved to : {OUTPUT}")


if __name__ == "__main__":
    main()