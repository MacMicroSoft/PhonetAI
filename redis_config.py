import os
import redis
from dotenv import load_dotenv


load_dotenv()

def create_redis_client():
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", 6379))
    db = int(os.getenv("REDIS_DB", 0))

    return redis.StrictRedis(host=host, port=port, db=db)

redis_client = create_redis_client()
