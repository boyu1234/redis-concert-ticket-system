import os

import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
STOCK = "ticket:stock"
BUYERS = "ticket:buyers"
QUEUE = "order:queue"
CHANNEL = "ticket:broadcast"
client = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=3)
