import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# ==========================================
# 【补丁】修复 aiosqlite 0.22.0 带来的破坏性更改
# 官方 Issue #6583 推荐方案
# ==========================================
if not hasattr(aiosqlite.Connection, "is_alive"):
    def _is_alive_patch(self):
        return True  # 永远认为是活着的


    aiosqlite.Connection.is_alive = _is_alive_patch

# ==========================================
# 正常实例化
# ==========================================

# 注意：这个 saver 是一个 context manager，我们在 FastAPI 的 lifespan 里启动它
checkpointer_cm = AsyncSqliteSaver.from_conn_string("checkpoints.db")
