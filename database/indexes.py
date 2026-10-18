from pymongo import ASCENDING, DESCENDING

from database.connection import db


def setup_indexes():
    # Menu items
    db.menu_items.create_index(
        [("item_name", ASCENDING)],
        unique=True,
        name="unique_menu_item_name"
    )
    db.menu_items.create_index(
        [("category", ASCENDING), ("active", ASCENDING)],
        name="category_active_idx"
    )

    # Meal records
    db.meal_records.create_index(
        [("date", DESCENDING), ("meal_type", ASCENDING)],
        unique=True,
        name="unique_date_meal_type"
    )

    # Attendance
    db.attendance.create_index(
        [("date", DESCENDING), ("meal_type", ASCENDING)],
        unique=True,
        name="unique_attendance_date_meal"
    )

    # Waste logs
    db.waste_logs.create_index(
        [("logged_at", DESCENDING)],
        name="waste_logged_at_idx"
    )
    db.waste_logs.create_index(
        [("record_id", ASCENDING)],
        name="waste_record_id_idx"
    )

    # Predictions
    db.predictions.create_index(
        [("target_date", ASCENDING), ("meal_type", ASCENDING)],
        name="prediction_date_meal_idx"
    )

    print("All indexes configured successfully!")


if __name__ == "__main__":
    setup_indexes()
