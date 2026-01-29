#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 NPU 是否正常工作"""

import os
os.environ['DEVICE'] = 'npu'

# 预加载 torch_npu
try:
    import torch_npu
    print(f"✓ torch_npu 加载成功，版本: {torch_npu.__version__ if hasattr(torch_npu, '__version__') else 'unknown'}")
except ImportError as e:
    print(f"✗ torch_npu 导入失败: {e}")
    exit(1)

import torch
print(f"✓ torch 版本: {torch.__version__}")
print(f"✓ has npu attr: {hasattr(torch, 'npu')}")

if hasattr(torch, 'npu'):
    print(f"✓ NPU 可用: {torch.npu.is_available()}")
    if torch.npu.is_available():
        print(f"✓ NPU 设备名: {torch.npu.get_device_name(0)}")
        
        # 测试创建 tensor
        x = torch.randn(3, 3).npu()
        print(f"✓ NPU tensor 创建成功: {x.device}")
        
        # 测试 facenet_pytorch
        from facenet_pytorch import MTCNN
        device = torch.device('npu:0')
        print(f"✓ 创建 MTCNN 设备: {device}")
        mtcnn = MTCNN(device=device)
        print("✓ MTCNN 初始化成功!")
else:
    print("✗ NPU 不可用")
    exit(1)

print("\n✓ 所有测试通过!")
