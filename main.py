# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# import logging
# from datetime import datetime
# from pymongo import MongoClient
# from config import MONGODB_URI

# # Logging sozlamalari
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # FastAPI
# app = FastAPI()

# # CORS sozlamalari
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Ishlab chiqarishda aniq domenlarni ko‘rsating
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # MongoDB Client
# try:
#     client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
#     client.admin.command('ping')
#     logger.info("Successfully connected to MongoDB")
# except Exception as e:
#     logger.error(f"Failed to connect to MongoDB: {e}")
#     raise

# db = client["billiard_db"]
# collection = db["game_stats"]

# # Pydantic Model
# class GameUpdate(BaseModel):
#     table_num: int
#     start_time: str
#     end_time: str
#     duration_minutes: int

# # Ma'lumotlarni MongoDB dan o'qish va yangilash funksiyasi
# def update_data(table_num: int, duration: int):
#     try:
#         today = datetime.now().strftime('%Y-%m-%d')
        
#         existing_entry = collection.find_one({"date": today})
        
#         if existing_entry:
#             if f"table_{table_num}" in existing_entry["tables"]:
#                 collection.update_one(
#                     {"date": today},
#                     {"$inc": {f"tables.table_{table_num}.total_time": duration}}
#                 )
#                 logger.info(f"Added {duration} seconds to existing table_{table_num}")
#             else:
#                 collection.update_one(
#                     {"date": today},
#                     {"$set": {f"tables.table_{table_num}": {"total_time": duration}}}
#                 )
#                 logger.info(f"Initialized table_{table_num} with {duration} seconds")
#         else:
#             new_entry = {
#                 "date": today,
#                 "tables": {f"table_{i}": {"total_time": 0} for i in range(1, 8)}
#             }
#             new_entry["tables"][f"table_{table_num}"]["total_time"] = duration
#             collection.insert_one(new_entry)
#             logger.info(f"Added new entry for {today} with table_{table_num}")

#     except Exception as e:
#         logger.error(f"Error updating data in MongoDB: {e}")
#         raise

# # API Endpoint: /update_stats
# @app.post("/update_stats")
# async def update_stats_api(game_update: GameUpdate):
#     try:
#         table_num = game_update.table_num
#         start_time_str = game_update.start_time
#         end_time_str = game_update.end_time
#         duration_minutes = game_update.duration_minutes

#         start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
#         end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M')
#         calculated_duration = int((end_time - start_time).total_seconds() / 60)
#         if abs(calculated_duration - duration_minutes) > 1:
#             logger.warning(f"Duration mismatch: reported {duration_minutes} min, calculated {calculated_duration} min")
#             raise HTTPException(status_code=400, detail="Duration mismatch")

#         if not 1 <= table_num <= 7:
#             logger.error(f"Invalid table_num: {table_num}")
#             raise HTTPException(status_code=400, detail="Table number must be between 1 and 7")

#         duration_seconds = duration_minutes * 60
#         if duration_seconds <= 0:
#             raise HTTPException(status_code=400, detail="Invalid duration")

#         update_data(table_num, duration_seconds)
#         logger.info(f"Successfully updated table_{table_num} with {duration_seconds} seconds from API")

#         return {"status": "success", "message": f"Updated table_{table_num} with {duration_seconds} seconds"}
#     except ValueError as e:
#         logger.error(f"Invalid date format: {e}")
#         raise HTTPException(status_code=400, detail="Invalid date format")
#     except Exception as e:
#         logger.error(f"Error in update_stats_api: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# # API Endpoint: /
# @app.get("/")
# async def hello():
#     return {
#         "message": "Nima gap",
#         "status": "ok"
#     }

# # MongoDB ulanishini yopish
# import os
# @app.on_event("shutdown")
# def shutdown_event():
#     client.close()
#     logger.info("MongoDB connection closed")

# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.getenv("PORT", 8000))
#     uvicorn.run("main:app", host="0.0.0.0", port=port)















from fastapi import FastAPI, HTTPException, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel 
import uvicorn
import os
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_URI, API_TOKEN
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI va Router
app = FastAPI()
router = APIRouter(trailing_slash=False)  # Redirect muammosini oldini olish uchun
app.include_router(router)

# CORS sozlamalari
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ishlab chiqarishda aniq domenlarni ko‘rsating
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# MongoDB Client (asinxron)
try:
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client["billiard_db"]
    collection = db["game_stats"]
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# Autentifikatsiya
security = HTTPBearer()

# Pydantic Model
class GameUpdate(BaseModel):
    table_num: int
    start_time: str
    end_time: str
    duration_minutes: int

# Ma'lumotlarni MongoDB dan o'qish va yangilash funksiyasi (asinxron)
async def update_data(table_num: int, duration: int):
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        existing_entry = await collection.find_one({"date": today})
        
        if existing_entry:
            if f"table_{table_num}" in existing_entry["tables"]:
                await collection.update_one(
                    {"date": today},
                    {"$inc": {f"tables.table_{table_num}.total_time": duration}}
                )
                logger.info(f"Added {duration} seconds to existing table_{table_num}")
            else:
                await collection.update_one(
                    {"date": today},
                    {"$set": {f"tables.table_{table_num}": {"total_time": duration}}}
                )
                logger.info(f"Initialized table_{table_num} with {duration} seconds")
        else:
            new_entry = {
                "date": today,
                "tables": {f"table_{i}": {"total_time": 0} for i in range(1, 8)}
            }
            new_entry["tables"][f"table_{table_num}"]["total_time"] = duration
            await collection.insert_one(new_entry)
            logger.info(f"Added new entry for {today} with table_{table_num}")

    except Exception as e:
        logger.error(f"Error updating data in MongoDB: {e}")
        raise

# API Endpoint: /update_stats
@router.post("/update_stats")
async def update_stats_api(game_update: GameUpdate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Noto'g'ri token")
    
    try:
        table_num = game_update.table_num
        start_time_str = game_update.start_time
        end_time_str = game_update.end_time
        duration_minutes = game_update.duration_minutes

        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
        end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M')
        calculated_duration = int((end_time - start_time).total_seconds() / 60)
        if abs(calculated_duration - duration_minutes) > 1:
            logger.warning(f"Duration mismatch: reported {duration_minutes} min, calculated {calculated_duration} min")
            raise HTTPException(status_code=400, detail="Duration mismatch")

        if not 1 <= table_num <= 7:
            logger.error(f"Invalid table_num: {table_num}")
            raise HTTPException(status_code=400, detail="Table number must be between 1 and 7")

        duration_seconds = duration_minutes * 60
        if duration_seconds <= 0:
            raise HTTPException(status_code=400, detail="Invalid duration")

        await update_data(table_num, duration_seconds)
        logger.info(f"Successfully updated table_{table_num} with {duration_seconds} seconds from API")

        return {"status": "success", "message": f"Updated table_{table_num} with {duration_seconds} seconds"}
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        raise HTTPException(status_code=400, detail="Invalid date format")
    except Exception as e:
        logger.error(f"Error in update_stats_api: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API Endpoint: /
@router.get("/")
async def hello():
    return {
        "message": "Nima gap",
        "status": "ok"
    }

# MongoDB ulanishini yopish
@router.on_event("shutdown")
async def shutdown_event():
    client.close()
    logger.info("MongoDB connection closed")

if __name__ == "__main__":
   
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)