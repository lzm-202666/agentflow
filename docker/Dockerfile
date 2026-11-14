# --- 阶段 1: 依赖构建 ---
FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# --- 阶段 2: 极简运行环境 ---
FROM python:3.11-slim AS runtime
WORKDIR /app

# 设置时区为上海
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装 libpq（Postgres 运行时依赖）
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*

# 安全：创建非 root 用户运行
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# 拷贝虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 拷贝项目代码
COPY . .
RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000
# 注意：这是后端 API 容器的默认启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]