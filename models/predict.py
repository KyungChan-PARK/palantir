import mlflow
import pandas as pd


def predict(features: dict, model_uri: str = "model"):
    """Load latest MLflow model and return prediction."""
    model = mlflow.pyfunc.load_model(model_uri)
    df = pd.DataFrame([features])
    pred = model.predict(df)
    return pred[0]
