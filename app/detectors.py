import redis.asyncio as aioredis
import time


class BehavioralDetector:
    def __init__(self, redis_url):
        self.redis_url = redis_url
        self.redis = None

    async def init(self):
        self.redis = await aioredis.from_url(self.redis_url)

    async def record_and_check(self, ip: str, endpoint: str, window_seconds=30, max_distinct=10):
        """
        Record endpoint access and check distinct endpoints within window.
        """
        key = f"ip_endpoints:{ip}"
        now = int(time.time())
        member = endpoint + ":" + str(now)
        await self.redis.zadd(key, {member: now})
        await self.redis.zremrangebyscore(key, 0, now - window_seconds)
        count = await self.redis.zcard(key)
        if count > max_distinct:
            return True
        return False
