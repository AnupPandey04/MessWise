from pymongo import MongoClient
from pymongo.errors import PyMongoError

from config import MONGO_URI, DATABASE_NAME

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client[DATABASE_NAME]


def test_connection():
    try:
        client.admin.command("ping")
        print("MongoDB connected successfully!")
        print(f"Database configured: {DATABASE_NAME}")
        return True

    except PyMongoError as error:
        print("MongoDB connection failed:", error)
        return False


if __name__ == "__main__":
    test_connection()
