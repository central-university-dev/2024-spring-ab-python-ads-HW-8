import os
import pickle
from typing import Any, Dict, Tuple

import pandas as pd
from catboost import CatBoostClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score
from sklearn.model_selection import train_test_split
from sklift.datasets import fetch_x5
from sklift.models import SoloModel, TwoModels


class UpliftPipeline:
    """Class to manage the pipeline of data loading, model training,
        and evaluation for uplift modeling.

    Attributes:
        features_path (str): Path to the features file.
        train_path (str): Path to the training data file.
        model_path (str): Base path for saving/loading models.
        model (Optional[object]): Model object after training.
        params_cat (Dict[str, Any]): Parameters for CatBoostClassifier.
        params_rf (Dict[str, Any]): Parameters for RandomForestClassifier.
    """

    def __init__(
        self,
        features_path: str = "df_features.parquet",
        train_path: str = "df_train.parquet",
        model_path: str = "model.pkl",
    ) -> None:
        self.features_path = features_path
        self.train_path = train_path
        self.model_path = model_path
        self.model = None
        self.params_cat = {
            "iterations": 20,
            "thread_count": 2,
            "random_state": 42,
            "silent": True,
        }
        self.params_rf = {"n_estimators": 100, "max_depth": 3, "random_state": 42}

    def load_data(self) -> None:
        """Loads and preprocesses data from the dataset,
        then saves it to parquet files."""
        dataset = fetch_x5()

        df_clients = dataset.data["clients"].set_index("client_id")
        df_train = pd.concat(
            [dataset.data["train"], dataset.treatment, dataset.target], axis=1
        ).set_index("client_id")

        df_features = df_clients.copy()
        df_features["first_issue_time"] = (
            pd.to_datetime(df_features["first_issue_date"]) - pd.Timestamp("1970-01-01")
        ) // pd.Timedelta("1s")
        df_features["first_redeem_time"] = (
            pd.to_datetime(df_features["first_redeem_date"])
            - pd.Timestamp("1970-01-01")
        ) // pd.Timedelta("1s")
        df_features["issue_redeem_delay"] = (
            df_features["first_redeem_time"] - df_features["first_issue_time"]
        )
        df_features = df_features.drop(
            ["first_issue_date", "first_redeem_date"], axis=1
        )

        df_features.to_parquet(self.features_path)
        df_train.to_parquet(self.train_path)

    def make_train_test_split(self, test_size: float) -> None:
        """Splits the data into training and validation sets."""
        self.df_features = pd.read_parquet(self.features_path)
        self.df_train = pd.read_parquet(self.train_path)
        indices_learn, indices_valid = train_test_split(
            self.df_train.index, test_size=test_size, random_state=123
        )
        indices_test = pd.Index(set(self.df_features.index) - set(self.df_train.index))

        self.X_train = self.df_features.loc[indices_learn, :]
        self.y_train = self.df_train.loc[indices_learn, "target"]
        self.treat_train = self.df_train.loc[indices_learn, "treatment_flg"]

        self.X_val = self.df_features.loc[indices_valid, :]
        self.y_val = self.df_train.loc[indices_valid, "target"]
        self.treat_val = self.df_train.loc[indices_valid, "treatment_flg"]

        self.X_test = self.df_features.loc[indices_test, :]

    def train_and_evaluate_model(
        self, approach: str, classifier: str, test_size: float = 0.2
    ) -> float:
        """Trains and evaluates the model based on the approach and classifier type.

        Args:
            approach (str): The modeling approach to use ('Solo Model' or 'Two Models').
            classifier (str): The type of classifier to use ('CatBoost' or 'RandomForest').
            test_size (float): The proportion of the dataset to include in the test split.

        Returns:
            float: The precision score of the model on the validation set.
        """
        uplift_param = {}
        self.make_train_test_split(test_size=test_size)
        model = None

        if approach == "Solo Model":
            if classifier == "CatBoost":
                model = SoloModel(estimator=CatBoostClassifier(**self.params_cat))
                uplift_param = {"estimator_fit_params": {"cat_features": ["gender"]}}
            elif classifier == "RandomForest":
                model = SoloModel(estimator=RandomForestClassifier(**self.params_rf))
        elif approach == "Two Models":
            if classifier == "CatBoost":
                model = TwoModels(
                    estimator_trmnt=CatBoostClassifier(**self.params_cat),
                    estimator_ctrl=CatBoostClassifier(**self.params_cat),
                    method="vanilla",
                )
                uplift_param = {
                    "estimator_trmnt_fit_params": {"cat_features": ["gender"]},
                    "estimator_ctrl_fit_params": {"cat_features": ["gender"]},
                }
            elif classifier == "RandomForest":
                model = TwoModels(
                    estimator_trmnt=RandomForestClassifier(**self.params_rf),
                    estimator_ctrl=RandomForestClassifier(**self.params_rf),
                    method="vanilla",
                )

        if model:
            model.fit(
                X=self.X_train,
                y=self.y_train,
                treatment=self.treat_train,
                **uplift_param
            )
            uplift_preds = model.predict(self.X_val)

            precision = precision_score(self.y_val, uplift_preds > 0.5, average="macro")

            self.save_model(model)

            return precision

    def save_model(self, model: Any) -> None:
        """Saves the trained model to a specified file."""
        with open(self.model_path, "wb") as file:
            pickle.dump(model, file)

    def load_model(self) -> Any:
        """Loads the model from a specified file."""
        with open(self.model_path, "rb") as file:
            self.model = pickle.load(file)
            return self.model
