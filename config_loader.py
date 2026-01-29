#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件加载模块
用于加载和管理配置参数
"""

import json
import os

# 使用绝对路径，确保在Docker环境中也能正确找到配置文件
def get_config_path():
    """获取配置文件目录（项目根目录）"""
    # 获取当前文件的绝对路径
    current_file = os.path.abspath(__file__)
    # 返回文件所在目录（项目根目录）
    return os.path.dirname(current_file)

config_file = os.path.join(get_config_path(), "conf", "config.json")
server_config_file = os.path.join(get_config_path(), "conf", "server_config.json")

# 默认配置模板
DEFAULT_CONFIG = {
    'threshold': 1.242,
}

def _json_object_hook(d):
    """JSON对象钩子函数，用于设置默认值
    
    遍历DEFAULT_CONFIG，为缺失的配置项设置默认值
    """
    for key, default_value in DEFAULT_CONFIG.items():
        if key not in d:
            d[key] = default_value
    return d

def load_config_json(file_path):
    """加载JSON配置文件，支持UTF-8 BOM格式，并设置默认值"""
    with open(file_path, 'r', encoding='utf-8') as fp:
        file_data = fp.read()
        if ord(file_data[0]) == 65279:  # \uFEFF 处理UTF-8 BOM格式
            file_data = file_data[1:]
        config = json.loads(file_data, object_hook=_json_object_hook)
        return config


class Config:
    """配置类，用于读取和管理配置参数，支持字典式访问"""
    
    def __init__(self, config_file_path=None):
        if config_file_path is None:
            # 如果未指���路径，使用全局变量 config_file
            config_file_path = config_file
        self._config = load_config_json(config_file_path)
    
    def __getitem__(self, key):
        """支持字典式访问: config['key']"""
        return self._config[key]
    
    def __contains__(self, key):
        """支持 'in' 操作符: 'key' in config"""
        return key in self._config


def get_config(config_path=None):
    """通用获取配置实例函数
    Args:
        config_path: 配置文件路径，可以是绝对路径或相对路径
                     如果为None，默认读取config.json
                     也可以是 'server_config.json' 这样的相对路径
    Returns:
        Config实例
    """
    if config_path is None:
        return Config(config_file)
    elif os.path.isabs(config_path):
        # 绝对路径直接使用
        return Config(config_path)
    else:
        # 相对路径，基于配置目录拼接
        full_path = os.path.join(get_config_path(), "conf", config_path)
        return Config(full_path)
