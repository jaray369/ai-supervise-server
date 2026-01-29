# AI Supervise Server API 接口文档

## 目录

- [1. 容器启动与停止](#1-容器启动与停止)
- [2. 接口列表](#2-接口列表)
  - [2.1 人脸比对接口](#21-人脸比对接口)
  - [2.2 条形码检测接口](#22-条形码检测接口)
  - [2.3 条形码解码接口](#23-条形码解码接口)
- [3. 接口调用示例](#3-接口调用示例)

---

## 1. 容器启动与停止

### 1.1 CPU 模式启动

```bash
# 启动容器
docker run -it \
    --name ai-supervise-server \
    --restart unless-stopped \
    -p 5002:5002 \
    -e DEVICE=cpu \
    -v "$(pwd)/logs:/app/logs" \
    -v "$(pwd)/data/uploads:/app/data/uploads" \
    ai-supervise-server:1.0
```

### 1.2 GPU 模式启动

```bash
# 启动容器
docker run -it \
    --name ai-supervise-server \
    --restart unless-stopped \
    -p 5002:5002 \
    --gpus all \
    -e DEVICE=gpu \
    -v "$(pwd)/logs:/app/logs" \
    -v "$(pwd)/data/uploads:/app/data/uploads" \
    ai-supervise-server:1.0
```

### 1.3 NPU 模式启动

```bash
# 启动容器
docker run -it \
    --name ai-supervise-server \
    -p 5002:5002 \
    --device=/dev/davinci0 \
    --device=/dev/davinci_manager \
    --device=/dev/devmm_svm \
    --device=/dev/hisi_hdc \
    -v /usr/local/dcmi:/usr/local/dcmi \
    -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi \
    -v /usr/local/Ascend/:/usr/local/Ascend/ \
    -v /usr/local/sbin/:/usr/local/sbin/ \
    -e DEVICE=npu \
    -v "$(pwd)/logs:/app/logs" \
    -v "$(pwd)/data/uploads:/app/data/uploads" \
    ai-supervise-server:1.0
```

### 1.4 容器管理命令

```bash
# 查看容器状态
docker ps -a | grep ai-supervise-server

# 查看容器日志
docker logs -f ai-supervise-server

# 停止容器
docker stop ai-supervise-server

# 删除容器
docker rm ai-supervise-server

# 重启容器
docker restart ai-supervise-server

# 进入容器
docker exec -it ai-supervise-server /bin/bash
```

### 1.5 启动后验证

服务启动后，可通过以下地址访问：
- 本地：`http://127.0.0.1:5002`
- 局域网：`http://<你的IP>:5002`

---

## 2. 接口列表

### 2.1 人脸比对接口

| 项目 | 说明 |
|------|------|
| **接口地址** | `/face_compare` |
| **请求方法** | `POST` |
| **Content-Type** | `application/json` |

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| image1 | String | 是 | 第一张图片的 Base64 编码 |
| image2 | String | 是 | 第二张图片的 Base64 编码 |

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| is_same_person | Boolean | 是否为同一人 |
| message | String | 返回消息 |

#### 响应示例

```json
{
  "is_same_person": true,
  "message": "ok"
}
```

---

### 2.2 条形码检测接口

| 项目 | 说明 |
|------|------|
| **接口地址** | `/bar_detect` |
| **请求方法** | `POST` |
| **Content-Type** | `application/json` |

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| image | String | 是 | 图片的 Base64 编码，可带 data URI 前缀 |

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | Integer | 状态码：0 成功，-1 失败 |
| message | String | 返回消息 |
| results | Array | 检测结果列表 |

#### results 数组项说明

| 参数名 | 类型 | 说明 |
|--------|------|------|
| label | String | 标签名称（barcode） |
| confidence | Float | 置信度（0-1） |
| bbox | Array | 边界框坐标 [x1, y1, x2, y2] |
| polygons | Array | 多边形顶点列表（4-8个点） |

#### 响应示例

```json
{
  "code": 0,
  "message": "ok",
  "results": [
    {
      "label": "barcode",
      "confidence": 0.95,
      "bbox": [100, 200, 400, 350],
      "polygons": [
        [[100, 200], [400, 200], [400, 350], [100, 350]]
      ]
    }
  ]
}
```

---

### 2.3 条形码解码接口

| 项目 | 说明 |
|------|------|
| **接口地址** | `/bar_decode` |
| **请求方法** | `POST` |
| **Content-Type** | `application/json` |

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| image | String | 是 | 图片的 Base64 编码，可带 data URI 前缀 |

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | Integer | 状态码：0 成功，-1 失败 |
| message | String | 返回消息 |
| results | Array | 解码结果列表 |

#### results 数组项说明

| 参数名 | 类型 | 说明 |
|--------|------|------|
| type | String | 条形码类型（如 QRCODE、CODE128、EAN13 等） |
| data | String | 解码后的条形码数据内容 |
| rect | Object | 条形码在图像中的位置和尺寸 {left, top, width, height} |
| confidence | Float | 检测置信度（0-1） |

#### 响应示例

```json
{
  "code": 0,
  "message": "ok",
  "results": [
    {
      "type": "QRCODE",
      "data": "https://example.com",
      "rect": {"left": 100, "top": 200, "width": 300, "height": 150},
      "confidence": 0.95
    }
  ]
}
```

---

## 3. 接口调用示例

### 3.1 使用 Python 调用

#### 3.1.1 人脸比对

```python
import requests
import base64

def image_to_base64(image_path):
    """将图片转换为base64编码"""
    with open(image_path, 'rb') as f:
        img_data = f.read()
    return base64.b64encode(img_data).decode('utf-8')

# 调用人脸比对接口
url = "http://127.0.0.1:5002/face_compare"

data = {
    'image1': image_to_base64('path/to/image1.jpg'),
    'image2': image_to_base64('path/to/image2.jpg')
}

response = requests.post(url, json=data)
result = response.json()

print(f"是否为同一人: {result['is_same_person']}")
```

#### 3.1.2 条形码检测

```python
import requests
import base64

def image_to_base64(image_path):
    """将图片转换为base64编码"""
    with open(image_path, 'rb') as f:
        img_data = f.read()
    return base64.b64encode(img_data).decode('utf-8')

# 调用条形码检测接口
url = "http://127.0.0.1:5002/bar_detect"

data = {
    'image': f'data:image/jpeg;base64,{image_to_base64("path/to/image.jpg")}'
}

response = requests.post(url, json=data)
result = response.json()

if result['code'] == 0:
    for det in result['results']:
        print(f"检测到 {len(det['polygons'])} 个多边形")
        print(f"置信度: {det['confidence']:.3f}")
        print(f"边界框: {det['bbox']}")
```

#### 3.1.3 条形码解码

```python
import requests
import base64

def image_to_base64(image_path):
    """将图片转换为base64编码"""
    with open(image_path, 'rb') as f:
        img_data = f.read()
    return base64.b64encode(img_data).decode('utf-8')

# 调用条形码解码接口
url = "http://127.0.0.1:5003/bar_decode"

data = {
    'image': f'data:image/jpeg;base64,{image_to_base64("path/to/image.jpg")}'
}

response = requests.post(url, json=data)
result = response.json()

if result['code'] == 0:
    for barcode in result['results']:
        print(f"类型: {barcode['type']}")
        print(f"数据: {barcode['data']}")
        print(f"置信度: {barcode['confidence']:.3f}")
        print(f"位置: {barcode['rect']}")
```


## 4. 常见问题
---

## 1. 日志位置

- **容器内日志：** `/app/logs/server.log`
- **挂载日志：** `${项目目录}/logs/server.log`

**查看日志：**
```bash
# 实时查看日志
tail -f logs/server.log

# 查看最近100行
tail -n 100 logs/server.log
```

---

