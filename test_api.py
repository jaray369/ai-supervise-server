#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API接口测试脚本
测试face_compare和bar_detect接口
"""

import requests
import base64
import os
import json

REST_API_URL = "http://127.0.0.1:5002/face_compare"
BAR_API_URL = "http://127.0.0.1:5002/bar_detect"
DEBAR_API_URL = "http://127.0.0.1:5002/bar_decode"

def image_to_base64(image_path):
    """将图片转换为base64编码"""
    try:
        with open(image_path, 'rb') as f:
            img_data = f.read()
        return base64.b64encode(img_data).decode('utf-8')
    except Exception as e:
        print(f"读取图片失败: {e}")
        return None

def get_test_images(test_dir):
    """
    批量获取测试图片
    
    Args:
        test_dir: 测试图片目录
        
    Returns:
        list: 测试图片路径列表
    """
    # 检查目录是否存在
    if not os.path.exists(test_dir):
        print(f"测试目录不存在: {test_dir}")
        return []
    
    # 获取所有测试图片
    test_images = []
    for filename in sorted(os.listdir(test_dir)):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            test_images.append(os.path.join(test_dir, filename))
    
    if not test_images:
        print(f"在 {test_dir} 目录下没有找到测试图片")
    
    return test_images

def test_face_compare():
    """测试人脸比对接口"""
    print("\n" + "="*50)
    print("测试人脸比对接口")
    print("="*50)
    
    # 测试图片路径
    img1_path = "data/1230.png"
    img2_path = "data/12301.png"

    img1_data = image_to_base64(img1_path)
    img2_data = image_to_base64(img2_path)
    
    if img1_data is not None and img2_data is not None:
        data = {'image1': img1_data, 'image2': img2_data}
        
        try:
            r = requests.post(REST_API_URL, json=data)
            result = r.json()
            print(f"状态码: {r.status_code}")
            print(f"结果: {result}")
        except Exception as e:
            print(f"请求失败: {e}")

def test_barcode_decode():
    """
    测试条形码解码接口
    使用 data/bar_test 目录下的测试图片
    """
    print("\n" + "="*50)
    print("测试条形码解码接口")
    print("="*50)
    
    # 测试图片目录
    test_dir = "data/bar_test"
    
    # 批量获取测试图片
    test_images = get_test_images(test_dir)
    
    if not test_images:
        return
    
    print(f"找到 {len(test_images)} 张测试图片")
    
    # 遍历测试每张图片
    for img_path in test_images:
        print(f"\n{'='*50}")
        print(f"测试图片: {os.path.basename(img_path)}")
        print('='*50)
        filename = img_path.split("/")[-1]
        # if filename != "2.jpg":
        #     continue
        
        img_data = image_to_base64(img_path)
        if img_data is None:
            print(f"读取图片失败: {img_path}")
            continue
        
        # 准备请求数据
        data = {
            'image': f'data:image/jpeg;base64,{img_data}'
        }
        
        try:
            # 发送请求
            r = requests.post(DEBAR_API_URL, json=data)
            
            # 解析响应
            result = r.json()
            
            # 打印结果
            print(f"状态码: {r.status_code}")
            print(f"响应码: {result.get('code')}")
            print(f"消息: {result.get('message')}")
            
            if result.get('code') == 0:
                decoded_results = result.get('results', [])
                print(f"解码到 {len(decoded_results)} 个条形码")
                
                for i, barcode in enumerate(decoded_results):
                    print(f"\n  条形码 {i+1}:")
                    print(f"    类型: {barcode.get('type')}")
                    print(f"    数据: {barcode.get('data')}")
                    print(f"    置信度: {barcode.get('confidence'):.3f}")
            else:
                print(f"错误: {result.get('message')}")
        
        except requests.exceptions.Timeout:
            print("请求超时")
        except requests.exceptions.ConnectionError:
            print("连接失败，请确认服务已启动")
        except Exception as e:
            print(f"请求失败: {e}")


def test_barcode_detect():
    """
    测试条形码检测接口
    使用 data/bar_test 目录下的测试图片
    """
    print("\n" + "="*50)
    print("测试条形码检测接口")
    print("="*50)
    
    # 测试图片目录
    test_dir = "data/bar_test"
    
    # 批量获取测试图片
    test_images = get_test_images(test_dir)
    
    if not test_images:
        return
    
    print(f"找到 {len(test_images)} 张测试图片")
    
    # 遍历测试每张图片
    for img_path in test_images:
        print(f"\n{'='*50}")
        print(f"测试图片: {os.path.basename(img_path)}")
        print('='*50)
        
        img_data = image_to_base64(img_path)
        if img_data is None:
            print(f"读取图片失败: {img_path}")
            continue
        
        # 准备请求数据
        data = {
            'image': f'data:image/jpeg;base64,{img_data}'
        }
        
        try:
            # 发送请求
            r = requests.post(BAR_API_URL, json=data)
            
            # 解析响应
            result = r.json()
            
            # 打印结果
            print(f"状态码: {r.status_code}")
            print(f"响应码: {result.get('code')}")
            print(f"消息: {result.get('message')}")
            
            if result.get('code') == 0:
                print(f"检测到 {len(result.get('results'))} 个条形码")
                
                for i, det in enumerate(result.get('results')):
                    print(f"\n  检测结果 {i+1}:")
                    print(f"    标签: {det.get('label')}")
                    print(f"    置信度: {det.get('confidence'):.3f}")
                    print(f"    边界框: {det.get('bbox')}")
                    print(f"    多边形框: {det.get('polygon')}")
            else:
                print(f"错误: {result.get('message')}")
        
        except requests.exceptions.Timeout:
            print("请求超时")
        except requests.exceptions.ConnectionError:
            print("连接失败，请确认服务已启动")
        except Exception as e:
            print(f"请求失败: {e}")


if __name__ == '__main__':
    # 测试人脸比对接口
    test_face_compare()
    
    # 测试条形码检测接口
    test_barcode_detect()
    
    # 测试条形码解码接口
    test_barcode_decode()
