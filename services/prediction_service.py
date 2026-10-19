from datetime import datetime, timedelta

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from database.connection import db

MODEL_NAME = "random_forest_v1"
MEAL_CODES = {"breakfast": 0, "lunch": 1, "dinner": 2}
FEATURES = ["day_of_week", "is_weekend", "meal_code"]


def load_data():
    """Read historical attendance from MongoDB."""
    records = list(
        db.attendance.find(
            {},
            {"_id": 0, "date": 1, "meal_type": 1, "actual_count": 1},
        ).sort("date", 1)
    )
    if not records:
        raise ValueError("No attendance data. Run database.seed_data first.")

    data = pd.DataFrame(records)
    data["date"] = pd.to_datetime(data["date"])
    data["day_of_week"] = data["date"].dt.dayofweek
    data["is_weekend"] = (data["day_of_week"] >= 5).astype(int)
    data["meal_code"] = data["meal_type"].map(MEAL_CODES)
    return data


def build_model():
    """Create a Random Forest regression model."""
    return RandomForestRegressor(
        n_estimators=100,
        max_depth=5,
        random_state=42,
    )


def evaluate_model(data):
    """Train on earlier dates and evaluate on the latest seven days."""
    cutoff = data["date"].max().normalize() - pd.Timedelta(days=6)
    train = data[data["date"] < cutoff]
    test = data[data["date"] >= cutoff]

    if train.empty or test.empty:
        raise ValueError("Not enough historical records to evaluate the model.")

    model = build_model()
    model.fit(train[FEATURES], train["actual_count"])
    predicted = model.predict(test[FEATURES])

    model_mae = mean_absolute_error(test["actual_count"], predicted)

    # baseline: use the training average for each meal type.
    meal_average = train.groupby("meal_type")["actual_count"].mean()
    baseline = test["meal_type"].map(meal_average)
    baseline_mae = mean_absolute_error(test["actual_count"], baseline)

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
        "result": (
            "Random Forest performed better"
            if model_mae < baseline_mae
            else "Baseline performed better or equally"
        ),
        "test_start_date": test["date"].min().to_pydatetime(),
        "test_end_date": test["date"].max().to_pydatetime(),
    }

    # Store the latest evaluation instead of adding duplicate documents.
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
    print("Note: MAE is an error metric; lower is better.")
    return model


def save_forecasts(data):
    """Train on all records and save predictions for the next seven days."""
    model = build_model()
    model.fit(data[FEATURES], data["actual_count"])

    last_date = data["date"].max().normalize()
    created_at = datetime.now()
    forecasts = []

    for offset in range(1, 8):
        date = last_date + timedelta(days=offset)
        for meal_type, meal_code in MEAL_CODES.items():
            day = date.weekday()
            row = pd.DataFrame([{
                "day_of_week": day,
                "is_weekend": int(day >= 5),
                "meal_code": meal_code,
            }])
            demand = max(0, round(float(model.predict(row)[0])))

            forecasts.append({
                "target_date": date.to_pydatetime(),
                "meal_type": meal_type,
                "predicted_demand": demand,
                "model_name": MODEL_NAME,
                "created_at": created_at,
            })

    # Replace the matching date/meal forecast, avoiding duplicates.
    for forecast in forecasts:
        db.predictions.update_one(
            {
                "target_date": forecast["target_date"],
                "meal_type": forecast["meal_type"],
                "model_name": MODEL_NAME,
            },
            {"$set": forecast},
            upsert=True,
        )

    print(f"Saved {len(forecasts)} forecasts for seven days.")


def main():
    data = load_data()
    print(f"Historical attendance records: {len(data)}")
    print(f"Date range: {data['date'].min().date()} to {data['date'].max().date()}")
    evaluate_model(data)
    save_forecasts(data)


if __name__ == "__main__":
    main()
