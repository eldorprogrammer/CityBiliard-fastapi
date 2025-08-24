import os

# MONGODB_URI = os.getenv("MONGO_PUBLIC_URL", "mongodb://mongo:wSUPTtKQyhVoPQaAScUxZoEwKAcoWgKc@gondola.proxy.rlwy.net:40669")

MONGODB_URI = "mongodb://mongo:wSUPTtKQyhVoPQaAScUxZoEwKAcoWgKc@gondola.proxy.rlwy.net:40669"  # MongoDB ulanish manzili (o‘z manzilingizga almashtiring)
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Frontend ilovasi manzili (masalan, React yoki boshqa)
    "http://localhost:8000",  # API serveri manzili
    "https://your-production-domain.com",  # Ishlab chiqarish domeni (agar mavjud bo‘lsa)
]