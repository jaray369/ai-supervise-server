#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型预下载脚本
用于在Docker镜像构建时预先下载facenet-pytorch的模型文件
避免容器启动后再下载，加快启动速度
"""

import os
import sys
import torch
from facenet_pytorch import InceptionResnetV1, MTCNN

def main():
    print("=" * 60)
    print("开始下载 facenet-pytorch 模型...")
    print("=" * 60)
    
    # 设置模型缓存目录
    cache_dir = "/app/.cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    # 设置环境变量，确保模型缓存在指定目录
    os.environ['TORCH_HOME'] = cache_dir
    os.environ['HOME'] = cache_dir
    
    print(f"\n模型缓存目录: {cache_dir}")
    print(f"TORCH_HOME: {os.environ.get('TORCH_HOME')}")
    
    device = torch.device('cpu')
    
    try:
        # 1. 下载 InceptionResnetV1 模型 (vggface2 预训练)
        print("\n[1/2] 正在下载 InceptionResnetV1 (vggface2) 模型...")
        print("模型大小约 100MB+，请耐心等待...")
        
        resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)
        print("✓ InceptionResnetV1 模型下载成功")
        
        # 2. 下载 MTCNN 模型（如果需要的话）
        print("\n[2/2] 正在初始化 MTCNN...")
        mtcnn = MTCNN(device=device)
        print("✓ MTCNN 初始化成功")
        
        print("\n" + "=" * 60)
        print("模型下载完成！")
        print("=" * 60)
        
        # 列出下载的模型文件
        print("\n已下载的模型文件:")
        cache_path = os.path.join(cache_dir, "torch", "hub", "checkpoints")
        if os.path.exists(cache_path):
            for file in os.listdir(cache_path):
                file_path = os.path.join(cache_path, file)
                if os.path.isfile(file_path):
                    size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    print(f"  - {file} ({size_mb:.2f} MB)")
        
        print(f"\n模型已缓存到: {cache_path}")
        print("容器启动后将直接使用这些缓存文件，无需重新下载")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ 模型下载失败: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
