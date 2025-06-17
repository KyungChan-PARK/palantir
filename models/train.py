import mlflow
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


def train(data: pd.DataFrame, label: str, experiment: str = "default") -> float:
    """Train a simple classifier and log to MLflow."""
    mlflow.set_experiment(experiment)
    with mlflow.start_run():
        X = data.drop(columns=[label])
        y = data[label]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        clf = LogisticRegression(max_iter=1000)
        clf.fit(X_train, y_train)
        preds = clf.predict(X_test)
        acc = accuracy_score(y_test, preds)
        mlflow.log_metric("accuracy", acc)
        mlflow.sklearn.log_model(clf, "model")
        return acc
