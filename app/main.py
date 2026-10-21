from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.chat import router as chat_router
from app.db.session import init_db
from app.observability.metrics import metrics_endpoint
from contextlib import asynccontextmanager

#异步上下文管理器一键创建表函数
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

#实例化FastAPI实例对象
app = FastAPI(title=settings.app_name,lifespan=lifespan)


#允许前端网页代码发起请求访问后端接口
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
#注册路由/接口
app.include_router(chat_router,prefix="/api")
app.add_route("/metrics",metrics_endpoint)

@app.get("/health")
async def health():
    return {"status":"ok","app":settings.app_name}