FROM repo.hexops.cn/ai-runtime-docker/cuda114-py310-ubuntu:1.2

# 支持构建时传入DEVICE参数（用于NPU环境配置）
ARG DEVICE=gpu
ARG SRV_NAME=""
ENV DEVICE=${DEVICE}
ENV SRV_NAME=${SRV_NAME}

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    ca-certificates \
    libzbar0 \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /var/cache/apt/archives/*

# 设置环境变量，指向系统证书
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

RUN pip install --upgrade pip

# 安装facenet-pytorch（使用--no-cache-dir避免缓存问题）
RUN pip install --no-cache-dir facenet-pytorch==2.6.0

# 复制requirements文件
COPY requirements.txt .

# 安装其他Python依赖
RUN pip install --no-cache-dir opencv-python==4.9.0.* onnxruntime-gpu==1.14.1 pyzbar flask multiprocess waitress gunicorn PyYAML 'Werkzeug<3.0.0'

RUN pip install hexai_backend==1.0.2b27 -i "https://ai-view:AP9g5Ut56hxKHUWXDeGZic871iu@repo.hexops.cn/artifactory/api/pypi/ai-pypi/simple"

# 设置环境变量，指定模型缓存目录
ENV TORCH_HOME=/app/.cache
ENV HOME=/app/.cache

# 创建模型缓存目录
RUN mkdir -p /app/.cache

# 复制模型下载脚本
COPY download_models.py /app/download_models.py

# 预下载 facenet-pytorch 模型（在构建时下载，避免运行时下载）
RUN echo "开始预下载模型..." && \
    python3 /app/download_models.py && \
    echo "模型预下载完成"

# 复制项目文件
COPY . .
# 删除whl文件
RUN find /app -name "*.whl" -type f -delete

# 创建必要的目录
RUN mkdir -p /app/logs /app/data/uploads

# 复制entrypoint脚本
COPY docker/entrypoint.sh /app/entrypoint.sh

# 给entrypoint脚本执行权限
RUN chmod +x /app/entrypoint.sh

# 暴露端口
EXPOSE 5002

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 使用entrypoint脚本启动
ENTRYPOINT []
CMD ["/bin/bash", "/app/entrypoint.sh"]
