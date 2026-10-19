"""Compare MongoDB's indexed query with a forced collection scan."""

from datetime import datetime
from database.connection import db


def explain_query(force_scan=False):
    query = {"date": {"$gte": datetime(2026, 10, 1)}}
    find_command = {"find": "meal_records", "filter": query}

    if force_scan:
        find_command["hint"] = {"$natural": 1}

    result = db.command(
        "explain",
        find_command,
        verbosity="executionStats",
    )
    stats = result["executionStats"]

    print("Collection scan" if force_scan else "Normal query plan")
    print("Documents returned:", stats["nReturned"])
    print("Documents examined:", stats["totalDocsExamined"])
    print("Index keys examined:", stats["totalKeysExamined"])
    print("Execution time (ms):", stats["executionTimeMillis"])


if __name__ == "__main__":
    explain_query()
    explain_query(force_scan=True)
