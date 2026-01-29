#!/bin/bash

echo "=========================================="
echo "构建AI Face Recognition Server Docker镜像"
echo "=========================================="

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo "项目目录: $PROJECT_DIR"
echo "Docker目录: $SCRIPT_DIR"

# 进入项目根目录
cd "$PROJECT_DIR"

# 解析命令行参数
BUILD_TYPE="gpu"
PLATFORM=""
DOCKERFILE="docker/Dockerfile"

while [[ $# -gt 0 ]]; do
    case $1 in
        --npu)
            BUILD_TYPE="npu"
            PLATFORM="--platform linux/arm64"
            DOCKERFILE="docker/Dockerfile.aarch64"
            shift
            ;;
        --gpu)
            BUILD_TYPE="gpu"
            PLATFORM=""
            DOCKERFILE="docker/Dockerfile"
            shift
            ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 [--gpu|--npu]"
            echo "  --gpu: 构建GPU版本（默认）"
            echo "  --npu: 构建NPU版本（ARM64架构）"
            exit 1
            ;;
    esac
done

echo "构建类型: $BUILD_TYPE"
echo "使用Dockerfile: $DOCKERFILE"

if [ "$BUILD_TYPE" = "npu" ]; then
    echo "目标平台: linux/arm64 (NPU/aarch64环境)"
    # NPU环境默认使用NPU，可以配置使用CPU
    BUILD_ARGS="--build-arg DEVICE=npu"
    echo "NPU打包配置: DEVICE=npu (可配置为cpu)"
else
    echo "目标平台: 默认平台 (GPU环境)"
    BUILD_ARGS="--build-arg DEVICE=gpu"
    echo "GPU打包配置: DEVICE=gpu"
fi

# 构建镜像（指定Dockerfile路径，传递DEVICE参数）
docker build $PLATFORM $BUILD_ARGS -f $DOCKERFILE -t ai-supervise-server:1.0 .

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ 镜像构建成功！"
    echo "镜像名称: ai-supervise-server:1.0"
    echo "构建类型: $BUILD_TYPE"
    echo "=========================================="
    echo ""
    echo "使用示例:"
    echo "  # CPU模式"
    echo "  docker run -d -p 5002:5002 -e DEVICE=cpu ai-supervise-server:1.0"
    echo ""
    echo "  # GPU模式"
    echo "  docker run -d -p 5002:5002 --gpus all -e DEVICE=gpu ai-supervise-server:1.0"
    echo ""
    echo "  # NPU模式"
    echo "  docker run -d -p 5002:5002 --device=/dev/davinci0 -e DEVICE=npu ai-supervise-server:1.0"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "✗ 镜像构建失败！"
    echo "=========================================="
    exit 1
fi
