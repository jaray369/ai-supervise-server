#!/bin/bash
set -e

echo "=========================================="
echo "AI Face Recognition Server - Docker Entrypoint"
echo "=========================================="

# 显示当前配置
echo "设备配置: ${DEVICE:-cpu} (通过环境变量DEVICE设置)"
echo "阈值配置: ${THRESHOLD:-1.242}"



echo ""
echo "=========================================="
echo "启动Gunicorn服务..."
echo "=========================================="

# 使用gunicorn启动服务，从环境变量获取服务名称
SRV_NAME="${SRV_NAME:-ai-face-recognition-server}"
echo "服务名称: $SRV_NAME"
gunicorn --config=pygunicorn.py -n=$SRV_NAME start:app
