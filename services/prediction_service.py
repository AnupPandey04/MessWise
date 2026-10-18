from datetime import datetime, timedelta

import pandas as pd
from pymongo import UpdateOne
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from database.connection import db


MODEL_NAME = "random_forest_v1"


def load_attendance_data():
    """Load historical attendance from MongoDB."""
    records = list(
        db.attendance.find(
            {},
            {
                "_id": 0,
                "date": 1,
                "meal_type": 1,
                "actual_count": 1,
            },
        ).sort("date", 1)
    )

    if not records:
        raise ValueError(
            "No attendance data found. Run the seed script first."
        )

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])

    # Features derived from the meal date
    df["day_of_week"] = df["date"].dt.dayofweek
    df["is_weekend"] = (
        df["day_of_week"] >= 5
    ).astype(int)

    return df


def build_model():
    """Create a preprocessing and regression pipeline."""
    numeric_features = ["day_of_week", "is_weekend"]
    categorical_features = ["meal_type"]

    preprocessing = ColumnTransformer(
        transformers=[
            ("numeric", "passthrough", numeric_features),
            (
                "meal_type",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features,
            ),
        ]
    )

    return Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=200,
                    max_depth=5,
                    min_samples_leaf=2,
                    random_state=42,
                ),
            ),
        ]
    )



def evaluate_model(df):
    """Evaluate the model and save metrics in MongoDB."""
    latest_date = df["date"].max()
    cutoff = latest_date.normalize() - pd.Timedelta(days=6)

    train = df[df["date"] < cutoff].copy()
    test = df[df["date"] >= cutoff].copy()

    if train.empty or test.empty:
        raise ValueError(
            "Not enough historical data for a chronological split."
        )

    features = ["day_of_week", "is_weekend", "meal_type"]
    target = "actual_count"

    model = build_model()
    model.fit(train[features], train[target])

    predictions = model.predict(test[features])
    model_mae = float(
        mean_absolute_error(test[target], predictions)
    )

    # Baseline: predict each meal type's training-set mean
    meal_means = train.groupby("meal_type")[target].mean()
    baseline_predictions = test["meal_type"].map(meal_means)

    baseline_mae = float(
        mean_absolute_error(test[target], baseline_predictions)
    )

    improvement_percent = (
        (baseline_mae - model_mae) / baseline_mae * 100
        if baseline_mae else 0.0
    )

    if model_mae < baseline_mae:
        result = "Random Forest outperformed the baseline"
    elif model_mae > baseline_mae:
        result = "Historical-mean baseline performed better"
    else:
        result = "Both methods performed equally"

    metrics = {
        "evaluation_name": "latest",
        "model_name": MODEL_NAME,
        "evaluation_date": datetime.now(),
        "training_records": int(len(train)),
        "test_records": int(len(test)),
        "model_mae": round(model_mae, 2),
        "baseline_mae": round(baseline_mae, 2),
        "improvement_percent": round(improvement_percent, 2),
        "result": result,
        "test_start_date": test["date"].min().to_pydatetime(),
        "test_end_date": test["date"].max().to_pydatetime(),
    }

    # Saved the latest evaluation; Note: do not create duplicates on every run
    db.model_evaluations.update_one(
        {"evaluation_name": "latest"},
        {"$set": metrics},
        upsert=True,
    )

    print("\nMODEL EVALUATION")
    print("=" * 45)
    print(f"Training records: {len(train)}")
    print(f"Test records: {len(test)}")
    print(f"Random Forest MAE: {model_mae:.2f}")
    print(f"Historical-mean baseline MAE: {baseline_mae:.2f}")
    print(f"Improvement over baseline: {improvement_percent:.2f}%")
    print(f"Result: {result}")
    print("Evaluation metrics saved to MongoDB.")

    return model
    """Test on the latest seven observed days."""
    latest_date = df["date"].max()
    cutoff = latest_date.normalize() - pd.Timedelta(days=6)

    train = df[df["date"] < cutoff].copy()
    test = df[df["date"] >= cutoff].copy()

    if train.empty or test.empty:
        raise ValueError(
            "Not enough historical data for a chronological split."
        )

    features = ["day_of_week", "is_weekend", "meal_type"]
    target = "actual_count"

    model = build_model()
    model.fit(train[features], train[target])

    predictions = model.predict(test[features])

    model_mae = mean_absolute_error(
        test[target], predictions
    )

    # Baseline: predict each meal type's training-set mean
    meal_means = train.groupby("meal_type")[
        target
    ].mean()

    baseline_predictions = test["meal_type"].map(
        meal_means
    )

    baseline_mae = mean_absolute_error(
        test[target], baseline_predictions
    )

    print("\nMODEL EVALUATION")
    print("=" * 45)
    print(f"Training records: {len(train)}")
    print(f"Test records: {len(test)}")
    print(f"Random Forest MAE: {model_mae:.2f}")
    print(f"Historical-mean baseline MAE: {baseline_mae:.2f}")

    if model_mae < baseline_mae:
        print("Result: Model outperformed the baseline.")
    elif model_mae > baseline_mae:
        print("Result: Baseline performed better.")
    else:
        print("Result: Both methods performed equally.")

    return model


def save_future_predictions(model, df, days=7):
    """Fit on all available history and save future forecasts."""
    features = ["day_of_week", "is_weekend", "meal_type"]

    final_model = build_model()
    final_model.fit(df[features], df["actual_count"])

    last_date = df["date"].max().normalize()
    meal_types = sorted(df["meal_type"].unique())
    created_at = datetime.now()

    operations = []

    for offset in range(1, days + 1):
        target_date = last_date + pd.Timedelta(days=offset)

        for meal_type in meal_types:
            day_of_week = target_date.dayofweek

            future_row = pd.DataFrame([{
                "day_of_week": day_of_week,
                "is_weekend": int(day_of_week >= 5),
                "meal_type": meal_type,
            }])

            predicted = max(
                0,
                round(float(final_model.predict(future_row)[0])),
            )

            operations.append(
                UpdateOne(
                    {
                        "target_date": target_date.to_pydatetime(),
                        "meal_type": meal_type,
                    },
                    {
                        "$set": {
                            "predicted_demand": predicted,
                            "model_name": MODEL_NAME,
                            "created_at": created_at,
                        }
                    },
                    upsert=True,
                )
            )

    if operations:
        result = db.predictions.bulk_write(operations)
        print(f"\nForecasts saved for {days} days.")
        print(f"Inserted: {result.upserted_count}")
        print(f"Updated: {result.modified_count}")


def main():
    df = load_attendance_data()

    print(f"Historical records loaded: {len(df)}")
    print(f"Date range: {df['date'].min().date()} "
          f"to {df['date'].max().date()}")

    # Evaluate with a time-based holdout
    evaluate_model(df)

    # Generate forecasts using all available historical records
    model = build_model()
    features = ["day_of_week", "is_weekend", "meal_type"]
    model.fit(df[features], df["actual_count"])

    save_future_predictions(model, df, days=7)

    print("\nLATEST FORECASTS")
    print("=" * 45)

    forecasts = list(
        db.predictions.find(
            {"model_name": MODEL_NAME},
            {
                "_id": 0,
                "target_date": 1,
                "meal_type": 1,
                "predicted_demand": 1,
                "model_name": 1,
            },
        ).sort([
            ("target_date", 1),
            ("meal_type", 1),
        ])
    )

    for item in forecasts:
        print(
            f"{item['target_date'].date()} | "
            f"{item['meal_type']:10} | "
            f"Predicted demand: {item['predicted_demand']}"
        )


if __name__ == "__main__":
    main()
