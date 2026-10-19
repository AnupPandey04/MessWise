from datetime import datetime, timedelta

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from database.connection import db

MEAL_CODES = {"breakfast": 0, "lunch": 1, "dinner": 2}
FEATURES = ["day_of_week", "is_weekend", "meal_code"]
MODEL_NAME = "random_forest_v1"


def load_data():
    """Load attendance records and prepare model features."""
    records = list(
        db.attendance.find(
            {},
            {"_id": 0, "date": 1, "meal_type": 1, "actual_count": 1},
        ).sort("date", 1)
    )

    if not records:
        raise ValueError("No attendance data found. Run database.seed_data first.")

    data = pd.DataFrame(records)
    data["date"] = pd.to_datetime(data["date"])
    data["day_of_week"] = data["date"].dt.dayofweek
    data["is_weekend"] = (data["day_of_week"] >= 5).astype(int)
    data["meal_code"] = data["meal_type"].map(MEAL_CODES)

    return data


def build_model():
    """Create the Random Forest model."""
    return RandomForestRegressor(
        n_estimators=100,
        max_depth=5,
        random_state=42,
    )


def evaluate_model(data):
    """Evaluate the model on the latest seven calendar days."""
    cutoff = data["date"].max().normalize() - pd.Timedelta(days=6)
    train = data[data["date"] < cutoff]
    test = data[data["date"] >= cutoff]

    if train.empty or test.empty:
        raise ValueError("Not enough historical data to evaluate the model.")

    model = build_model()
    model.fit(train[FEATURES], train["actual_count"])
    predictions = model.predict(test[FEATURES])

    model_mae = mean_absolute_error(test["actual_count"], predictions)

    # Baseline: predict the training average for each meal type.
    meal_averages = train.groupby("meal_type")["actual_count"].mean()
    baseline_predictions = test["meal_type"].map(meal_averages)
    baseline_mae = mean_absolute_error(
        test["actual_count"], baseline_predictions
    )

    improvement = (
        (baseline_mae - model_mae) / baseline_mae * 100
        if baseline_mae else 0
    )

    result = {
        "evaluation_name": "latest",
        "model_name": MODEL_NAME,
        "evaluation_date": datetime.now(),
        "training_records": len(train),
        "test_records": len(test),
        "model_mae": round(float(model_mae), 2),
        "baseline_mae": round(float(baseline_mae), 2),
        "improvement_percent": round(float(improvement), 2),
        "test_start_date": test["date"].min().to_pydatetime(),
        "test_end_date": test["date"].max().to_pydatetime(),
    }

    db.model_evaluations.update_one(
        {"evaluation_name": "latest"},
        {"$set": result},
        upsert=True,
    )

    print("\nMODEL EVALUATION")
    print(f"Training records: {len(train)}")
    print(f"Test records: {len(test)}")
    print(f"Random Forest MAE: {model_mae:.2f}")
    print(f"Baseline MAE: {baseline_mae:.2f}")
    print(f"Improvement over baseline: {improvement:.2f}%")
    print("Lower MAE is better.")

    return model


def save_forecasts(data):
    """Generate and save forecasts for the next seven days."""
    model = build_model()
    model.fit(data[FEATURES], data["actual_count"])

    last_date = data["date"].max().normalize()
    created_at = datetime.now()
    count = 0

    for offset in range(1, 8):
        date = last_date + timedelta(days=offset)
        day = date.weekday()

        for meal_type, meal_code in MEAL_CODES.items():
            features = pd.DataFrame([{
                "day_of_week": day,
                "is_weekend": int(day >= 5),
                "meal_code": meal_code,
            }])

            demand = max(0, round(float(model.predict(features)[0])))
            forecast = {
                "target_date": date.to_pydatetime(),
                "meal_type": meal_type,
                "predicted_demand": demand,
                "model_name": MODEL_NAME,
                "created_at": created_at,
            }

            db.predictions.update_one(
                {
                    "target_date": forecast["target_date"],
                    "meal_type": meal_type,
                    "model_name": MODEL_NAME,
                },
                {"$set": forecast},
                upsert=True,
            )
            count += 1

    print(f"Saved {count} forecasts for seven days.")


def main():
    data = load_data()
    print(f"Historical attendance records: {len(data)}")
    print(f"Date range: {data['date'].min().date()} to {data['date'].max().date()}")

    evaluate_model(data)
    save_forecasts(data)


if __name__ == "__main__":
    main()
