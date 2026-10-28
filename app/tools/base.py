import time
from pydantic import BaseModel
from typing import Type
from app.config import settings

#定义工具类
class BaseTool:
    name: str = ""
    description: str = ""
    args_schema: Type[BaseModel] = None

    async def run(self,args: BaseModel) -> dict:
        raise NotImplementedError
    async def execute(self,raw_args: dict) ->dict:
        """
        统一的执行入口，自带参数校验和耗时统计
        :param raw_args:
        :return:
        """
        start=time.time()
        try:
            #pydantic严格校验返回BaseModel类或子类的实例对象，校验好的实例对象
            validated_args = self.args_schema(**raw_args)
            #执行真实逻辑
            result = await self.run(validated_args)
            return {
                "success":True,
                "data":result,
                "latency_ms":int((time.time()-start) * 1000),
            }
        except Exception as e:
            return {
                "success":False,
                "data":result,
                "latency_ms":int((time.time()-start) * 1000)
            }