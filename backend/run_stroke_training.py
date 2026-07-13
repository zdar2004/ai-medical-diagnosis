from pathlib import Path

from app.risk_assessment.training.train_model import TrainingPipeline

trainer = TrainingPipeline(
    disease_name="stroke",
    model_name="logistic",
    target_column="stroke",
    processed_data_dir=Path(
        "risk_assessment/datasets/processed/stroke"
    ),
    save_directory=Path(
        "risk_assessment/saved_models/stroke"
    ),
)

result = trainer.run()

print("=" * 60)
print("Stroke model trained successfully.")
print("=" * 60)
print(result)