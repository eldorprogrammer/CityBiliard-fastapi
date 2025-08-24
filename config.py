# # config.py
# import os

# MONGODB_URI = os.getenv("MONGO_PUBLIC_URL", "mongodb://mongo:wSUPTtKQyhVoPQaAScUxZoEwKAcoWgKc@gondola.proxy.rlwy.net:40669")



from dotenv import load_dotenv
import os

load_dotenv()  # .env faylni yuklaydi
MONGODB_URI = os.getenv("MONGO_PUBLIC_URL")
API_TOKEN = os.getenv("API_TOKEN")




















