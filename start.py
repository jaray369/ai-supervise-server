#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from config_loader import get_config

# 读取服务器配置
s_configs = get_config('server_config.json')

# 设置GPU相关环境变量（如果需要）
if 'gpu_ids' in s_configs:
    os.environ['CUDA_VISIBLE_DEVICES'] = s_configs['gpu_ids']

from run_server import app
from waitress import serve

# 如果不是直接运行，则将日志输出到 gunicorn 中
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

if __name__ == "__main__":
    # 启动 web 服务
    print("* Starting web service...")
    logging.info("* Starting web service...")
    serve(app, host='0.0.0.0', port=5002, threads=1)
