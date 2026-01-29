#!/bin/bash

# 【关键修复】设置多进程启动方式为 spawn，避免 fork 导致的问题
export MULTIPROCESSING_START_METHOD=spawn
export PYTHONHASHSEED=0

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR" || exit 1

# 服务名称、PID文件和日志文件
SERVICE_NAME="ai-face-recognition-server"
PID_FILE="$PROJECT_DIR/server.pid"
LOG_FILE="$PROJECT_DIR/logs/server.log"
PYTHON_CMD="python3"

# 确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

# 检查服务是否已经运行（通过进程名称查找）
RUNNING_PID=$(ps aux | grep "[a]i-face-recognition-server" | awk '{print $2}')
if [ -n "$RUNNING_PID" ]; then
    echo -e "${YELLOW}⚠ 警告: 服务已经在运行中 (PID: $RUNNING_PID)${NC}"
    echo -e "${YELLOW}如需重启，请先运行 stop.sh 停止服务${NC}"
    exit 1
fi

# 清理旧的PID文件
if [ -f "$PID_FILE" ]; then
    rm -f "$PID_FILE"
fi


# 检查必要文件是否存在
if [ ! -f "$PROJECT_DIR/run_server.py" ]; then
    echo -e "${RED}✗ 错误: 找不到 run_server.py${NC}"
    exit 1
fi

if [ ! -f "$PROJECT_DIR/pygunicorn.py" ]; then
    echo -e "${RED}✗ 错误: 找不到 pygunicorn.py${NC}"
    exit 1
fi

# 启动服务（使用gunicorn）
echo -e "${GREEN}启动 ai-face-recognition-server...${NC}"
# 使用gunicorn启动，进程名称为ai-face-recognition-server
nohup gunicorn -c pygunicorn.py run_server:app > "$LOG_FILE" 2>&1 &
NEW_PID=$!

# 等待服务启动
sleep 2

# 检查服务是否启动成功
if ps -p "$NEW_PID" > /dev/null; then
    echo "$NEW_PID" > "$PID_FILE"
    echo -e "${GREEN}✓ 服务启动成功!${NC}"
    echo -e "  - 主机: 0.0.0.0"
    echo -e "  - 端口: 5002"
    echo -e "  - API接口: http://0.0.0.0:5002/face_compare"
    echo ""
    echo -e "${GREEN}使用以下命令查看日志:${NC}"
    echo -e "  tail -f $LOG_FILE"
    echo ""
    echo -e "${GREEN}使用以下命令停止服务:${NC}"
    echo -e "  ./stop.sh"
else
    echo -e "${RED}✗ 服务启动失败，请查看日志: $LOG_FILE${NC}"
    rm -f "$PID_FILE"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
