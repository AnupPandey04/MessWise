from datetime import datetime

from pymongo.errors import DuplicateKeyError, WriteError

from database.connection import db


def test_valid_menu_item():
    item = {
        "item_name": "Test Integrity Dish",
        "category": "breakfast",
        "unit_cost": 25.0,
        "active": True,
    }

    result = db.menu_items.insert_one(item)

    try:
        saved = db.menu_items.find_one(
            {"_id": result.inserted_id}
        )
        assert saved is not None
        assert saved["item_name"] == "Test Integrity Dish"
        print("PASS: Valid insert and read")
    finally:
        db.menu_items.delete_one({"_id": result.inserted_id})


def test_invalid_menu_item():
    try:
        db.menu_items.insert_one({
            "item_name": "Invalid Test Dish",
            "category": "invalid_category",
            "unit_cost": 25.0,
            "active": True,
        })
    except WriteError:
        print("PASS: Invalid category rejected")
        return

    raise AssertionError("Invalid category was accepted")


def test_unique_menu_name():
    item = {
        "item_name": "Test Unique Dish",
        "category": "breakfast",
        "unit_cost": 30.0,
        "active": True,
    }

    first_id = db.menu_items.insert_one(item).inserted_id

    try:
        try:
            db.menu_items.insert_one(item.copy())
        except DuplicateKeyError:
            print("PASS: Duplicate menu name rejected")
        else:
            raise AssertionError(
                "Duplicate menu name was accepted"
            )
    finally:
        db.menu_items.delete_one({"_id": first_id})


def test_update_and_delete():
    result = db.menu_items.insert_one({
        "item_name": "Test Update Dish",
        "category": "lunch",
        "unit_cost": 40.0,
        "active": True,
    })

    item_id = result.inserted_id

    try:
        db.menu_items.update_one(
            {"_id": item_id},
            {"$set": {"unit_cost": 45.0}},
        )

        updated = db.menu_items.find_one({"_id": item_id})
        assert updated["unit_cost"] == 45.0
        print("PASS: Update operation")

        db.menu_items.delete_one({"_id": item_id})
        assert db.menu_items.find_one({"_id": item_id}) is None
        print("PASS: Delete operation")
    finally:
        db.menu_items.delete_one({"_id": item_id})


def test_prediction_records():
    count = db.predictions.count_documents({
        "model_name": "random_forest_v1"
    })

    assert count == 21, (
        f"Expected 21 Random Forest forecasts, found {count}"
    )
    print("PASS: 21 Random Forest forecasts exist")


def run_tests():
    test_valid_menu_item()
    test_invalid_menu_item()
    test_unique_menu_name()
    test_update_and_delete()
    test_prediction_records()

    print("\nAll database checks passed!")


if __name__ == "__main__":
    run_tests()
