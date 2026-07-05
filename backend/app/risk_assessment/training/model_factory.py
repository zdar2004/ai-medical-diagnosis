"""Model factory utilities for the Risk Assessment module.

This module provides a reusable :class:`ModelFactory` class responsible
solely for instantiating supported machine learning models by name. It
performs no training, evaluation, or persistence of any kind.
"""

from typing import Any, Dict, Optional

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC

from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

SUPPORTED_MODELS = {"logistic", "random_forest", "svm", "xgboost", "neural_network"}


class ModelFactory:
    """Instantiate supported machine learning models by name.

    This class is a pure factory: given a model name and optional
    hyperparameters, it returns a freshly initialized (untrained) model
    instance. It contains no training, evaluation, or model-saving
    logic, and no disease-specific behavior.

    Supported model names:
        - ``"logistic"``: :class:`sklearn.linear_model.LogisticRegression`
        - ``"random_forest"``: :class:`sklearn.ensemble.RandomForestClassifier`
        - ``"svm"``: :class:`sklearn.svm.SVC`
        - ``"xgboost"``: :class:`xgboost.XGBClassifier`
        - ``"neural_network"``: :class:`sklearn.neural_network.MLPClassifier`
    """

    @staticmethod
    def get_model(model_name: str, model_params: Optional[Dict[str, Any]] = None) -> Any:
        """Return an initialized (untrained) model instance by name.

        Args:
            model_name: Name of the model to instantiate. Must be one of
                ``"logistic"``, ``"random_forest"``, ``"svm"``,
                ``"xgboost"``, or ``"neural_network"`` (case-insensitive).
            model_params: Optional dictionary of hyperparameters to pass
                to the model's constructor. If ``None``, sensible default
                hyperparameters are used.

        Returns:
            Any: An untrained model instance corresponding to
            ``model_name``.

        Raises:
            ValueError: If ``model_name`` is not one of the supported
                model names.
            ImportError: If ``model_name`` is ``"xgboost"`` but the
                ``xgboost`` package is not installed.
        """
        if not isinstance(model_name, str):
            error_message = f"model_name must be a string, got {type(model_name).__name__}."
            logger.error(error_message)
            raise ValueError(error_message)

        normalized_name = model_name.strip().lower()
        params = model_params.copy() if model_params else {}

        if normalized_name not in SUPPORTED_MODELS:
            error_message = (
                f"Unsupported model name '{model_name}'. "
                f"Supported models are: {sorted(SUPPORTED_MODELS)}."
            )
            logger.error(error_message)
            raise ValueError(error_message)

        try:
            if normalized_name == "logistic":
                params.setdefault("max_iter", 1000)
                params.setdefault("random_state", 42)
                params.setdefault("class_weight", "balanced")
                model = LogisticRegression(**params)

            elif normalized_name == "random_forest":
                params.setdefault("n_estimators", 100)
                params.setdefault("random_state", 42)
                params.setdefault("class_weight", "balanced")
                model = RandomForestClassifier(**params)

            elif normalized_name == "svm":
                params.setdefault("probability", True)
                params.setdefault("random_state", 42)
                params.setdefault("class_weight", "balanced")
                model = SVC(**params)

            elif normalized_name == "xgboost":
                model = ModelFactory._build_xgboost_model(params)

            elif normalized_name == "neural_network":
                params.setdefault("max_iter", 500)
                params.setdefault("random_state", 42)
                model = MLPClassifier(**params)

            else:
                # Unreachable due to the membership check above, kept for safety.
                error_message = f"Unsupported model name '{model_name}'."
                logger.error(error_message)
                raise ValueError(error_message)

            logger.info(
                "Instantiated model '%s' with params=%s -> %s",
                normalized_name,
                params,
                type(model).__name__,
            )
            return model

        except (ValueError, ImportError):
            raise
        except Exception as error:
            error_message = f"Failed to instantiate model '{model_name}': {error}"
            logger.error(error_message)
            raise ValueError(error_message) from error

    @staticmethod
    def _build_xgboost_model(params: Dict[str, Any]) -> Any:
        """Instantiate an XGBoost classifier.

        Isolated into its own method so that the optional ``xgboost``
        dependency is only imported when actually requested.

        Args:
            params: Hyperparameters to pass to
                :class:`xgboost.XGBClassifier`.

        Returns:
            Any: An untrained :class:`xgboost.XGBClassifier` instance.

        Raises:
            ImportError: If the ``xgboost`` package is not installed.
        """
        try:
            from xgboost import XGBClassifier
        except ImportError as error:
            error_message = (
                "The 'xgboost' package is required to use model_name='xgboost' "
                "but is not installed. Install it with 'pip install xgboost'."
            )
            logger.error(error_message)
            raise ImportError(error_message) from error

        params.setdefault("eval_metric", "logloss")
        params.setdefault("random_state", 42)

        return XGBClassifier(**params)