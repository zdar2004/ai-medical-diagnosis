from app.risk_assessment.training.train_model import TrainingPipeline

trainer = TrainingPipeline(
    disease_name="diabetes",
    model_name="logistic",
    target_column="diabetes",
    processed_data_dir="risk_assessment/datasets/processed/diabetes",
    save_directory="risk_assessment/saved_models/diabetes",
)

summary = trainer.run(save_model=True)

print("=" * 60)
print("TRAINING COMPLETED")
print("=" * 60)
print(summary["model_type"])
print(summary["saved_model_path"])