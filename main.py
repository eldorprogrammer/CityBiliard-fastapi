







from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import logging
from datetime import datetime
import os

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI
app = FastAPI()

# Pydantic Model (Ma'lumot validatsiyasi uchun)
class GameUpdate(BaseModel):
    table_num: int
    start_time: str
    end_time: str
    duration_minutes: int

# Ma'lumotlarni JSON dan o'qish va yangilash funksiyasi
def update_data(table_num: int, duration: int):
    try:
        # Faylni o'qish yoki yangi yaratish
        try:
            with open('data.json', 'r', encoding='utf-8') as file:
                current_data = json.load(file) if os.path.getsize('data.json') > 0 else {"data": []}
        except FileNotFoundError:
            current_data = {"data": []}
            logger.info("data.json fayli topilmadi, yangi yaratildi.")

        today = datetime.now().strftime('%Y-%m-%d')
        found = False
        for entry in current_data["data"]:
            if entry["date"] == today:
                found = True
                if f"table_{table_num}" in entry["tables"]:
                    entry["tables"][f"table_{table_num}"]["total_time"] += duration
                    logger.info(f"Added {duration} seconds to existing table_{table_num}")
                else:
                    entry["tables"][f"table_{table_num}"] = {"total_time": duration}
                    logger.info(f"Initialized table_{table_num} with {duration} seconds")
                break

        if not found:
            new_entry = {
                "date": today,
                "tables": {f"table_{i}": {"total_time": 0} for i in range(1, 8)}
            }
            new_entry["tables"][f"table_{table_num}"]["total_time"] = duration
            current_data["data"].append(new_entry)
            logger.info(f"Added new entry for {today} with table_{table_num}")

        # Faylni saqlash
        with open('data.json', 'w', encoding='utf-8') as file:
            json.dump(current_data, file, ensure_ascii=False, indent=2)
            logger.info(f"data.json file successfully updated for table_{table_num}")
    except Exception as e:
        logger.error(f"Error updating data: {e}")
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
