import os, logging
try:
    import redis
except:
    redis = None

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self, host=None, port=None, db=0):
        host = host or os.getenv("REDIS_HOST", "localhost")
        port = int(port or os.getenv("REDIS_PORT", 6379))

        if redis is None:
            logger.warning("redis package not available; using in-memory cache")
            self._store = {}
            self._client = None
            return

        try:
            self._client = redis.Redis(host=host, port=port, db=db)
            self._client.ping()
        except:
            logger.warning("Failed to connect to Redis; using in-memory cache")
            self._store = {}
            self._client = None

    def set(self, key, value, ex=None):
        if self._client:
            return self._client.set(key, value, ex=ex)
        self._store[key] = value
        return True

    def get(self, key):
        if self._client:
            return self._client.get(key)
        return self._store.get(key)

    def delete(self, key):
        if self._client:
            return self._client.delete(key)
        self._store.pop(key, None)
        return True