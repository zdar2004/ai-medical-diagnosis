import logging
import sys
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

from xgboost import XGBClassifier

from app.ai.training.preprocessing import prepare_training_data


logger = logging.getLogger(__name__)


# ============================================================
# PATHS
# ============================================================

_THIS_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _THIS_DIR.parents[2]

MODELS_DIR = _BACKEND_DIR / "app" / "ai" / "models"

CLASSIFIER_PATH = MODELS_DIR / "disease_classifier.pkl"
VECTORIZER_PATH = MODELS_DIR / "tfidf_vectorizer.pkl"
ENCODER_PATH = MODELS_DIR / "label_encoder.pkl"

PERFORMANCE_PATH = MODELS_DIR / "model_performance.pkl"


# ============================================================
# SETTINGS
# ============================================================

TEST_SIZE = 0.2
RANDOM_STATE = 42


TFIDF_PARAMS = {
    "ngram_range": (1, 2),
    "min_df": 1,
    "sublinear_tf": True,
    "strip_accents": "unicode",
    "analyzer": "word",
}


# ============================================================
# RESULT CLASS
# ============================================================

@dataclass
class TrainingResult:
    vectorizer: TfidfVectorizer
    encoder: LabelEncoder
    classifier: object

    best_model_name: str
    model_results: list[dict]

    n_samples: int
    n_train: int
    n_test: int
    n_classes: int

    class_names: list[str]


# ============================================================
# METRICS FUNCTION
# ============================================================

def calculate_metrics(y_true, y_pred):
    accuracy = accuracy_score(y_true, y_pred)

    precision = precision_score(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0,
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
    }


# ============================================================
# TRAIN ALL MODELS
# ============================================================

def train():

    logger.info("Loading dataset...")
    X, y = prepare_training_data()

    n_samples = len(X)

    logger.info(
        "Dataset loaded: %d samples",
        n_samples,
    )


    # --------------------------------------------------------
    # LABEL ENCODING
    # --------------------------------------------------------

    logger.info("Encoding labels...")

    encoder = LabelEncoder()

    y_encoded = encoder.fit_transform(y)

    n_classes = len(encoder.classes_)


    # --------------------------------------------------------
    # TRAIN / TEST SPLIT
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_encoded,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y_encoded,
    )

    n_train = len(X_train)
    n_test = len(X_test)


    # --------------------------------------------------------
    # TF-IDF
    # --------------------------------------------------------

    logger.info("Creating TF-IDF features...")

    vectorizer = TfidfVectorizer(
        **TFIDF_PARAMS
    )

    X_train_tfidf = vectorizer.fit_transform(
        X_train
    )

    X_test_tfidf = vectorizer.transform(
        X_test
    )


    # ========================================================
    # DEFINE MODELS
    # ========================================================

    models = {


        "Logistic Regression":

        LogisticRegression(
            C=4.0,
            max_iter=1000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),


        "Random Forest":

        RandomForestClassifier(
            n_estimators=100,
            max_depth=30,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features="sqrt",
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=1,
        ),


        "SVM":

        SVC(
            C=2.0,
            kernel="linear",
            probability=True,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),


        "XGBoost":

        XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="multi:softprob",
            num_class=n_classes,
            eval_metric="mlogloss",
            tree_method="hist",
            random_state=RANDOM_STATE,
            n_jobs=4,
        ),


        "Neural Network":

        MLPClassifier(
            hidden_layer_sizes=(128, 64),
            activation="relu",
            solver="adam",
            max_iter=500,
            random_state=RANDOM_STATE,
        ),
    }


    # ========================================================
    # TRAIN AND COMPARE
    # ========================================================

    model_results = []

    best_model = None
    best_model_name = None
    best_accuracy = -1


    for model_name, model in models.items():

        logger.info(
            "Training %s...",
            model_name,
        )

        model.fit(
            X_train_tfidf,
            y_train,
        )


        logger.info(
            "Evaluating %s...",
            model_name,
        )

        predictions = model.predict(
            X_test_tfidf
        )


        metrics = calculate_metrics(
            y_test,
            predictions,
        )


        result = {
            "model": model_name,
            "accuracy": metrics["accuracy"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1_score": metrics["f1_score"],
        }


        model_results.append(
            result
        )


        logger.info(
            "%s -> Accuracy: %.2f%% | "
            "Precision: %.2f%% | "
            "Recall: %.2f%% | "
            "F1: %.2f%%",

            model_name,

            metrics["accuracy"] * 100,
            metrics["precision"] * 100,
            metrics["recall"] * 100,
            metrics["f1_score"] * 100,
        )


        # ----------------------------------------------------
        # SELECT BEST MODEL
        # ----------------------------------------------------

        if metrics["accuracy"] > best_accuracy:

            best_accuracy = metrics["accuracy"]

            best_model = model

            best_model_name = model_name


    logger.info(
        "Best model: %s",
        best_model_name,
    )


    return TrainingResult(

        vectorizer=vectorizer,

        encoder=encoder,

        classifier=best_model,

        best_model_name=best_model_name,

        model_results=model_results,

        n_samples=n_samples,

        n_train=n_train,

        n_test=n_test,

        n_classes=n_classes,

        class_names=list(
            encoder.classes_
        ),
    )


# ============================================================
# SAVE ARTEFACTS
# ============================================================

def save_artefacts(result):

    MODELS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    # Save TF-IDF vectorizer

    joblib.dump(
        result.vectorizer,
        VECTORIZER_PATH,
    )


    # Save label encoder

    joblib.dump(
        result.encoder,
        ENCODER_PATH,
    )


    # Save BEST model

    joblib.dump(
        result.classifier,
        CLASSIFIER_PATH,
    )


    # Save performance results

    joblib.dump(
        {
            "best_model": result.best_model_name,
            "results": result.model_results,
            "total_samples": result.n_samples,
            "training_samples": result.n_train,
            "testing_samples": result.n_test,
            "disease_classes": result.n_classes,
        },
        PERFORMANCE_PATH,
    )


    logger.info(
        "All artefacts saved successfully."
    )


# ============================================================
# PRINT REPORT
# ============================================================

def print_report(result):

    print("\n")
    print("=" * 70)

    print("MEDISYS AI - MULTI MODEL PERFORMANCE REPORT")

    print("=" * 70)

    print()

    print(
        f"Total Samples: {result.n_samples}"
    )

    print(
        f"Training Samples: {result.n_train}"
    )

    print(
        f"Testing Samples: {result.n_test}"
    )

    print(
        f"Disease Classes: {result.n_classes}"
    )

    print()

    print("-" * 70)

    print(
        f"{'Model':25}"
        f"{'Accuracy':12}"
        f"{'Precision':12}"
        f"{'Recall':12}"
        f"{'F1 Score':12}"
    )

    print("-" * 70)


    for result_data in result.model_results:

        print(
            f"{result_data['model']:25}"
            f"{result_data['accuracy'] * 100:10.2f}%"
            f"{result_data['precision'] * 100:12.2f}%"
            f"{result_data['recall'] * 100:10.2f}%"
            f"{result_data['f1_score'] * 100:12.2f}%"
        )


    print("-" * 70)

    print()

    print(
        f"BEST MODEL: {result.best_model_name}"
    )

    print()

    print(
        "Best model saved as:"
    )

    print(
        "disease_classifier.pkl"
    )

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    logging.basicConfig(

        level=logging.INFO,

        format=(
            "%(asctime)s | "
            "%(levelname)-8s | "
            "%(name)s - "
            "%(message)s"
        ),

        datefmt="%Y-%m-%d %H:%M:%S",

        stream=sys.stdout,
    )


    logger.info(
        "MediSys AI multi-model training started..."
    )


    try:

        result = train()

        save_artefacts(
            result
        )

        print_report(
            result
        )


    except Exception as exc:

        logger.exception(
            "Training failed: %s",
            exc,
        )

        sys.exit(1)


    logger.info(
        "Training completed successfully."
    )


if __name__ == "__main__":
    main()