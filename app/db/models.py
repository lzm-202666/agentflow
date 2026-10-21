import uuid
from datetime import datetime
from sqlalchemy import String,Text,JSON,DateTime,Numeric,Integer,Boolean,ForeignKey,func
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column

#定义基类模板
class Base(DeclarativeBase):
    pass
#创建id生成函数
def _uuid() ->str:
    return str(uuid.uuid4())
#创建数据库表模板
class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String(36),primary_key=True,default=_uuid())
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text,nullable=True)
    graph_json: Mapped[JSON] = mapped_column(JSON,default=dict)
    ctreat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())
class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(36),primary_key=True,default=_uuid())
    workflow_id: Mapped[str | None] = mapped_column(String(36),ForeignKey("workflows.id"),nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(64),nullable=True)
    created_id: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())
class Trace(Base):
    __tablename__ = "traces"
    id: Mapped[str] = mapped_column(String(36),primary_key=True,default=_uuid)
    session_id: Mapped[str | None] = mapped_column(String(36),ForeignKey("sessions.id"),nullable=True)
    input: Mapped[str] = mapped_column(Text)
    output: Mapped[str | None] = mapped_column(Text,nullable=True)
    route: Mapped[str | None] = mapped_column(String(32),nullable=True)
    status: Mapped[str] = mapped_column(String(16),default="pending")
    prompt_tokens: Mapped[int] = mapped_column(Integer,default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer,default=0)
    cost_usd: Mapped[float] = mapped_column(Numeric(12,6),default=0)
    latency_ms: Mapped[int] = mapped_column(Integer,default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())
class Toolcall(Base):
    __tablename__ = "tool_calls"
    id: Mapped[str] = mapped_column(String(36),primary_key=True,default=_uuid())
    trace_id: Mapped[str] = mapped_column(String(36),ForeignKey("traces.id"))
    tool_name: Mapped[str] = mapped_column(String(64))
    args: Mapped[dict] = mapped_column(JSON,default=dict)
    result: Mapped[dict | None] = mapped_column(JSON,nullable=True)
    success: Mapped[bool] = mapped_column(Boolean,default=False)
    error: Mapped[str | None] = mapped_column(Text,nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer,default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())
