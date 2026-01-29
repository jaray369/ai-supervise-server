#!/bin/bash
# 人脸比对服务停止脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR" || exit 1

# 服务名称和PID文件
SERVICE_NAME="ai-supervise-server"
PID_FILE="$PROJECT_DIR/server.pid"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   人脸比对服务停止脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 通过服务名称查找进程
RUNNING_PIDS=$(ps aux | grep "[a]i-supervise-server" | awk '{print $2}')

# 如果没有找到进程
if [ -z "$RUNNING_PIDS" ]; then
    echo -e "${YELLOW}⚠ 警告: 未找到运行中的 $SERVICE_NAME 服务${NC}"
    
    # 清理PID文件（如果存在）
    if [ -f "$PID_FILE" ]; then
        echo -e "${YELLOW}清理旧的PID文件...${NC}"
        rm -f "$PID_FILE"
    fi
    
    exit 0
fi

echo -e "${GREEN}找到运行中的服务进程: $RUNNING_PIDS${NC}"

# 停止所有找到的进程
for PID in $RUNNING_PIDS; do
    echo -e "${YELLOW}正在停止服务 (PID: $PID)...${NC}"
    
    # 尝试优雅地停止进程
    kill "$PID"
    
    # 等待进程结束
    WAIT_COUNT=0
    MAX_WAIT=10
    while ps -p "$PID" > /dev/null 2>&1 && [ $WAIT_COUNT -lt $MAX_WAIT ]; do
        sleep 1
        WAIT_COUNT=$((WAIT_COUNT + 1))
        echo -n "."
    done
    echo ""
    
    # 检查是否成功停止
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}进程 $PID 未响应，强制终止...${NC}"
        kill -9 "$PID"
        sleep 1
    fi
    
    # 最终检查
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${RED}✗ 错误: 无法停止进程 $PID${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ 进程 $PID 已成功停止${NC}"
    fi
done

# 清理PID文件
if [ -f "$PID_FILE" ]; then
    rm -f "$PID_FILE"
fi

echo -e "${GREEN}✓ 服务已成功停止${NC}"
