from database.connection import db


def get_meal_summary():
    """Summarize prepared, served, and leftover meals by meal type."""
    pipeline = [
        {
            "$group": {
                "_id": "$meal_type",
                "total_prepared": {"$sum": "$prepared_meals"},
                "total_served": {"$sum": "$served_meals"},
                "total_leftovers": {"$sum": "$leftover_meals"},
                "average_attendance": {"$avg": "$attendance_count"},
                "record_count": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "meal_type": "$_id",
                "total_prepared": 1,
                "total_served": 1,
                "total_leftovers": 1,
                "average_attendance": {"$round": ["$average_attendance", 2]},
                "record_count": 1,
                "leftover_percentage": {
                    "$cond": [
                        {"$gt": ["$total_prepared", 0]},
                        {
                            "$round": [
                                {
                                    "$multiply": [
                                        {"$divide": ["$total_leftovers", "$total_prepared"]},
                                        100,
                                    ]
                                },
                                2,
                            ]
                        },
                        0,
                    ]
                },
            }
        },
        {"$sort": {"meal_type": 1}},
    ]
    return list(db.meal_records.aggregate(pipeline))


def get_waste_by_menu_item():
    """Join waste logs with menu items and total waste by item."""
    pipeline = [
        {
            "$lookup": {
                "from": "menu_items",
                "localField": "item_id",
                "foreignField": "_id",
                "as": "menu_item",
            }
        },
        {"$unwind": "$menu_item"},
        {
            "$group": {
                "_id": "$menu_item.item_name",
                "total_waste_kg": {"$sum": "$quantity_kg"},
                "waste_events": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "item_name": "$_id",
                "total_waste_kg": {"$round": ["$total_waste_kg", 2]},
                "waste_events": 1,
            }
        },
        {"$sort": {"total_waste_kg": -1}},
    ]
    return list(db.waste_logs.aggregate(pipeline))


def get_attendance_summary():
    """Compare expected and actual attendance by meal type."""
    pipeline = [
        {
            "$group": {
                "_id": "$meal_type",
                "total_expected": {"$sum": "$expected_count"},
                "total_actual": {"$sum": "$actual_count"},
                "average_actual": {"$avg": "$actual_count"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "meal_type": "$_id",
                "total_expected": 1,
                "total_actual": 1,
                "average_actual": {"$round": ["$average_actual", 2]},
                "attendance_variance": {
                    "$subtract": ["$total_actual", "$total_expected"]
                },
            }
        },
        {"$sort": {"meal_type": 1}},
    ]
    return list(db.attendance.aggregate(pipeline))
