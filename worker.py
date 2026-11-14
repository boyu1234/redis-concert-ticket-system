import redis
import json
import time

# 建立 Redis 連線 (這支程式自己獨立連線)
from redis_config import QUEUE, client as r
order_queue = QUEUE

def process_order(order_data_str):
    """模擬處理單筆訂單的繁重工作"""
    try:
        # 將 Redis 取出的字串轉回 JSON 格式 (字典)
        order = json.loads(order_data_str)
        user_id = order.get("user")
        
        print(f"📦 收到新訂單，準備處理 - User: {user_id}")
        
        # 1. 模擬寫入關聯式資料庫 (SQL) 需要時間
        print("   ⏳ 正在寫入關聯式資料庫...")
        time.sleep(1) # 故意延遲 1 秒
        
        # 2. 模擬呼叫第三方支付 API
        print("   💳 正在產生結帳連結...")
        time.sleep(0.5) 
        
        # 3. 模擬寄送 Email
        print(f"   📧 正在發送【搶購成功確認信】至 {user_id}@example.com...")
        time.sleep(0.5)
        
        print(f"✅ 訂單處理完畢：{user_id}\n" + "-"*30)
        
    except json.JSONDecodeError:
        print("❌ 訂單資料格式錯誤，無法解析 JSON")
    except Exception as e:
        print(f"❌ 處理訂單時發生錯誤: {str(e)}")

print("🚀 背景訂單處理系統啟動中...")
print("📡 正在監聽 Redis 佇列: order:queue")
print("=" * 40)

# 使用無窮迴圈讓 Worker 持續運行
while True:
    try:
        # 【進階功能2：Queue】使用 BRPOP 阻塞式取出
        # 這個指令會一直卡在這裡等，直到 Queue 裡面有資料才會繼續往下執行
        # timeout=0 代表無限等待
        result = r.brpop(order_queue, timeout=0)
        
        # result 是一個 Tuple，格式為 (key_name, value)
        # 例如: ('order:queue', '{"user": "U_1234", "time": "..."}')
        queue_name, order_data_str = result
        
        # 處理取出的訂單資料
        process_order(order_data_str)
        
    except KeyboardInterrupt:
        print("\n🛑 系統手動關閉。")
        break
    except redis.ConnectionError:
        print("\n⚠️ 無法連線至 Redis 伺服器，3 秒後重試...")
        time.sleep(3)
