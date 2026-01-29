# 日志系统说明

## 日志位置
- **日志文件**: `logs/server.log`
- **日志格式**: `YYYY-MM-DD HH:MM:SS - logger_name - LEVEL - message`

## 查看日志的方法

### 1. 实时查看日志（推荐）
```bash
tail -f logs/server.log
```

### 2. 查看最后100行日志
```bash
tail -n 100 logs/server.log
```

### 3. 查看全部日志
```bash
cat logs/server.log
```

### 4. 搜索特定关键词
```bash
grep "关键词" logs/server.log
```

### 5. 查看ERROR级别日志
```bash
grep "ERROR" logs/server.log
```

### 6. 查看最近的日志轮转文件
```bash
ls -lh logs/
```

## 日志配置说明

### 日志级别
- **INFO**: 常规信息（服务启动、请求处理等）
- **WARNING**: 警告信息（不影响服务运行的问题）
- **ERROR**: 错误信息（服务处理过程中的错误）

### 日志轮转
- 单个日志文件最大大小: **10MB**
- 保留的备份文件数量: **5个**
- 备份文件命名: `server.log.1`, `server.log.2`, 等

### 日志输出位置
1. **文件输出**: `logs/server.log`
2. **控制台输出**: 通过 `nohup` 重定向到 `logs/server.log`

## 常见日志信息

### 服务启动
```
YYYY-MM-DD HH:MM:SS - root - INFO - * Starting web service...
 * Running on http://0.0.0.0:5002
```

### API请求
```
YYYY-MM-DD HH:MM:SS - root - INFO - Call /face_compare
```

### 人脸比对
```
YYYY-MM-DD HH:MM:SS - root - INFO - 保存base64图片: /path/to/image1.jpg, /path/to/image2.jpg
YYYY-MM-DD HH:MM:SS - root - INFO - 开始比对人脸: /path/to/image1.jpg vs /path/to/image2.jpg
YYYY-MM-DD HH:MM:SS - root - INFO - 比对完成: distance=0.123, is_same_person=True
```

### 错误信息
```
YYYY-MM-DD HH:MM:SS - root - ERROR - 图片格式错误: xxx
YYYY-MM-DD HH:MM:SS - root - ERROR - 服务器错误: xxx
```

## 服务管理

### 启动服务
```bash
./start.sh
```

### 停止服务
```bash
./stop.sh
```

### 查看服务状态
```bash
ps aux | grep "[a]i-face-recognition-server"
```

### 查看服务日志
```bash
tail -f logs/server.log
```
