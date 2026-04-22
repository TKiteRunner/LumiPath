FROM docker.m.daocloud.io/library/python:3.12-slim

# 构建时代理（可选，解决 Docker 内 DNS 被 VPN/Clash Fake-IP 拦截问题）
# 用法: docker compose build --build-arg HTTP_PROXY=http://host.docker.internal:7890
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG http_proxy=${HTTP_PROXY}
ARG https_proxy=${HTTPS_PROXY}

# PyPI 镜像源（HTTP 避免 SSL EOF 问题，可通过 build-arg 覆盖）
ARG PIP_INDEX=http://mirrors.aliyun.com/pypi/simple/
ARG PIP_TRUSTED_HOST=mirrors.aliyun.com

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    http_proxy=${HTTP_PROXY} \
    https_proxy=${HTTPS_PROXY}

WORKDIR /app

# 切换 apt 为阿里云镜像源（兼容新旧两种 sources 格式）
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's|http://deb.debian.org|https://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources; \
    else \
        sed -i 's|http://deb.debian.org|https://mirrors.aliyun.com|g' /etc/apt/sources.list; \
    fi

# System deps: gcc + libpq for asyncpg/psycopg native builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps from pyproject.toml（阿里云 PyPI 镜像）
COPY pyproject.toml .
RUN pip install hatchling -i ${PIP_INDEX} --trusted-host ${PIP_TRUSTED_HOST} && \
    pip install -e . -i ${PIP_INDEX} --trusted-host ${PIP_TRUSTED_HOST}

# Copy application source
COPY . .

EXPOSE 8000
