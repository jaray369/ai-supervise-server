import os
import sys
import multiprocessing

# 【关键修复】在导入任何库之前设置 multiprocessing 启动方式
# 同时设置环境变量确保子进程也使用相同配置
os.environ['PYTHONHASHSEED'] = '0'  # 固定哈希种子

# 【NPU 修复】设置 NPU 相关环境变量，避免 TBE 子进程错误
if os.getenv('DEVICE') == 'npu':
    os.environ['TE_PARALLEL_COMPILER'] = '0'  # 禁用并行编译
    os.environ['CPU_CORE_NUM'] = '1'  # 限制 CPU 核心数
    os.environ['OMP_NUM_THREADS'] = '1'  # 限制 OpenMP 线程数
    os.environ['MKL_NUM_THREADS'] = '1'  # 限制 MKL 线程数

try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass

# 添加项目根目录到Python路径
if '__file__' in dir():
    project_dir = os.path.dirname(os.path.abspath(__file__))
else:
    project_dir = os.getcwd()

# 确保项目目录在Python路径中
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from config_loader import get_config

# 读取服务器配置，使用通用的get_config函数
s_configs = get_config('server_config.json')

bind = f"{s_configs['host']}:{s_configs['port']}"
workers = s_configs['workers']
threads = s_configs['threads'] if 'threads' in s_configs else 1
# 【关键修复】使用 sync worker 而不是 gthread，避免多线程与 multiprocessing 冲突
worker_class = 'sync'
loglevel = s_configs['log_level'] if 'log_level' in s_configs else 'info'

proc_name = 'ai-face-recognition-server'
pidfile = './run.pid'
timeout = 360
keepalive = 75

# 禁用预加载，让每个worker独立初始化（避免 fork 导致的 ForkAwareLocal ��接问题）
preload_app = False

# worker 配置
def on_starting(server):
    """主进程启动时记录日志"""
    import logging
    logging.info("Gunicorn 主进程启动中...")

def worker_int(worker):
    """Worker 进程被杀死时调用"""
    pass

def worker_abort(worker):
    """Worker 进程被中止时调用"""
    pass
