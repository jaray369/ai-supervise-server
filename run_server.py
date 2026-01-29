#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人脸比对API服务
提供/face_compare接口用于人脸比对
"""

import os
import base64
import uuid
import io
from flask import Flask, request, jsonify
import logging
from logging.handlers import RotatingFileHandler
from PIL import Image
from app.face_compare import FaceComparator
from app.barcode_detect import BarDetect

# 初始化模型
comparator = FaceComparator()
bar = BarDetect()
# 配置日志
def setup_logging():
    """配置日志系统"""
    # 获取项目根目录（兼容exec启动方式）
    if '__file__' in dir():
        # 正常Python脚本启动
        project_dir = os.path.dirname(os.path.abspath(__file__))
    else:
        # exec方式启动，使用当前工作目录
        project_dir = os.getcwd()
    
    log_dir = os.path.join(project_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'server.log')
    
    # 创建logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 清除已有的handlers
    logger.handlers.clear()
    
    # 创建文件处理器（带日志轮转，每个文件最大10MB，保留5个备份）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 初始化日志
setup_logging()

app = Flask(__name__)

def validate_image_format(image_data):
    """验证数据是否为有效的图片格式"""
    try:
        # 使用Pillow验证图片格式
        img = Image.open(io.BytesIO(image_data))
        img.verify()  # 验证图片完整性
        
        # 重新打开因为verify()会消耗文件
        img = Image.open(io.BytesIO(image_data))
        
        # 支持的图片格式列表
        supported_formats = {'JPEG', 'PNG', 'JPG', 'WEBP', 'BMP', 'GIF'}
        img_format = img.format.upper() if img.format else ''
        
        if img_format not in supported_formats:
            raise ValueError(f"不支持的图片格式: {img_format}")
        
        return True, img_format
    except Exception as e:
        logging.error(f"图片错误: {str(e)}")
        return False, str(e)

def save_base64_image(base64_string, upload_dir='./data/uploads'):
    """将base64字符串保存为图片文件"""
    # 确保上传目录存在
    os.makedirs(upload_dir, exist_ok=True)
    
    # 解码base64
    if ',' in base64_string:
        # 移除data:image/jpeg;base64,等前缀
        base64_string = base64_string.split(',')[1]
    
    image_data = base64.b64decode(base64_string)
    
    # 验证是否为有效的图片格式
    is_valid, result = validate_image_format(image_data)
    if not is_valid:
        raise ValueError(f"图片格式错误: {result}")
    
    # 生成唯一文件名
    filename = f"{uuid.uuid4()}.jpg"
    filepath = os.path.join(upload_dir, filename)
    
    # 保存图片
    with open(filepath, 'wb') as f:
        f.write(image_data)
    
    return filepath

def icr_process():
    try:
        img1_path = None
        img2_path = None
        
        # 判断是JSON请求还是multipart/form-data请求
        if request.is_json:
            data = request.get_json()
            
            # 检查必需参数
            if 'image1' not in data or 'image2' not in data:
                logging.error("缺少必需参数：image1和image2")
                return {
                    'is_same_person': False,
                    'message': '缺少必需参数：image1和image2'
                }, 400
            
            # 保存base64图片（包含图片格式验证）
            try:
                img1_path = save_base64_image(data['image1'])
                img2_path = save_base64_image(data['image2'])
                logging.info(f"保存base64图片: {img1_path}, {img2_path}")
            except ValueError as ve:
                logging.error(f"图片格式错误: {str(ve)}")
                return {
                    'is_same_person': False,
                    'message': str(ve)
                }, 400
        
        # 进行人脸比对
        logging.info(f"开始比对人脸: {img1_path} vs {img2_path}")
        distance, is_same_person = comparator.compare(img1_path, img2_path)
        
        # 清理临时文件
        try:
            if os.path.exists(img1_path):
                os.remove(img1_path)
            if os.path.exists(img2_path):
                os.remove(img2_path)
            logging.info(f"清理临时文件成功")
        except Exception as cleanup_error:
            logging.warning(f"清理临时文件失败: {str(cleanup_error)}")
        
        # 返回成功结果
        result = {
            'is_same_person': is_same_person,
            'message': 'ok'
        }
        logging.info(f"比对完成: distance={distance}, is_same_person={is_same_person}")
        return result
        
    except Exception as e:
        logging.error(f"服务器错误: {str(e)}", exc_info=True)
        return {
            'is_same_person': False,
            'message': f'服务器错误: {str(e)}'
        }, 500

@app.route('/face_compare', methods=['POST'])
def face_compare():
    import time
    logging.info("Call /face_compare")
    start_time = time.time()
    result = icr_process()
    # 计算耗时（秒）并记录到日志
    cost_time = round(time.time() - start_time, 3)
    logging.info(f"cost_time: {cost_time}s")
    # 返回结果
    if isinstance(result, tuple):
        # 处理有状态码的情况
        response_data, status_code = result
        return jsonify(response_data), status_code
    else:
        # 正常返回
        return jsonify(result)


def bd_process():
    """
    条形码检测处理函数
    接收 base64 编码的图片，返回检测结果
    """
    try:
        img_path = None
        
        # 判断是JSON请求还是multipart/form-data请求
        if request.is_json:
            data = request.get_json()
            
            # 检查必需参数
            if 'image' not in data:
                logging.error("缺少必需参数：image")
                return {
                    'code': -1,
                    'message': '缺少必需参数：image'
                }, 400
            
            # 保存base64图片
            try:
                img_path = save_base64_image(data['image'])
                logging.info(f"保存base64图片: {img_path}")
            except ValueError as ve:
                logging.error(f"图片格式错误: {str(ve)}")
                return {
                    'code': -1,
                    'message': str(ve)
                }, 400
        else:
            return {
                'code': -1,
                'message': '只支持 JSON 请求格式'
            }, 400
        
        # 进行条形码检测
        logging.info(f"开始检测条形码: {img_path}")
        results, _ = bar.predict(img_path)
        if 0 == len(results):
            return {
            'code': 0,
            'message': '未检测到条形码！',
            'results': results
        }
        # 删除 mask 字段
        for result in results:
            result.pop('mask', None)
        
        # 清理临时文件
        try:
            if os.path.exists(img_path):
                os.remove(img_path)
                logging.info(f"清理临时文件成功")
        except Exception as cleanup_error:
            logging.warning(f"清理临时文件失败: {str(cleanup_error)}")

        return {
            'code': 0,
            'message': 'ok',
            'results': results
        }
        
    except Exception as e:
        logging.error(f"服务器错误: {str(e)}", exc_info=True)
        return {
            'code': -1,
            'message': f'服务器错误: {str(e)}'
        }, 500

def bc_process():
    """
    条形码解码处理函数
    接收 base64 编码的图片，返回解码结果
    """
    try:
        img_path = None
        
        # 判断是JSON请求还是multipart/form-data请求
        if request.is_json:
            data = request.get_json()
            
            # 检查必需参数
            if 'image' not in data:
                logging.error("缺少必需参数：image")
                return {
                    'code': -1,
                    'message': '缺少必需参数：image'
                }, 400
            
            # 保存base64图片
            try:
                img_path = save_base64_image(data['image'])
                logging.info(f"保存base64图片: {img_path}")
            except ValueError as ve:
                logging.error(f"图片格式错误: {str(ve)}")
                return {
                    'code': -1,
                    'message': str(ve)
                }, 400
        else:
            return {
                'code': -1,
                'message': '只支持 JSON 请求格式'
            }, 400
        
        # 进行条形码解码
        logging.info(f"开始解码条形码: {img_path}")
        results = bar.barcode_decode(img_path)
        message = 'ok'
        if 0 == len(results):
            message = '解码失败！'
        # 清理临时文件
        try:
            if os.path.exists(img_path):
                os.remove(img_path)
                logging.info(f"清理临时文件成功")
        except Exception as cleanup_error:
            logging.warning(f"清理临时文件失败: {str(cleanup_error)}")

        response = {
            'code': 0,
            'message': message,
            'results': results
        }
        
        return response
        
    except Exception as e:
        logging.error(f"服务器错误: {str(e)}", exc_info=True)
        return {
            'code': -1,
            'message': f'服务器错误: {str(e)}'
        }, 500

@app.route('/bar_detect', methods=['POST'])
def bar_detect():
    """
    条形码检测接口
    接收 base64 编码的图片，返回检测结果
    """
    import time
    logging.info("Call /bar_detect")
    start_time = time.time()
    
    result = bd_process()
    
    # 计算耗时（秒）并记录到日志
    cost_time = round(time.time() - start_time, 3)
    if isinstance(result, tuple):
        logging.info(f"cost_time: {cost_time}s")
        response_data, status_code = result
        return jsonify(response_data), status_code
    else:
        logging.info(f"检测完成: cost_time: {cost_time}s")
        return jsonify(result)

@app.route('/bar_decode', methods=['POST'])
def bar_decode():
    """
    条形码解码接口
    接收 base64 编码的图片，返回解码结果
    """
    import time
    logging.info("Call /bar_decode")
    start_time = time.time()
    
    result = bc_process()
    
    # 计算耗时（秒）并记录到日志
    cost_time = round(time.time() - start_time, 3)
    if isinstance(result, tuple):
        logging.info(f"cost_time: {cost_time}s")
        response_data, status_code = result
        return jsonify(response_data), status_code
    else:
        logging.info(f"解码完成: cost_time: {cost_time}s")
        return jsonify(result)

if __name__ == '__main__':
    # from waitress import serve
    # logging.info("* Starting web service...")
    # face_comparator = FaceComparator()
    # serve(app, host='0.0.0.0', port=5002, threads=2) # , threads=1

    logging.info("* Starting web service...")
    app.run(host='0.0.0.0', port=5002, debug=True)
