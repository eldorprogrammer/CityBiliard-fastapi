from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from datetime import datetime
from pymongo import MongoClient
from config import MONGODB_URI  # MongoDB connection string from config

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI
app = FastAPI()

# MongoDB Client
try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    # Test the connection
    client.admin.command('ping')
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

db = client["billiard_db"]  # Database name
collection = db["game_stats"]  # Collection name

# Pydantic Model (Ma'lumot validatsiyasi uchun)
class GameUpdate(BaseModel):
    table_num: int
    start_time: str
    end_time: str
    duration_minutes: int

# Ma'lumotlarni MongoDB dan o'qish va yangilash funksiyasi
def update_data(table_num: int, duration: int):
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Check if a document exists for today
        existing_entry = collection.find_one({"date": today})
        
        if existing_entry:
            # Update existing document
            if f"table_{table_num}" in existing_entry["tables"]:
                # Increment total_time for the table
                collection.update_one(
                    {"date": today},
                    {"$inc": {f"tables.table_{table_num}.total_time": duration}}
                )
                logger.info(f"Added {duration} seconds to existing table_{table_num}")
            else:
                # Initialize new table entry
                collection.update_one(
                    {"date": today},
                    {"$set": {f"tables.table_{table_num}": {"total_time": duration}}}
                )
                logger.info(f"Initialized table_{table_num} with {duration} seconds")
        else:
            # Create new document for today
            new_entry = {
                "date": today,
                "tables": {f"table_{i}": {"total_time": 0} for i in range(1, 8)}
            }
            new_entry["tables"][f"table_{table_num}"]["total_time"] = duration
            collection.insert_one(new_entry)
            logger.info(f"Added new entry for {today} with table_{table_num}")

    except Exception as e:
        logger.error(f"Error updating data in MongoDB: {e}")
        raise

# API Endpoint: /update_stats
@app.post("/update_stats")
async def update_stats_api(game_update: GameUpdate):
    try:
        table_num = game_update.table_num
        start_time_str = game_update.start_time
        end_time_str = game_update.end_time
        duration_minutes = game_update.duration_minutes

        # Vaqtni tekshirish
        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
        end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M')
        calculated_duration = int((end_time - start_time).total_seconds() / 60)
        if abs(calculated_duration - duration_minutes) > 1:  # 1 daqiqa ichidagi xatolikka ruxsat
            logger.warning(f"Duration mismatch: reported {duration_minutes} min, calculated {calculated_duration} min")
            raise HTTPException(status_code=400, detail="Duration mismatch")

        # Stol raqamini tekshirish
        if not 1 <= table_num <= 7:
            logger.error(f"Invalid table_num: {table_num}")
            raise HTTPException(status_code=400, detail="Table number must be between 1 and 7")

        duration_seconds = duration_minutes * 60
        if duration_seconds <= 0:
            raise HTTPException(status_code=400, detail="Invalid duration")

        # Ma'lumotlarni yangilash
        update_data(table_num, duration_seconds)
        logger.info(f"Successfully updated table_{table_num} with {duration_seconds} seconds from API")

        return {"status": "success", "message": f"Updated table_{table_num} with {duration_seconds} seconds"}
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        raise HTTPException(status_code=400, detail="Invalid date format")
    except Exception as e:
        logger.error(f"Error in update_stats_api: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API Endpoint: /
@app.get("/")
async def hello():
    return {
        "message": "Nima gap",
        "status": "ok"
    }

# MongoDB ulanishini yopish (server yopilganda)
@app.on_event("shutdown")
def shutdown_event():
    client.close()
    logger.info("MongoDB connection closed")

