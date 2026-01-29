#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型管理器
参考 ai-bsocr-serving 项目的模型加载方式
"""

import os
import json


class ModelConfig:
    """
    读取模型config参数
    """
    
    def __init__(self, model_dir):
        self.model_dir = model_dir
        self.config_path = os.path.join(model_dir, "model_config.json")
        # 需要路径处理的配置项（根据当前配置文件）
        self.filekeys = [
            "modelFile",
        ]
    
    def parse_config(self, gpu_m_fraction=0.5):
        """
        解析模型配置
        
        Args:
            gpu_m_fraction: GPU显存比例
            
        Returns:
            dict: 模型配置参数
        """
        if os.path.exists(self.config_path):
            configs = json.load(open(self.config_path, "r", encoding="utf-8-sig"))
            # 处理文件路径
            for key, value in configs.items():
                if key in self.filekeys:
                    configs[key] = os.path.join(self.model_dir, value)
            configs["gpu_m_fraction"] = gpu_m_fraction
            return configs
        else:
            raise Exception(f"model config is not found: {self.config_path}")


class Modelload:
    """
    模型加载器
    """
    
    @staticmethod
    def barcode(model_type, gpu_memory_fraction=0.8):
        """
        加载条形码检测模型
        从配置文件读取 model_type
        
        Args:
            model_type: 模型类型名称（已弃用，从配置文件读取）
            gpu_memory_fraction: GPU显存比例
            
        Returns:
            BarcodeModel: 条形码检测模型实例
        """
        from nets.barcode import BarcodeModel
        
        model_dir = os.path.join("./model", model_type)
        configs = ModelConfig(model_dir).parse_config(gpu_memory_fraction)
        
        # 从配置文件读取 model_type（如果配置文件中有定义）
        model_type = configs.get("model_type", model_type)
        
        conf_threshold = configs.get("confThreshold", 0.5)
        iou_threshold = configs.get("nmsThreshold", 0.7)
        gpu_m_fraction = configs.get("gpu_m_fraction", 0.8)
        model_file = configs.get("modelFile", "model.onnx")
        
        return BarcodeModel(model_file, conf_threshold, iou_threshold, gpu_m_fraction)


class ModelManager:
    """
    模型管理器 - 单例模式
    """
    
    _instance = None
    _registry = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._registry = {}
            self._initialized = True
    
    def register(self, name, loader):
        """
        注册模型加载器
        
        Args:
            name: 模型类型名称
            loader: 加载函数
        """
        self._registry[name] = loader
    
    def get_model(self, model_type, gpu_memory_fraction=0.5):
        """
        获取模型实例
        
        Args:
            model_type: 模型类型名称
            gpu_memory_fraction: GPU显存比例
            
        Returns:
            模型实例
        """
        if model_type in self._registry:
            return self._registry[model_type](model_type, gpu_memory_fraction)
        else:
            raise Exception(f"未注册的模型类型: {model_type}")


# 注册默认的模型加载器
manager = ModelManager()
manager.register("barcode", Modelload.barcode)
