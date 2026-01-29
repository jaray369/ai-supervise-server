#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用facenet-pytorch对两张人脸图片进行比对
主要步骤：
1. 使用MTCNN检测并裁剪人脸
2. 使用InceptionResnetV1提取特征向量
3. 计算两个特征向量的欧氏距离
4. 根据距离判断是否为同一人

支持设备: CPU, GPU (CUDA), NPU (华为昇腾)
"""

import os

# # 【NPU 修复】设置 NPU 相关环境变量，避免 TBE 子进程错误
if os.getenv('DEVICE') == 'npu':
    os.environ['TE_PARALLEL_COMPILER'] = '0'  # 禁用并行编译
    os.environ['CPU_CORE_NUM'] = '1'  # 限制 CPU 核心数
    os.environ['OMP_NUM_THREADS'] = '1'  # 限制 OpenMP 线程数
    os.environ['MKL_NUM_THREADS'] = '1'  # 限制 MKL 线程数

from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image
import torch
import logging
from config_loader import get_config

# 获取logger
logger = logging.getLogger(__name__)
device_type = os.getenv('DEVICE', 'cpu')

class FaceComparator:
    def __init__(self):
        # 从配置文件获取阈值
        config = get_config()
        # 根据环境变量初始化设备
        if device_type == 'npu':
            self.device = self._init_npu_device()
        elif device_type == 'gpu':
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:  # 'cpu' or 其他
            self.device = torch.device('cpu')
        
        self.threshold = config['threshold']
        logger.info(f"使用设备: {self.device} (DEVICE: {device_type})")
        
        # 初始化MTCNN人脸检测
        self.mtcnn = MTCNN(
            image_size=160,      # 输出图像大小
            margin=0,            # 人脸边距
            min_face_size=20,    # 最小人脸尺寸
            thresholds=[0.6, 0.7, 0.7],  # MTCNN三个网络的阈值
            factor=0.709,        # 图像金字塔缩放因子
            post_process=True,
            device=self.device
        )
        # 初始化InceptionResnetV1特征提取
        self.resnet = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
    
    def _init_npu_device(self):
        """初始化华为 NPU 设备"""
        try:
            import torch_npu
            torch.npu.set_compile_mode(jit_compile=False)
            torch_npu.npu.set_device("npu:0")
            return torch.device('npu')
        except Exception as e:
            import logging
            logging.warning(f"NPU 初始化失败，降级到 CPU: {e}")
            return torch.device('cpu')
    
    def extract_face(self, img_path):
        """
        从图片中检测并裁剪人脸
        """
        try:
            img = Image.open(img_path).convert('RGB')
            # 使用MTCNN检测并裁剪人脸
            face = self.mtcnn(img)
            if face is None:
                print(f"警告: 在图片 {img_path} 中未检测到人脸")
                return None
            return face
        except Exception as e:
            print(f"错误: 处理图片 {img_path} 时出错: {str(e)}")
            return None
    
    def extract_embedding(self, face_tensor):
        """
        提取人脸特征向量（512维embedding）
        """
        with torch.no_grad():
            # 添加batch维度并提取特征
            embedding = self.resnet(face_tensor.unsqueeze(0).to(self.device))
        return embedding
    
    def compare(self, img_path1, img_path2):
        """
        比对两张图片中的人脸
        """
        # 1. 检测并裁剪人脸
        face1 = self.extract_face(img_path1)
        face2 = self.extract_face(img_path2)
        if face1 is None or face2 is None:
            print("\n人脸检测失败, 无法进行比对")
            return None, None
        # 2. 提取特征向量
        embedding1 = self.extract_embedding(face1)
        embedding2 = self.extract_embedding(face2)
        print(f"特征向量维度: {embedding1.shape[1]}")
        
        # 3. 计算欧氏距离
        distance = (embedding1 - embedding2).norm().item()
        
        # 判断是否为同一人
        is_same_person = distance < self.threshold
        return distance, is_same_person
