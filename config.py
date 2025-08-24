# # config.py
# import os

# MONGODB_URI = os.getenv("MONGO_PUBLIC_URL", "mongodb://mongo:wSUPTtKQyhVoPQaAScUxZoEwKAcoWgKc@gondola.proxy.rlwy.net:40669")





from environs import Env

# Env obyektini yaratamiz
env = Env()
env.read_env()  # .env faylni yuklaydi

# MongoDB sozlamalari
MONGODB_URI = env.str("MONGO_PUBLIC_URL", "mongodb://mongo:wSUPTtKQyhVoPQaAScUxZoEwKAcoWgKc@gondola.proxy.rlwy.net:40669")

# Bot sozlamalari
BOT_TOKEN = env.str("BOT_TOKEN", "")
ALLOWED_USER_IDS = env.list("ALLOWED_USER_IDS", subcast=int, default=[])

# API va boshqa sozlamalar
API_TOKEN = env.str("API_TOKEN", "MY_SECURETY_TOKEN")
NUM_TABLES = env.int("NUM_TABLES", 7)
HOURLY_RATE = env.int("HOURLY_RATE", 35000)