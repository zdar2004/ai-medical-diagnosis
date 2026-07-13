from pathlib import Path

import pandas as pd

from app.risk_assessment.preprocessing.preprocessing_pipeline import (
    PreprocessingPipeline,
)

# Load dataset
df = pd.read_csv(
    "app/risk_assessment/datasets/raw/hypertension/hypertension_dataset.csv"
)

# Encode target
df["Has_Hypertension"] = df["Has_Hypertension"].map(
    {
        "No": 0,
        "Yes": 1,
    }
)

# Save encoded dataset temporarily
encoded_dataset_path = (
    "app/risk_assessment/datasets/raw/hypertension/hypertension_dataset_encoded.csv"
)
df.to_csv(encoded_dataset_path, index=False)

pipeline = PreprocessingPipeline(
    disease_name="hypertension",
    dataset_path=Path(encoded_dataset_path),
    target_column="Has_Hypertension",
    categorical_columns=[
        "BP_History",
        "Medication",
        "Family_History",
        "Exercise_Level",
        "Smoking_Status",
    ],
    numerical_columns=[
        "Age",
        "Salt_Intake",
        "Stress_Score",
        "Sleep_Duration",
        "BMI",
    ],
    test_size=0.2,
    random_state=42,
)

result = pipeline.run()

print("=" * 60)
print("Hypertension preprocessing completed successfully.")
print("=" * 60)
print(f"Disease: {result['disease_name']}")
print(f"Dataset: {result['source_file']}")
print(f"Raw Shape: {result['raw_shape']}")
print(f"Processed Directory: {result['processed_dir']}")
print(f"Pipeline Path: {result['pipeline_path']}")