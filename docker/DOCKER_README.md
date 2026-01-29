# Docker部署指南

本指南说明如何使用Docker容器化部署AI人脸识别服务，支持在启动时配置device参数。

## 目录结构

```
docker/
├── Dockerfile          # Docker镜像构建文件
├── entrypoint.sh       # 容器启动脚本
├── build.sh           # 镜像构建脚本
├── .dockerignore      # Docker构建忽略文件
└── DOCKER_README.md   # 本文档
```

## 快速开始

### 1. 构建Docker镜像

```bash
cd docker
chmod +x build.sh
./build.sh
```

构建成功后，会生成名为 `ai-face-recognition-server:1.0` 的镜像。

### 2. 运行容器

#### CPU模式（默认）
```bash
docker run -d \
  --name face-recognition-cpu \
  -p 5002:5002 \
  -e DEVICE=cpu \
  ai-face-recognition-server:1.0
```

#### GPU模式（需要nvidia-docker支持）
```bash
docker run -d \
  --name face-recognition-gpu \
  -p 5002:5002 \
  --gpus all \
  -e DEVICE=gpu \
  ai-face-recognition-server:1.0
```

#### NPU模式（华为昇腾，需要NPU驱动）
```bash
docker run -d \
  --name face-recognition-npu \
  -p 5002:5002 \
  --device=/dev/davinci0 \
  --device=/dev/davinci_manager \
  --device=/dev/devmm_svm \
  -v /usr/local/Ascend/driver:/usr/local/Ascend/driver \
  -v /usr/local/bin/hccn_tool:/usr/local/bin/hccn_tool \
  -e DEVICE=npu \
  ai-face-recognition-server:1.0
```

## 环境变量配置

### DEVICE（必需/可选）
指定运行设备类型：
- `cpu` - 使用CPU（默认）
- `gpu` - 使用NVIDIA GPU
- `npu` - 使用华为昇腾NPU

```bash
docker run -e DEVICE=gpu ai-face-recognition-server:1.0
```

### THRESHOLD（可选）
人脸比对阈值，默认值为 `1.242`

```bash
docker run -e DEVICE=cpu -e THRESHOLD=1.5 ai-face-recognition-server:1.0
```

## 数据持久化

### 挂载日志目录
```bash
docker run -d \
  -p 5002:5002 \
  -e DEVICE=cpu \
  -v /path/to/logs:/app/logs \
  ai-face-recognition-server:1.0
```

### 挂载上传文件目录
```bash
docker run -d \
  -p 5002:5002 \
  -e DEVICE=cpu \
  -v /path/to/uploads:/app/data/uploads \
  ai-face-recognition-server:1.0
```

### 挂载配置文件
```bash
docker run -d \
  -p 5002:5002 \
  -v /path/to/config.json:/app/conf/config.json \
  ai-face-recognition-server:1.0
```

## 验证服务

### 检查容器状态
```bash
docker ps
docker logs face-recognition-cpu
```

### 测试API
```bash
curl -X POST http://localhost:5002/face_compare \
  -H "Content-Type: application/json" \
  -d '{
    "image1": "data:image/jpeg;base64,...",
    "image2": "data:image/jpeg;base64,..."
  }'
```

## 常见问题

### 1. GPU模式运行失败
确保已安装nvidia-docker：
```bash
# 检查nvidia-docker
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### 2. NPU模式运行失败
确保宿主机已安装华为CANN驱动，并正确挂载设备文件。

### 3. 查看容器日志
```bash
# 实时查看日志
docker logs -f face-recognition-cpu

# 查看最近100行日志
docker logs --tail 100 face-recognition-cpu
```

### 4. 进入容器调试
```bash
docker exec -it face-recognition-cpu bash
```

### 5. 停止和删除容器
```bash
# 停止容器
docker stop face-recognition-cpu

# 删除容器
docker rm face-recognition-cpu

# 删除镜像
docker rmi ai-face-recognition-server:1.0
```

## 性能优化建议

### CPU模式
- 限制容器CPU资源：
  ```bash
  docker run -d --cpus="2.0" -e DEVICE=cpu ai-face-recognition-server:1.0
  ```

### GPU模式
- 指定GPU设备：
  ```bash
  docker run -d --gpus '"device=0"' -e DEVICE=gpu ai-face-recognition-server:1.0
  ```
- 设置GPU内存限制：
  ```bash
  docker run -d --gpus all --shm-size=1g -e DEVICE=gpu ai-face-recognition-server:1.0
  ```

### 内存限制
```bash
docker run -d -m="2g" -e DEVICE=cpu ai-face-recognition-server:1.0
```

## 技术支持

如有问题，请检查：
1. Docker日志：`docker logs <container_name>`
2. 配置文件：确保配置文件格式正确
3. 依赖安装：确保所有Python包正确安装
4. 设备驱动：确保GPU/NPU驱动正确安装
