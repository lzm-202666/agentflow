# --- 阶段 1: 依赖构建 ---
FROM python:3.11-slim AS builder
WORKDIR /build

# 【关键加速 1】把 Debian 系统源换成阿里云，解决 apt-get 龟速
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .

# 【关键加速 2】pip 使用清华源，解决 Python 包龟速
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# --- 阶段 2: 极简运行环境 ---
FROM python:3.11-slim AS runtime
WORKDIR /app

# 【关键加速 3】运行阶段也要换源，解决 libpq5 下载慢
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

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
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]