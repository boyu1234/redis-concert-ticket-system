import json
import time

import redis

from redis_config import BUYERS, CHANNEL, QUEUE, STOCK, client


def buy_ticket(user_id, connection=client):
    with connection.pipeline() as pipe:
        for attempt in range(12):
            try:
                pipe.watch(STOCK, BUYERS, QUEUE)
                stock = int(pipe.get(STOCK) or 0)
                if pipe.sismember(BUYERS, user_id):
                    return "duplicate"
                if stock <= 0:
                    return "sold_out"
                if pipe.type(QUEUE) not in ("none", "list"):
                    raise redis.ResponseError("Invalid order queue type")

                order = json.dumps({"user": user_id, "time": str(time.time())})
                pipe.multi()
                pipe.decr(STOCK)
                pipe.sadd(BUYERS, user_id)
                pipe.lpush(QUEUE, order)
                pipe.publish(CHANNEL, stock - 1)
                pipe.execute()
                return "success"
            except redis.WatchError:
                time.sleep(0.002 * (attempt + 1))
        return "busy"


if __name__ == "__main__":
    print(buy_ticket("user_001"))
