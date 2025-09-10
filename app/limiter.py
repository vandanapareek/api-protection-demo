import time
import redis.asyncio as aioredis

LUA_TOKEN_BUCKET = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local capacity = tonumber(ARGV[3])
local tokens_key = key .. ":tokens"
local last_key = key .. ":last"

local tokens = tonumber(redis.call("get", tokens_key) or capacity)
local last = tonumber(redis.call("get", last_key) or 0)
local delta = math.max(0, now - last)
tokens = math.min(capacity, tokens + delta * refill_rate)
if tokens >= 1 then
  tokens = tokens - 1
  redis.call("set", tokens_key, tokens)
  redis.call("set", last_key, now)
  return {1, tokens}
else
  redis.call("set", tokens_key, tokens)
  redis.call("set", last_key, now)
  return {0, tokens}
end
"""


class RedisRateLimiter:
    def __init__(self, redis_url):
        self.redis_url = redis_url
        self.redis = None
        self.script_sha = None

    async def init(self):
        self.redis = await aioredis.from_url(self.redis_url)
        self.script_sha = await self.redis.script_load(LUA_TOKEN_BUCKET)

    async def allow_request(self, key: str, capacity: int, refill_rate: float):
        now = time.time()
        res = await self.redis.evalsha(self.script_sha, 1, key, now, refill_rate, capacity)
        return int(res[0]) == 1, float(res[1])
