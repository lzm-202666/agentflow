import sqlite3
import os

# 自动定位到项目根目录的数据库
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agentflow.db"))

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT input, output, route, prompt_tokens, completion_tokens, latency_ms FROM traces")
rows = cursor.fetchall()
conn.close()

print("----- 历史 Trace 记录 -----")
if not rows:
    print("❌ 数据库里还没有记录，请先去 Swagger 发一次请求！")
else:
    for row in rows:
        print(f"输入: {row[0]}")
        print(f"输出: {row[1]}")
        print(f"路由: {row[2]}")
        print(f"Tokens: 输入({row[3]}) / 输出({row[4]})")
        print(f"延迟: {row[5]} ms")
        print("-" * 20)