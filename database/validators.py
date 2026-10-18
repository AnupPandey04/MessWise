from database.connection import db

# Reusable definitions for non-negative whole numbers
NON_NEGATIVE_INT = {
    "bsonType": ["int", "long"],
    "minimum": 0
}

NON_NEGATIVE_NUMBER = {
    "bsonType": ["int", "long", "double", "decimal"],
    "minimum": 0
}

DATE_TYPE = {"bsonType": "date"}

SCHEMAS = {
    "menu_items": {
        "bsonType": "object",
        "required": ["item_name", "category", "unit_cost", "active"],
        "properties": {
            "item_name": {
                "bsonType": "string",
                "minLength": 2
            },
            "category": {
                "bsonType": "string",
                "enum": ["breakfast", "lunch", "dinner", "snack"]
            },
            "unit_cost": NON_NEGATIVE_NUMBER,
            "active": {"bsonType": "bool"}
        }
    },

    "meal_records": {
        "bsonType": "object",
        "required": [
            "date", "meal_type", "menu_item_ids",
            "prepared_meals", "served_meals",
            "leftover_meals", "attendance_count"
        ],
        "properties": {
            "date": DATE_TYPE,
            "meal_type": {
                "bsonType": "string",
                "enum": ["breakfast", "lunch", "dinner"]
            },
            "menu_item_ids": {
                "bsonType": "array",
                "items": {"bsonType": "objectId"}
            },
            "prepared_meals": NON_NEGATIVE_INT,
            "served_meals": NON_NEGATIVE_INT,
            "leftover_meals": NON_NEGATIVE_INT,
            "attendance_count": NON_NEGATIVE_INT
        }
    },

    "attendance": {
        "bsonType": "object",
        "required": [
            "date", "meal_type", "expected_count", "actual_count"
        ],
        "properties": {
            "date": DATE_TYPE,
            "meal_type": {
                "bsonType": "string",
                "enum": ["breakfast", "lunch", "dinner"]
            },
            "expected_count": NON_NEGATIVE_INT,
            "actual_count": NON_NEGATIVE_INT
        }
    },

    "waste_logs": {
        "bsonType": "object",
        "required": [
            "record_id", "item_id", "quantity_kg", "reason", "logged_at"
        ],
        "properties": {
            "record_id": {"bsonType": "objectId"},
            "item_id": {"bsonType": "objectId"},
            "quantity_kg": NON_NEGATIVE_NUMBER,
            "reason": {
                "bsonType": "string",
                "enum": [
                    "overproduction",
                    "spoiled",
                    "serving_leftovers",
                    "other"
                ]
            },
            "logged_at": DATE_TYPE
        }
    },

    "predictions": {
        "bsonType": "object",
        "required": [
            "target_date", "meal_type", "predicted_demand",
            "model_name", "created_at"
        ],
        "properties": {
            "target_date": DATE_TYPE,
            "meal_type": {
                "bsonType": "string",
                "enum": ["breakfast", "lunch", "dinner"]
            },
            "predicted_demand": NON_NEGATIVE_NUMBER,
            "model_name": {"bsonType": "string"},
            "created_at": DATE_TYPE
        }
    }
}


def setup_validators():
    for collection_name, schema in SCHEMAS.items():
        validator = {"$jsonSchema": schema}

        if collection_name in db.list_collection_names():
            # Updated validation on an existing collection
            db.command({
                "collMod": collection_name,
                "validator": validator,
                "validationLevel": "strict",
                "validationAction": "error"
            })
        else:
            # Created a new collection with validation
            db.create_collection(
                collection_name,
                validator=validator,
                validationLevel="strict",
                validationAction="error"
            )

        print(f"Validator configured: {collection_name}")


if __name__ == "__main__":
    setup_validators()
