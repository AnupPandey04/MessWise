from datetime import datetime, timedelta
import random

from database.connection import db

random.seed(42)

# Synthetic menu data: name, category, cost per serving
MENU = [
    ("Vegetable Poha", "breakfast", 25.0),
    ("Aloo Paratha", "breakfast", 35.0),
    ("Idli Sambhar", "breakfast", 30.0),
    ("Dal Rice", "lunch", 55.0),
    ("Rajma Rice", "lunch", 60.0),
    ("Paneer Curry", "dinner", 80.0),
    ("Roti Sabzi", "dinner", 50.0),
    ("Fruit Bowl", "snack", 30.0),
]

MEAL_ITEMS = {
    "breakfast": ["Vegetable Poha", "Aloo Paratha", "Idli Sambhar"],
    "lunch": ["Dal Rice", "Rajma Rice"],
    "dinner": ["Paneer Curry", "Roti Sabzi"],
}

# Average demand and variation for simulated attendance
BASE_DEMAND = {
    "breakfast": 220,
    "lunch": 380,
    "dinner": 320,
}


def clear_seed_collections():
    """Reset the project collections before generating fresh data."""
    for name in [
        "menu_items",
        "meal_records",
        "attendance",
        "waste_logs",
        "predictions",
    ]:
        db[name].delete_many({})


def create_menu():
    """Insert menu items and return their MongoDB ObjectIds."""
    menu_ids = {}

    for name, category, cost in MENU:
        result = db.menu_items.insert_one({
            "item_name": name,
            "category": category,
            "unit_cost": cost,
            "active": True,
        })
        menu_ids[name] = result.inserted_id

    return menu_ids


def generate_history(menu_ids):
    """Generate 30 days of attendance, meals, and waste records."""
    today = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    demand_history = {
        meal_type: [] for meal_type in BASE_DEMAND
    }

    for day_offset in range(29, -1, -1):
        date = today - timedelta(days=day_offset)
        weekend = date.weekday() >= 5

        for meal_type, base in BASE_DEMAND.items():
            # Simulate lower attendance on weekends
            weekend_factor = 0.78 if weekend else 1.0
            actual_count = max(
                0,
                round(
                    base * weekend_factor
                    + random.gauss(0, base * 0.07)
                ),
            )

            expected_count = max(
                0, round(base * weekend_factor)
            )

            db.attendance.insert_one({
                "date": date,
                "meal_type": meal_type,
                "expected_count": expected_count,
                "actual_count": actual_count,
            })

            # Prepare slightly more or less than actual demand
            prepared = max(
                0, round(actual_count * random.uniform(0.90, 1.12))
            )
            served = min(actual_count, prepared)
            leftover = prepared - served

            selected_names = random.sample(
                MEAL_ITEMS[meal_type],
                k=min(2, len(MEAL_ITEMS[meal_type])),
            )

            record = {
                "date": date,
                "meal_type": meal_type,
                "menu_item_ids": [
                    menu_ids[name] for name in selected_names
                ],
                "prepared_meals": prepared,
                "served_meals": served,
                "leftover_meals": leftover,
                "attendance_count": actual_count,
            }

            record_id = db.meal_records.insert_one(
                record
            ).inserted_id

            demand_history[meal_type].append(actual_count)

            # Simulated waste: about 0.35 kg per leftover serving
            if leftover > 0:
                waste_kg = round(
                    leftover * random.uniform(0.25, 0.40), 2
                )

                db.waste_logs.insert_one({
                    "record_id": record_id,
                    "item_id": menu_ids[
                        random.choice(selected_names)
                    ],
                    "quantity_kg": waste_kg,
                    "reason": random.choice([
                        "overproduction",
                        "serving_leftovers",
                        "other",
                    ]),
                    "logged_at": date + timedelta(hours=21),
                })

    return demand_history, today


def create_baseline_predictions(demand_history, today):
    """Forecast demand using the historical mean for each meal."""
    created_at = datetime.now()

    for offset in range(1, 8):
        target_date = today + timedelta(days=offset)

        for meal_type, values in demand_history.items():
            # Simple baseline, not yet an ML model
            predicted = round(sum(values) / len(values))

            db.predictions.insert_one({
                "target_date": target_date,
                "meal_type": meal_type,
                "predicted_demand": predicted,
                "model_name": "historical_mean_baseline",
                "created_at": created_at,
            })


def seed_database():
    # WARNING: This resets the five project collections.
    clear_seed_collections()

    menu_ids = create_menu()
    demand_history, today = generate_history(menu_ids)
    create_baseline_predictions(demand_history, today)

    print("\nMessWise seed data created successfully!")
    print(f"Menu items: {db.menu_items.count_documents({})}")
    print(f"Meal records: {db.meal_records.count_documents({})}")
    print(f"Attendance records: {db.attendance.count_documents({})}")
    print(f"Waste logs: {db.waste_logs.count_documents({})}")
    print(f"Predictions: {db.predictions.count_documents({})}")


if __name__ == "__main__":
    seed_database()
