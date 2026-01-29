#!/bin/bash

# AI Face Recognition Server - Docker运行脚本

set -e

DEVICE=${1:-cpu}
SRV_NAME="ai-supervise-server"

echo "=========================================="
echo "启动AI Supervise Server"
echo "=========================================="
echo "设备模式: $DEVICE"
echo "容器名称: $SRV_NAME"
echo ""

# 检查是否已有同名容器在运行
if docker ps -a --format '{{.Names}}' | grep -q "^${SRV_NAME}$"; then
    echo "警告: 容器 $SRV_NAME 已存在"
    read -p "是否删除并重新创建? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker stop $SRV_NAME 2>/dev/null || true
        docker rm $SRV_NAME 2>/dev/null || true
        echo "旧容器已删除"
    else
        echo "取消操作"
        exit 0
    fi
fi

# 根据设备类型选择运行参数
case $DEVICE in
    cpu)
        echo "启动CPU模式..."
        docker run -it --entrypoint=/bin/bash\
            --name $SRV_NAME \
            --restart unless-stopped \
            -p 5002:5002 \
            -e DEVICE=cpu \
            -v "$(pwd):/code" \
            -v "$(pwd)/../logs:/app/logs" \
            -v "$(pwd)/../data/uploads:/app/data/uploads" \
            ai-supervise-server:1.0
        ;;
    gpu)
        echo "启动GPU模式..."
        docker run -it \
            -e REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
            -e SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
            --name $SRV_NAME \
            --restart unless-stopped \
            -p 5002:5002 \
            --gpus all \
            -e DEVICE=gpu \
            -v "$(pwd)/../logs:/app/logs" \
            -v "$(pwd)/../data/uploads:/app/data/uploads" \
            ai-supervise-server:1.0
        ;;
    gpu_test)
        echo "启动GPU模式..."
        docker run -it --entrypoint=/bin/bash\
            -e REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
            -e SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
            --name $SRV_NAME \
            --restart unless-stopped \
            -p 5002:5002 \
            --gpus all \
            -e DEVICE=gpu \
            -v "$(pwd):/code" \
            -v "$(pwd)/../logs:/app/logs" \
            -v "$(pwd)/../data/uploads:/app/data/uploads" \
            ai-supervise-server:1.0
        ;;
    npu)
        echo "启动NPU模式..."
        docker run -it \
            --name $SRV_NAME \
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
            -v "$(pwd)/../logs:/app/logs" \
            -v "$(pwd)/../data/uploads:/app/data/uploads" \
            ai-supervise-server:1.0
        ;;
    npu_test)
        echo "启动NPU模式..."
        docker run -it --entrypoint=/bin/bash \
            --name $SRV_NAME \
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
            -v "$(pwd):/code" \
            -v "$(pwd)/../logs:/app/logs" \
            -v "$(pwd)/../data/uploads:/app/data/uploads" \
            ai-supervise-server:1.0
        ;;
    *)
        echo "错误: 不支持的设备类型 '$DEVICE'"
        echo "支持的设备: cpu, gpu, npu"
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ 容器启动成功！"
    echo "=========================================="
    echo ""
    echo "容器名称: $SRV_NAME"
    echo "服务端口: 5002"
    echo ""
    echo "查看日志:"
    echo "  docker logs -f $SRV_NAME"
    echo ""
    echo "停止容器:"
    echo "  docker stop $SRV_NAME"
    echo ""
    echo "删除容器:"
    echo "  docker rm $SRV_NAME"
    echo ""
else
    echo ""
    echo "✗ 容器启动失败！"
    exit 1
fi
