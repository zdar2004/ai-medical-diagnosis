from pathlib import Path

from app.risk_assessment.training.train_model import TrainingPipeline

trainer = TrainingPipeline(
    disease_name="hypertension",
    model_name="logistic",
    target_column="Has_Hypertension",
    processed_data_dir=Path(
        "risk_assessment/datasets/processed/hypertension"
    ),
    save_directory=Path(
        "risk_assessment/saved_models/hypertension"
    ),
)

result = trainer.run()

print("=" * 60)
print("Hypertension model trained successfully.")
print("=" * 60)
print(result)