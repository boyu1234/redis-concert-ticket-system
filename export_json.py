import json
from pathlib import Path

from redis_config import BUYERS, QUEUE, STOCK, client


def export_to_json():
    data = {
        STOCK: client.get(STOCK),
        BUYERS: sorted(client.smembers(BUYERS)),
        QUEUE: client.lrange(QUEUE, 0, -1),
    }
    Path("redis_data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    export_to_json()
