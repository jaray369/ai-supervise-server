# AI Face Recognition Server 改造总结

## 改造内容

参考 `/data/cjl/ai-bsocr-serving` 项目，对 `ai-face-recognition-server` 进行了以下改造：

### 1. DEVICE 配置改为环境变量方式 ✓

**改动文件：**
- `config_loader.py` - 移除了device的默认配置
- `conf/config.json` - 移除了device配置项
- `face_compare.py` - 改为从 `os.getenv('DEVICE', 'cpu')` 获取设备类型

**说明：**
- DEVICE配置不再从配置文件读取
- ���为从环境变量读取，默认值为 'cpu'
- 支持 'cpu', 'gpu', 'npu' 三种模式

### 2. 服务启动使用 Gunicorn 并指定进程名称 ✓

**改动文件：**
- `pygunicorn.py` - 新建Gunicorn配置文件
  - 进程名称：`ai-face-recognition-server`
  - 配置读取：从 `conf/server_config.json` 读取配置
- `start.sh` - 改为使用gunicorn启动
- `docker/entrypoint.sh` - 改为使用gunicorn启动
- `requirements.txt` - 添加了gunicorn依赖
- `run_server.py` - 支持懒加载FaceComparator（避免在导入时加载模型）

**说明：**
- 使用Gunicorn替代Flask内置服务器
- 进程名称固定为 `ai-face-recognition-server`
- 支持多worker和多线程配置

### 3. 合并GPU和NPU的build.sh为一个 ✓

**改动文件：**
- `docker/build.sh` - 合并了原来的 `build.sh` 和 `build_npu.sh`

**参数说明：**
- `--gpu` (默认) - 构建GPU版本，使用 `docker/Dockerfile`
- `--npu` - 构建NPU版本（ARM64架构），使用 `docker/Dockerfile.aarch64`

**使用示例：**
```bash
# 构建GPU版本（默认）
docker/build.sh
docker/build.sh --gpu

# 构建NPU版本（ARM64）
docker/build.sh --npu
```

### 4. NPU打包配置 ✓

**改动说明：**
- NPU环境默认使用NPU设备（可通过环境变量配置为CPU）
- 通过 `--build-arg DEVICE=npu` 传递给Dockerfile
- Dockerfile支持 `ARG DEVICE` 参数

**文件：**
- `docker/build.sh` - NPU构建时传递 DEVICE=npu
- `docker/Dockerfile` - 添加 ARG DEVICE 支持

### 5. 多线程配置 ✓

**配置文件：** `conf/server_config.json`

**配置项：**
```json
{
  "host": "0.0.0.0",
  "port": 5002,
  "workers": 1,      // worker进程数
  "threads": 1,      // 每个worker的线程数
  "log_level": "INFO"
}
```

**Docker运行时配置多线程：**

方法1 - 修改配置文件后重新构建镜像：
```bash
# 修改 conf/server_config.json 中的 workers 和 threads
# 然后重新构建镜像
docker/build.sh --gpu
```

方法2 - 运行时挂载配置文件：
```bash
# 创建自定义配置
cat > custom_server_config.json << EOF
{
  "host": "0.0.0.0",
  "port": 5002,
  "workers": 4,
  "threads": 2,
  "log_level": "INFO"
}
EOF

# 运行时挂载配置文件
docker run -d -p 5002:5002 \
  -v $(pwd)/custom_server_config.json:/app/conf/server_config.json \
  -e DEVICE=gpu \
  ai-face-recognition-server:1.0
```

方法3 - Dockerfile中通过ARG传递配置：
```bash
# 修改 docker/build.sh，添加配置参数
docker build --build-arg WORKERS=4 --build-arg THREADS=2 ...
```

## 配置文件说明

### conf/config.json
只包含应用配置（threshold等），不包含device配置：
```json
{
  "threshold": 1.242
}
```

### conf/server_config.json
包含服务器配置（host, port, workers, threads等）：
```json
{
  "host": "0.0.0.0",
  "port": 5002,
  "debug": false,
  "workers": 1,
  "threads": 1,
  "log_level": "INFO"
}
```

## 环境变量说明

### DEVICE
指定运行设备类型：
- `cpu` - 使用CPU
- `gpu` - 使用GPU (CUDA)
- `npu` - 使用华为昇腾NPU

**示例：**
```bash
# Docker运行
docker run -d -p 5002:5002 -e DEVICE=cpu ai-face-recognition-server:1.0
docker run -d -p 5002:5002 --gpus all -e DEVICE=gpu ai-face-recognition-server:1.0
docker run -d -p 5002:5002 --device=/dev/davinci0 -e DEVICE=npu ai-face-recognition-server:1.0

# 本地运行
export DEVICE=gpu
./start.sh
```

## 改动文件清单

### 已修改的文件：
1. `config_loader.py` - 移除device默认配置
2. `conf/config.json` - 移除device配置项
3. `conf/server_config.json` - 添加threads配置
4. `face_compare.py` - 使用os.getenv读取DEVICE
5. `run_server.py` - 支持懒加载
6. `start.sh` - 使用gunicorn启动
7. `docker/entrypoint.sh` - 使用gunicorn启动，不再修改config.json
8. `docker/build.sh` - 合并GPU和NPU构建，支持DEVICE参数
9. `docker/Dockerfile` - 支持ARG DEVICE参数
10. `requirements.txt` - 添加gunicorn

### 新增的文件：
1. `pygunicorn.py` - Gunicorn配置文件
2. `CHANGES_SUMMARY.md` - 本文档

## 测试验证

所有改动已完成并检查：
- ✓ config_loader.py - 移除device默认配置
- ✓ conf/config.json - 移除device配置项
- ✓ conf/server_config.json - 添加threads配置
- ✓ face_compare.py - 使用os.getenv读取DEVICE
- ✓ pygunicorn.py - Gunicorn配置文件，支持workers和threads
- ✓ run_server.py - 支持懒加载
- ✓ start.sh - 使用gunicorn启动
- ✓ docker/entrypoint.sh - 使用gunicorn启动
- ✓ requirements.txt - 添加gunicorn
- ✓ docker/build.sh - 合并GPU和NPU构建
- ✓ docker/Dockerfile - 支持DEVICE参数
