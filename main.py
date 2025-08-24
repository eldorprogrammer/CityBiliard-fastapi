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












from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, WriteError
from tenacity import retry, stop_after_attempt, wait_fixed
import os
from config import MONGODB_URI  # config.py dan faqat MONGODB_URI ni import qilamiz

# Doimiy o‘zgaruvchilar
NUM_TABLES = 7  # Jadval raqamlari soni
DURATION_TOLERANCE = 2  # Daqiqalarda ruxsat etilgan farq

# CORS uchun ruxsat berilgan domenlar (config.py o‘rniga bu yerda aniqlaymiz)
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Frontend ilovasi (masalan, React)
    "http://localhost:8000",  # API serveri
    # Ishlab chiqarish domenini qo‘shing: "https://your-production-domain.com"
]

# Log sozlamalari
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI ilovasini yaratish
app = FastAPI()

# CORS sozlamalari (xavfsizlik uchun faqat ruxsat berilgan domenlar)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB ulanishi
try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')  # Ulanishni sinash
    logger.info("MongoDB ga muvaffaqiyatli ulandi")
except Exception as e:
    logger.error(f"MongoDB ga ulanishda xatolik: {e}")
    raise

db = client["billiard_db"]  # Ma'lumotlar bazasi nomi
collection = db["game_stats"]  # To'plam nomi

# Pydantic Model (ma'lumotlarni validatsiya qilish uchun)
class GameUpdate(BaseModel):
    table_num: int  # Jadval raqami
    start_time: str  # Boshlanish vaqti (YYYY-MM-DD HH:MM)
    end_time: str  # Tugash vaqti (YYYY-MM-DD HH:MM)
    duration_minutes: int  # Davomiylik (daqiqalarda)

# Ma'lumotlarni MongoDB ga yangilash funksiyasi (qayta urinish bilan)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def update_data(table_num: int, duration: int):
    try:
        today = datetime.now().strftime('%Y-%m-%d')  # Bugungi sana
        existing_entry = collection.find_one({"date": today})

        if existing_entry:
            if f"table_{table_num}" in existing_entry["tables"]:
                # Mavjud jadvalga vaqt qo'shish
                collection.update_one(
                    {"date": today},
                    {"$inc": {f"tables.table_{table_num}.total_time": duration}}
                )
                logger.info(f"table_{table_num} ga {duration} soniya qo'shildi")
            else:
                # Yangi jadvalni boshlash
                collection.update_one(
                    {"date": today},
                    {"$set": {f"tables.table_{table_num}": {"total_time": duration}}}
                )
                logger.info(f"table_{table_num} {duration} soniya bilan boshlandi")
        else:
            # Yangi kun uchun yozuv yaratish
            new_entry = {
                "date": today,
                "tables": {f"table_{i}": {"total_time": 0} for i in range(1, NUM_TABLES + 1)}
            }
            new_entry["tables"][f"table_{table_num}"]["total_time"] = duration
            collection.insert_one(new_entry)
            logger.info(f"{today} uchun yangi yozuv qo'shildi, table_{table_num} bilan")

    except ConnectionFailure as e:
        logger.error(f"MongoDB ulanish xatosi: {e}")
        raise HTTPException(status_code=503, detail="Ma'lumotlar bazasiga ulanish muvaffaqiyatsiz")
    except WriteError as e:
        logger.error(f"MongoDB yozish xatosi: {e}")
        raise HTTPException(status_code=500, detail="Ma'lumotlar bazasiga yozish muvaffaqiyatsiz")
    except Exception as e:
        logger.error(f"Ma'lumotlarni yangilashda kutilmagan xatolik: {e}")
        raise

# API Endpoint: /update_stats
@app.post("/update_stats")
async def update_stats_api(game_update: GameUpdate):
    try:
        table_num = game_update.table_num
        start_time_str = game_update.start_time
        end_time_str = game_update.end_time
        duration_minutes = game_update.duration_minutes

        # Sana formatini qattiq tekshirish (YYYY-MM-DD HH:MM)
        try:
            start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
            end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M')
        except ValueError:
            logger.error(f"Noto'g'ri sana formati: {start_time_str} yoki {end_time_str}")
            raise HTTPException(status_code=400, detail="Sana formati 'YYYY-MM-DD HH:MM' bo'lishi kerak")

        # Davomiylikni tekshirish
        calculated_duration = int((end_time - start_time).total_seconds() / 60)
        if abs(calculated_duration - duration_minutes) > DURATION_TOLERANCE:
            logger.warning(f"Davomiylik mos kelmadi: kiritilgan {duration_minutes} min, hisoblangan {calculated_duration} min")
            raise HTTPException(status_code=400, detail="Davomiylik mos kelmaydi")

        # Jadval raqamini tekshirish
        if not 1 <= table_num <= NUM_TABLES:
            logger.error(f"Noto'g'ri jadval raqami: {table_num}")
            raise HTTPException(status_code=400, detail=f"Jadval raqami 1 dan {NUM_TABLES} gacha bo'lishi kerak")

        duration_seconds = duration_minutes * 60
        if duration_seconds <= 0:
            raise HTTPException(status_code=400, detail="Noto'g'ri davomiylik")

        update_data(table_num, duration_seconds)
        logger.info(f"table_{table_num} {duration_seconds} soniya bilan muvaffaqiyatli yangilandi")

        return {"status": "success", "message": f"table_{table_num} {duration_seconds} soniya bilan yangilandi"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"update_stats_api da xatolik: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API Endpoint: / (test uchun)
@app.get("/")
async def hello():
    return {"message": "Nima gap", "status": "ok"}

# API Endpoint: /health (server va MongoDB holatini tekshirish)
@app.get("/health")
async def health_check():
    try:
        client.admin.command('ping')
        return {"status": "ok", "mongodb": "connected"}
    except Exception as e:
        logger.error(f"Salomatlik tekshiruvida xatolik: {e}")
        raise HTTPException(status_code=503, detail="MongoDB ulanishi muvaffaqiyatsiz")

# Ilova yopilganda MongoDB ulanishini yopish
@app.on_event("shutdown")
def shutdown_event():
    client.close()
    logger.info("MongoDB ulanishi yopildi")

if __name__ == "__main__":
    import uvicorn
    port = os.getenv("PORT", "8000")
    try:
        port = int(port)
        if not 1 <= port <= 65535:
            raise ValueError("Port 1 dan 65535 gacha bo'lishi kerak")
    except ValueError as e:
        logger.error(f"Noto'g'ri port qiymati: {e}")
        port = 8000  # Sukut bo'yicha port
    uvicorn.run(app, host="0.0.0.0", port=port)