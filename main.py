import json
import csv
import os.path
from mitmproxy import ctx

# 这是我们要保存数据的文件名
CSV_FILENAME = "transactions.csv"

# 用一个集合来存储已经写入CSV的ID，用于去重
SEEN_IDS = set()

# 脚本加载时执行的初始化函数
def load(loader):
    """
    在脚本第一次加载时，读取现有CSV文件并填充SEEN_IDS
    """
    if not os.path.exists(CSV_FILENAME):
        ctx.log.info(f"'{CSV_FILENAME}' 文件不存在，将创建新文件。")
        return

    try:
        with open(CSV_FILENAME, 'r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            # 假设'id'列一定存在
            for row in reader:
                if 'id' in row:
                    SEEN_IDS.add(row['id'])
        ctx.log.info(f"成功加载了 {len(SEEN_IDS)} 个已存在的ID用于去重。")
    except Exception as e:
        ctx.log.error(f"读取CSV文件时出错: {e}")

def response(flow):
    """
    当任何一个网络请求有响应时，这个函数就会被Mitmproxy调用
    """
    if "bingshanshuju.com/transaction_list" in flow.request.url:
        ctx.log.info("捕获到目标请求！")

        data = json.loads(flow.response.text)
        items = data.get("data", {}).get("items", [])
        
        if not items:
            return
            
        new_items_to_write = []
        for item in items:
            item_id = str(item.get("id")) # 将id统一转为字符串处理
            if item_id and item_id not in SEEN_IDS:
                SEEN_IDS.add(item_id)
                new_items_to_write.append(item)

        if not new_items_to_write:
            ctx.log.info("没有新的不重复数据。")
            return
            
        # 动态获取表头，以第一个新数据为准
        headers = list(new_items_to_write[0].keys())
        
        # 检查文件是否存在，如果不存在则写入表头
        file_exists = os.path.exists(CSV_FILENAME)
        
        with open(CSV_FILENAME, 'a', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            if not file_exists:
                writer.writeheader()
            
            writer.writerows(new_items_to_write)
            
        ctx.log.info(f"成功将 {len(new_items_to_write)} 条新数据写入到 {CSV_FILENAME}")