# 快速开始指南

## 三步部署AI人脸识别服务

### 步骤1: 构建Docker镜像
```bash
cd docker
./build.sh
```

### 步骤2: 启动容器

#### CPU模式（默认）
```bash
./run.sh cpu
```

#### GPU模式
```bash
./run.sh gpu
```

#### NPU模式
```bash
./run.sh npu
```

### 步骤3: 测试服务

查看容器状态：
```bash
docker ps
docker logs -f face-recognition-cpu
```

测试API（使用项目中的测试脚本）：
```bash
cd ..
python test_api.py
```

## 容器自动重启

✅ **已配置自动重启策略** - 容器会在以下情况自动重启：
- Docker守护进程重启后
- 宿主机重启后
- 容器异常退出后

重启策略：`unless-stopped`（除非手动停止，否则总是重启）

## 常用命令

### 查看运行中的容器
```bash
docker ps
```

### 查看容器日志
```bash
docker logs -f face-recognition-cpu
```

### 进入容器调试
```bash
docker exec -it face-recognition-cpu bash
```

### 停止容器
```bash
docker stop face-recognition-cpu
```

### 删除容器
```bash
docker rm face-recognition-cpu
```

### 重启容器
```bash
docker restart face-recognition-cpu
```

## 配置说明

### DEVICE环境变量
- `cpu` - 使用CPU（默认）
- `gpu` - 使用NVIDIA GPU
- `npu` - 使用华为昇腾NPU

### THRESHOLD环境变量
人脸比对阈值，默认1.242，可以根据需要调整：
```bash
docker run -e DEVICE=cpu -e THRESHOLD=1.5 ai-face-recognition-server:1.0
```

## 端口说明

服务默认监听端口：`5002`

容器内端口映射：
```
宿主机端口:容器端口
5002:5002
```

## 数据持久化

默认挂载目录：
- `./logs` - 日志文件
- `./data/uploads` - 上传的图片文件

可以根据需要修改挂载路径：
```bash
docker run -v /your/path/logs:/app/logs ai-face-recognition-server:1.0
```

## 故障排查

1. **容器无法启动**
   ```bash
   docker logs face-recognition-cpu
   ```

2. **端口被占用**
   ```bash
   # 修改端口映射
   docker run -p 5003:5002 ai-face-recognition-server:1.0
   ```

3. **GPU模式失败**
   - 检查nvidia-docker是否安装
   - 检查GPU驱动是否正常
   ```bash
   docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

4. **NPU模式失败**
   - 检查华为CANN驱动是否安装
   - 检查设备文件是否存在
   ```bash
   ls -l /dev/davinci*
   ```

## 更多信息

详细文档请参考：`DOCKER_README.md`
