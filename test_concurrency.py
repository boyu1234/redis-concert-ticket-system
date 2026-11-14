from concurrent.futures import ThreadPoolExecutor
import os
from uuid import uuid4

import redis

from flash_sale import buy_ticket
from redis_config import BUYERS, QUEUE, STOCK


def run_test():
    # Use a new, dedicated test datastore. Never point this at the demo.
    url = os.environ["TEST_REDIS_URL"]
    with redis.Redis.from_url(url, decode_responses=True) as connection:
        if connection.exists(STOCK, BUYERS, QUEUE):
            raise RuntimeError("Use an empty test database")
        if not connection.set(STOCK, 10, nx=True):
            raise RuntimeError("Test database is already in use")
        try:
            prefix = uuid4().hex
            user = f"{prefix}_0"
            assert buy_ticket(user, connection) == "success"
            assert buy_ticket(user, connection) == "duplicate"
            with ThreadPoolExecutor(max_workers=24) as executor:
                users = (f"{prefix}_{i}" for i in range(1, 100))
                outcomes = list(executor.map(lambda uid: buy_ticket(uid, connection), users))
            assert outcomes.count("success") == 9, outcomes
            assert connection.get(STOCK) == "0"
            assert connection.scard(BUYERS) == connection.llen(QUEUE) == 10
            print("100 unique buyers, 10 tickets sold, 0 remaining, 10 queued; duplicate rejected")
        finally:
            connection.delete(STOCK, BUYERS, QUEUE)


if __name__ == "__main__":
    run_test()
