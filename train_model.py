import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


DATA_FILE = "data/flood_risk_ml_data.csv"
MODEL_DIR = "models"
MODEL_FILE = os.path.join(
    MODEL_DIR,
    "flood_risk_model.joblib"
)

FEATURES = [
    "rainfall_24h",
    "rainfall_72h",
    "max_hourly_rain",
    "humidity",
    "temperature",
    "current_rain"
]

TARGET = "flood_risk"


def main():

    print("Loading ML dataset...")

    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found.")
        return

    df = pd.read_csv(DATA_FILE)

    required_columns = FEATURES + [TARGET]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        print("Missing columns:")
        print(missing_columns)
        return

    df = df.dropna(
        subset=required_columns
    ).copy()

    print(f"Total records: {len(df)}")

    print()
    print("Class distribution:")
    print(df[TARGET].value_counts())

    X = df[FEATURES]
    y = df[TARGET]

    # Keep approximately the same class proportions
    # in training and testing data.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    print()
    print(f"Training records: {len(X_train)}")
    print(f"Testing records: {len(X_test)}")

    print()
    print("Training Random Forest model...")

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced",
        min_samples_leaf=2,
        n_jobs=-1
    )

    model.fit(
        X_train,
        y_train
    )

    predictions = model.predict(
        X_test
    )

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    print()
    print("Model training completed!")

    print()
    print(
        f"Test Accuracy: {accuracy * 100:.2f}%"
    )

    print()
    print("Classification Report:")
    print(
        classification_report(
            y_test,
            predictions,
            labels=[
                "LOW",
                "MEDIUM",
                "HIGH"
            ],
            zero_division=0
        )
    )

    print("Confusion Matrix:")
    print(
        confusion_matrix(
            y_test,
            predictions,
            labels=[
                "LOW",
                "MEDIUM",
                "HIGH"
            ]
        )
    )

    print()
    print("Feature Importance:")

    feature_importance = pd.Series(
        model.feature_importances_,
        index=FEATURES
    ).sort_values(
        ascending=False
    )

    print(feature_importance)

    os.makedirs(
        MODEL_DIR,
        exist_ok=True
    )

    model_package = {
        "model": model,
        "features": FEATURES,
        "classes": list(model.classes_),
        "model_type": "RandomForestClassifier",
        "label_type": "rainfall_based_weather_risk_proxy"
    }

    joblib.dump(
        model_package,
        MODEL_FILE
    )

    print()
    print(
        f"Model saved successfully: {MODEL_FILE}"
    )

    print()
    print(
        "IMPORTANT: Accuracy measures performance "
        "against rainfall-based proxy labels. "
        "It does not prove real-world flood-event accuracy."
    )


if __name__ == "__main__":
    main()