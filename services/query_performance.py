from datetime import datetime

from database.connection import db


def compare_query_plans():
    query = {
        "date": {
            "$gte": datetime(2026, 10, 1)
        }
    }

    print("\nQUERY PERFORMANCE ANALYSIS")
    print("=" * 55)

    # Used the database command directly for compatibility
    result = db.command(
        "explain",
        {
            "find": "meal_records",
            "filter": query
        },
        verbosity="executionStats"
    )

    stats = result["executionStats"]
    winning_plan = result["queryPlanner"]["winningPlan"]

    print("\nQuery execution details")
    print("Winning plan:", winning_plan)
    print("Documents returned:", stats["nReturned"])
    print("Keys examined:", stats["totalKeysExamined"])
    print("Documents examined:", stats["totalDocsExamined"])
    print("Execution time (ms):", stats["executionTimeMillis"])



def compare_with_collection_scan():
    query = {
        "date": {
            "$gte": datetime(2026, 10, 1)
        }
    }

    result = db.command(
        "explain",
        {
            "find": "meal_records",
            "filter": query,
            "hint": {"$natural": 1}
        },
        verbosity="executionStats"
    )

    stats = result["executionStats"]
    plan = result["queryPlanner"]["winningPlan"]

    print("\nFORCED COLLECTION SCAN")
    print("=" * 55)
    print("Winning plan:", plan)
    print("Documents returned:", stats["nReturned"])
    print("Keys examined:", stats["totalKeysExamined"])
    print("Documents examined:", stats["totalDocsExamined"])
    print("Execution time (ms):", stats["executionTimeMillis"])


if __name__ == "__main__":
    compare_query_plans()
    compare_with_collection_scan()
