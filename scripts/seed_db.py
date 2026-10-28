import sqlite3

conn = sqlite3.connect("agentflow.db")
cursor = conn.cursor()

#建个业务表
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT,
    amount REAL
    )
""")
#塞点数据
cursor.execute("DELETE FROM sales") #这里是先执行把表里的数据都清除真正业务数据不用
cursor.executemany(
    "INSERT INTO sales (month,amount) VALUES (?,?)",
    [("2023-09",15000),("2023-10",22000),("2023-11",18000)]
)
conn.commit()
conn.close()
print("Mock data inserted.")