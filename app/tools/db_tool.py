import sqlite3
from pydantic import BaseModel,Field
from app.tools.base import BaseTool

#定义继承BaseModel基类做：参数校验类
class DBQueryArgs(BaseModel):
    month: str = Field(description="要查询的月份，格式如‘2023-10")

#定义查询数据库工具类继承BaseTool
class DBQueryTool(BaseTool):
    name: str = "query_sales"
    description: str = "查询某个月的销售额"
    args_schema = DBQueryArgs
    async def run(self,args: DBQueryArgs) -> dict:
        #实际工程用MySQL,这里用SQLite演示
        conn = sqlite3.connect("agentflow.db")
        cursor = conn.cursor()
        cursor.execute("SELECT amount FROM sales WHERE month = ?",(args.month,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return {"error":f"没有找到{args.month}的销售数据"}
        return {"month":args.month,"amount":row[0]}

#实例化查询数据库对象
db_query_tool = DBQueryTool()
