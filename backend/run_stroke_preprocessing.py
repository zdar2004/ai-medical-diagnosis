from pathlib import Path

from app.risk_assessment.preprocessing.preprocessing_pipeline import (
    PreprocessingPipeline,
)

pipeline = PreprocessingPipeline(
    disease_name="stroke",
    dataset_path=Path(
        "app/risk_assessment/datasets/raw/stroke/healthcare-dataset-stroke-data.csv"
    ),
    target_column="stroke",
    categorical_columns=[
        "gender",
        "ever_married",
        "work_type",
        "Residence_type",
        "smoking_status",
    ],
    numerical_columns=[
        "age",
        "avg_glucose_level",
        "bmi",
    ],
    test_size=0.2,
    random_state=42,
)

result = pipeline.run()

print("=" * 60)
print("Stroke preprocessing completed successfully.")
print("=" * 60)
print(f"Disease: {result['disease_name']}")
print(f"Dataset: {result['source_file']}")
print(f"Raw Shape: {result['raw_shape']}")
print(f"Processed Directory: {result['processed_dir']}")
print(f"Pipeline Path: {result['pipeline_path']}")