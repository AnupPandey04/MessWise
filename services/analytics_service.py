from database.connection import db


def get_meal_summary():
    pipeline = [
        {
            "$group": {
                "_id": "$meal_type",
                "total_prepared": {"$sum": "$prepared_meals"},
                "total_served": {"$sum": "$served_meals"},
                "total_leftovers": {"$sum": "$leftover_meals"},
                "average_attendance": {
                    "$avg": "$attendance_count"
                },
                "record_count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "meal_type": "$_id",
                "total_prepared": 1,
                "total_served": 1,
                "total_leftovers": 1,
                "average_attendance": {
                    "$round": ["$average_attendance", 2]
                },
                "record_count": 1,
                "leftover_percentage": {
                    "$cond": [
                        {"$gt": ["$total_prepared", 0]},
                        {
                            "$round": [
                                {
                                    "$multiply": [
                                        {
                                            "$divide": [
                                                "$total_leftovers",
                                                "$total_prepared"
                                            ]
                                        },
                                        100
                                    ]
                                },
                                2
                            ]
                        },
                        0
                    ]
                }
            }
        },
        {"$sort": {"meal_type": 1}}
    ]

    return list(db.meal_records.aggregate(pipeline))



def get_waste_by_menu_item():
    pipeline = [
        {
            "$lookup": {
                "from": "menu_items",
                "localField": "item_id",
                "foreignField": "_id",
                "as": "menu_item"
            }
        },
        {"$unwind": "$menu_item"},
        {
            "$group": {
                "_id": "$menu_item.item_name",
                "total_waste_kg": {"$sum": "$quantity_kg"},
                "waste_events": {"$sum": 1},
                "average_waste_kg": {"$avg": "$quantity_kg"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "item_name": "$_id",
                "total_waste_kg": {"$round": ["$total_waste_kg", 2]},
                "waste_events": 1,
                "average_waste_kg": {"$round": ["$average_waste_kg", 2]}
            }
        },
        {"$sort": {"total_waste_kg": -1}}
    ]

    return list(db.waste_logs.aggregate(pipeline))



def get_attendance_summary():
    pipeline = [
        {
            "$group": {
                "_id": "$meal_type",
                "total_expected": {"$sum": "$expected_count"},
                "total_actual": {"$sum": "$actual_count"},
                "average_actual": {"$avg": "$actual_count"},
                "records": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "meal_type": "$_id",
                "total_expected": 1,
                "total_actual": 1,
                "average_actual": {
                    "$round": ["$average_actual", 2]
                },
                "records": 1,
                "attendance_variance": {
                    "$subtract": [
                        "$total_actual",
                        "$total_expected"
                    ]
                }
            }
        },
        {"$sort": {"meal_type": 1}}
    ]

    return list(db.attendance.aggregate(pipeline))


if __name__ == "__main__":
    summaries = get_meal_summary()

    print("\nMESSWISE: MEAL SUMMARY")
    print("=" * 75)

    for summary in summaries:
        print(f"\nMeal type: {summary['meal_type']}")
        print(f"Records: {summary['record_count']}")
        print(f"Total prepared: {summary['total_prepared']}")
        print(f"Total served: {summary['total_served']}")
        print(f"Total leftovers: {summary['total_leftovers']}")
        print(f"Average attendance: {summary['average_attendance']}")
        print(f"Leftover percentage: {summary['leftover_percentage']}%")

    print("\nWASTE BY MENU ITEM")
    print("=" * 60)

    for item in get_waste_by_menu_item():
        print(
            f"{item['item_name']}: "
            f"{item['total_waste_kg']} kg across "
            f"{item['waste_events']} events"
        )


    print("\nATTENDANCE SUMMARY")
    print("=" * 60)

    for item in get_attendance_summary():
        print(
            f"{item['meal_type']}: "
            f"Expected={item['total_expected']}, "
            f"Actual={item['total_actual']}, "
            f"Variance={item['attendance_variance']}"
        )
