"""
条形码检测业务逻辑模块
负责预处理、调用模型推理、后处理得到最终结果
"""

import numpy as np
from PIL import Image
import cv2
from nets.model_manager import manager
from pyzbar.pyzbar import decode


class BarDetect:
    """
    条形码检测业务类
    """
    
    def __init__(self):
        self.model = manager.get_model("barcode")
    
    def preprocess(self, image_path):
        """
        预处理图像
        
        Args:
            image_path: 图像路径或 PIL Image 对象
            
        Returns:
            input_tensor: 模型输入张量
            original_size: 原始图像尺寸
        """
        if isinstance(image_path, str):
            img = Image.open(image_path)
        else:
            img = image_path
            
        # 保存原始尺寸
        original_size = img.size  # (width, height)
        
        # 转换为 RGB
        img = img.convert("RGB")
        
        # 调整大小到 640x640
        img_resized = img.resize((640, 640))
        
        # 转换为张量 [1, 3, 640, 640]
        input_tensor = np.array(img_resized)
        input_tensor = input_tensor.transpose(2, 0, 1)
        input_tensor = input_tensor.reshape(1, 3, 640, 640).astype('float32')
        input_tensor = input_tensor / 255.0
        
        return input_tensor, original_size, img
    
    def postprocess(self, outputs, img_width, img_height):
        """
        后处理模型输出
        
        输出格式: (1, 37, 8400)
        - 4: 边界框坐标 (x_center, y_center, width, height)
        - 1: objectness 置信度
        - 32: 分割掩码系数
        
        优化: 先进行 NMS 过滤，再对保留的少量检测框进行掩码矩阵乘法，大幅减少计算量
        
        Args:
            outputs: 模型输出
            img_width: 原始图像宽度
            img_height: 原始图像高度
            
        Returns:
            results: 检测结果列表
        """
        # 提取输出
        output0 = outputs[0][0].transpose()  # (8400, 37)
        output1 = outputs[1][0]  # (32, 160, 160) - 掩码原型
        
        # 分离检测框和掩码系数
        boxes = output0[:, 0:4]  # [x, y, w, h]
        confs = output0[:, 4]    # objectness
        masks = output0[:, 5:37] # 32 个掩码系数
        
        # 第一步: 根据置信度过滤，并转换坐标格式
        candidates = []
        for i in range(len(boxes)):
            conf = confs[i]
            
            # 过滤低置信度检测
            if conf < self.model.conf_threshold:
                continue
            
            # 获取边界框坐标 (中心点格式)
            xc, yc, w, h = boxes[i]
            
            # 转换为左上角右下角格式，并缩放到原始图像尺寸
            x1 = (xc - w / 2) / 640 * img_width
            y1 = (yc - h / 2) / 640 * img_height
            x2 = (xc + w / 2) / 640 * img_width
            y2 = (yc + h / 2) / 640 * img_height
            
            # 保存候选检测框（暂不计算掩码）
            candidates.append({
                'bbox': [x1, y1, x2, y2],
                'confidence': float(conf),
                'mask_coeffs': masks[i],  # 保存掩码系数
                'index': i
            })
        
        # 第二步: 对候选框应用 NMS
        candidates.sort(key=lambda x: x['confidence'], reverse=True)
        nms_results = []
        
        while len(candidates) > 0:
            nms_results.append(candidates[0])
            candidates = [obj for obj in candidates if self.model.iou(obj['bbox'], nms_results[-1]['bbox']) < self.model.iou_threshold]
        
        # 第三步: 只对 NMS 保留的少量检测框计算掩码（大幅减少矩阵乘法）
        results = []
        
        # 重塑 output1 用于矩阵乘法（只做一次）
        output1_reshaped = output1.reshape(32, 160 * 160)  # (32, 25600)
        
        for obj in nms_results:
            x1, y1, x2, y2 = obj['bbox']
            box = [x1, y1, x2, y2]
            
            # 矩阵乘法生成掩码（只对 NMS 后的少量框计算）
            mask_coeffs = obj['mask_coeffs']  # (32,)
            mask_flat = mask_coeffs @ output1_reshaped  # (25600,)
            
            # 获取最终掩码
            mask = self.model.get_mask(mask_flat, box, img_width, img_height)
            
            # 从掩码中提取多边形轮廓（传入box参数，返回与box重合最多的多边形）
            polygon = self.model.mask_to_polygon(mask, box)
            
            results.append({
                'bbox': box,
                'label': self.model.classes[0],  # barcode
                'confidence': obj['confidence'],
                'mask': mask,
                'polygon': polygon
            })
        
        return results
    
    def calculate_rotation_angle(self, polygon):
        """
        计算多边形的旋转角度
        
        Args:
            polygon: 多边形顶点列表，每个顶点为 [x, y]
            
        Returns:
            float: 旋转角度（度）
        """
        if polygon is None or len(polygon) < 4:
            return 0.0
        
        polygon = np.array(polygon)
        
        # 计算多边形的最小外接矩形
        rect = cv2.minAreaRect(polygon)
        
        # 获取矩形的四个角点
        box = cv2.boxPoints(rect)  # 返回 4x2 的数组
        
        # 计算每条边的长度
        edges = [
            np.linalg.norm(box[0] - box[1]),
            np.linalg.norm(box[1] - box[2]),
            np.linalg.norm(box[2] - box[3]),
            np.linalg.norm(box[3] - box[0])
        ]
        
        # 找出长边（条形码的方向）
        # 条形码是细长的，取较长的两条边中的一条作为方向
        long_edge_idx = 0 if edges[0] >= edges[1] else 1
        
        # 计算长边的角度
        if long_edge_idx == 0:
            dx = box[1][0] - box[0][0]
            dy = box[1][1] - box[0][1]
        else:
            dx = box[2][0] - box[1][0]
            dy = box[2][1] - box[1][1]
        
        # 计算相对于水平轴的角度
        rotation_angle = np.degrees(np.arctan2(dy, dx))
        
        return rotation_angle


    def should_correct_rotation(self, polygon, threshold=15):
        """
        判断是否需要校正旋转
        
        Args:
            polygon: 多边形顶点列表
            threshold: 角度阈值（度），默认 15
            
        Returns:
            bool: 是否需要校正
            float: 旋转角度（度）
        """
        angle = self.calculate_rotation_angle(polygon)
        
        # 判断角度是否超过阈值
        # 考虑对称性：条形码旋转 180 度看起来一样，所以只需要考虑 [-90, 90] 范围内
        # 归一化角度到 [-90, 90]
        normalized_angle = angle
        if normalized_angle > 90:
            normalized_angle -= 180
        elif normalized_angle < -90:
            normalized_angle += 180
        
        # 检查是否需要校正（使用绝对值）
        return abs(normalized_angle) > threshold, normalized_angle


    def rotate_image_and_mask(self, image, mask, angle, center=None):
        """
        旋转图像和掩码
        
        Args:
            image: numpy 数组格式的图像
            mask: numpy 数组格式的掩码
            angle: 旋转角度（度），正值为顺时针
            center: 旋转中心，默认为图像中心
            
        Returns:
            rotated_image: 旋转后的图像
            rotated_mask: 旋转后的掩码
        """
        (h, w) = image.shape[:2]
        
        if center is None:
            center = (w // 2, h // 2)
        
        # 计算旋转矩阵
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # 旋转图像
        rotated_image = cv2.warpAffine(image, rotation_matrix, (w, h), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
        
        # 旋转掩码（单通道）
        if mask is not None and mask.ndim == 2:
            rotated_mask = cv2.warpAffine(mask, rotation_matrix, (w, h), flags=cv2.INTER_NEAREST, borderValue=0)
        else:
            rotated_mask = mask
        
        return rotated_image, rotated_mask

    def filter_mask_by_polygon(self, mask, polygon, bbox, expand_pixels=10):
        """
        使用多边形过滤掩码，只保留多边形内部（扩展后）的区域
        
        Args:
            mask: 全尺寸掩码（numpy 数组）
            polygon: 多边形顶点列表 [[x1,y1], [x2,y2], ...]，坐标相对于 bbox
            bbox: 边界框 [x1, y1, x2, y2]
            expand_pixels: 多边形向外扩展的像素数，默认 10
            
        Returns:
            filtered_mask: 过滤后的掩码
        """
        if polygon is None or len(polygon) < 3:
            return mask
        
        # 创建与原掩码相同尺寸的空白掩码
        filtered_mask = np.zeros_like(mask)
        
        # 获取 bbox 的偏移量
        x1, y1, _, _ = [int(v) for v in bbox]
        
        # 将 polygon 坐标转换为绝对坐标（加上 bbox 偏移）
        polygon_abs = np.array(polygon, dtype=np.int32)
        if polygon_abs.ndim == 2 and polygon_abs.shape[1] == 2:
            polygon_abs = polygon_abs + np.array([x1, y1])
        
        # 将多边形向外扩展 10 个像素
        # 创建更大的掩码用于膨胀操作
        temp_mask = np.zeros_like(mask)
        cv2.fillPoly(temp_mask, [polygon_abs], 255)
        
        # 创建膨胀核（圆形，半径 10）
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (expand_pixels * 2 + 1, expand_pixels * 2 + 1))
        
        # 膨胀操作，向外扩展多边形
        expanded_mask = cv2.dilate(temp_mask, kernel, iterations=1)
        
        # 与原掩码进行与操作，只保留扩展后多边形内部的区域
        filtered_mask = cv2.bitwise_and(mask, expanded_mask)
        
        return filtered_mask

    def predict(self, image_path):
        """
        对图像进行预测
        
        Args:
            image_path: 图像路径或 PIL Image 对象
            
        Returns:
            results: 检测结果列表
        """
        # 预处理
        input_tensor, (img_width, img_height), img = self.preprocess(image_path)
        
        # 运行推理
        outputs = self.model.infer(input_tensor)
        
        # 后处理
        results = self.postprocess(outputs, img_width, img_height)
        
        return results, img
    
    def barcode_decode(self, image_path):
        # 1. 获取检测结果和原图
        bar_results, original_img = self.predict(image_path)
        
        # 转换为 numpy 数组
        original_img_np = np.array(original_img)
        
        # 2. 遍历每个检测结果，裁剪并解码
        results = []
        for result in bar_results:
            mask = result.get('mask')
            polygon = result.get('polygon')
            if mask is None:
                continue
            
            # mask 已经是裁剪到 bbox 尺寸的，需要放大回原图尺寸
            x1, y1, x2, y2 = [int(v) for v in result['bbox']]
            
            # 创建与原图同尺寸的掩码
            full_mask = np.zeros(original_img_np.shape[:2], dtype=np.uint8)
            
            # 调整 mask 大小并放入对应位置
            mask_resized = cv2.resize(mask, (x2 - x1, y2 - y1))
            full_mask[y1:y2, x1:x2] = mask_resized
            
            # 使用多边形过滤掩码（向外扩展 10 像素）
            full_mask = self.filter_mask_by_polygon(full_mask, polygon, result['bbox'], expand_pixels=10)
            
            # 检查是否需要旋转校正
            need_correction, rotation_angle = self.should_correct_rotation(polygon, threshold=15)
            
            # 如果需要旋转校正，则旋转图像和掩码
            if need_correction:
                original_img_np, full_mask = self.rotate_image_and_mask(original_img_np, full_mask, rotation_angle)
            
            # 使用掩码提取 ROI
            cropped = cv2.bitwise_and(original_img_np, original_img_np, mask=full_mask)
            
            # 裁剪到最小包围区域（去除黑边）
            coords = np.column_stack(np.where(full_mask > 0))
            if len(coords) > 0:
                y_min, x_min = coords.min(axis=0)
                y_max, x_max = coords.max(axis=0)
                cropped = cropped[y_min:y_max, x_min:x_max]
            
            # 保存裁剪图像到当前目录
            cropped_pil = Image.fromarray(cropped)
            # cropped_pil.save(f"/data/cjl/ai-supervise-server/data/cropped/cropped_{len(results)}.jpg")
            
            # 使用 pyzbar 解码
            barcodes = decode(cropped_pil)
            
            for barcode in barcodes:
                results.append({
                    'type': barcode.type,
                    'data': barcode.data.decode('utf-8'),
                    'rect': barcode.rect,
                    'confidence': result['confidence']
                })
        return results

########################可视化检测结果看效果###################################
    def visualize(self, image_path, results, output_path=None, draw_polygon=True):
        """
        Args:
            image_path: 原始图像路径
            results: 检测结果
            output_path: 输出路径 (可选)
            draw_polygon: 是否绘制多边形轮廓
            
        Returns:
            annotated_image: 标注后的图像
        """
        # 读取原始图像
        if isinstance(image_path, str):
            img = cv2.imread(image_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            img = np.array(image_path)
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        
        overlay = img.copy()
        
        for result in results:
            x1, y1, x2, y2 = [int(v) for v in result['bbox']]
            label = result['label']
            conf = result['confidence']
            mask = result['mask']
            polygons = result.get('polygons', [])
            
            # 绘制边界框
            cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 绘制标签
            text = f"{label}: {conf:.2f}"
            cv2.putText(overlay, text, (x1, max(0, y1 - 10)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # 绘制多边形轮廓
            if draw_polygon and len(polygons) > 0:
                for polygon in polygons:
                    # 将多边形点转换为 numpy 数组
                    pts = np.array(polygon, dtype=np.int32)
                    
                    # 绘制多边形轮廓（红色线条）
                    # 注意：多边形坐标是相对于边界框的，需要加上边界框左上角坐标
                    pts_shifted = pts + np.array([x1, y1])
                    
                    cv2.polylines(overlay, [pts_shifted], True, (255, 0, 0), 2)
            
            # 应用掩码 (半透明)
            if mask is not None and mask.shape[0] > 0 and mask.shape[1] > 0:
                # 确保坐标在图像范围内
                x1_safe = max(0, min(x1, img.shape[1]))
                y1_safe = max(0, min(y1, img.shape[0]))
                x2_safe = max(0, min(x2, img.shape[1]))
                y2_safe = max(0, min(y2, img.shape[0]))
                
                if x2_safe > x1_safe and y2_safe > y1_safe:
                    # 调整掩码大小以匹配边界框
                    mask_resized = cv2.resize(mask, (x2_safe - x1_safe, y2_safe - y1_safe))
                    
                    # 创建彩色掩码
                    mask_colored = np.zeros((y2_safe - y1_safe, x2_safe - x1_safe, 3), dtype=np.uint8)
                    mask_colored[mask_resized > 127] = [0, 255, 0]  # 绿色
                    
                    # 混合
                    roi = overlay[y1_safe:y2_safe, x1_safe:x2_safe]
                    overlay[y1_safe:y2_safe, x1_safe:x2_safe] = cv2.addWeighted(roi, 0.7, mask_colored, 0.3, 0)
        
        # 如果有输出路径，保存图像
        if output_path:
            img_bgr = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
            cv2.imwrite(output_path, img_bgr)
            print(f"可视化结果已保存到: {output_path}")
        
        return overlay
    
def main():
    """
    主函数示例
    """
    # 测试图像路径
    image_path = "datasets/segment/test/3.jpg"
    
    # 初始化模型
    print("初始化模型...")
    model = BarDetect()
    
    # 进行预测
    print(f"\n正在处理图像: {image_path}")
    results = model.predict(image_path)
    
    print(f"\n检测到 {len(results)} 个对象:")
    for i, result in enumerate(results):
        print(f"\n对象 {i + 1}:")
        print(f"  类别: {result['label']}")
        print(f"  置信度: {result['confidence']:.3f}")
        print(f"  边界框: {result['bbox']}")
        if result['mask'] is not None:
            print(f"  掩码形状: {result['mask'].shape}")
        if 'polygons' in result and len(result['polygons']) > 0:
            print(f"  多边形数量: {len(result['polygons'])}")
            for j, polygon in enumerate(result['polygons']):
                print(f"    多边形 {j + 1}: {len(polygon)} 个点")
    cv2.imwrite("mask.png", results[0]['mask'])
    # 可视化结果（绘制边界框、掩码和多边形轮廓）
    output_path = "result_annotated.jpg"
    model.visualize(image_path, results, output_path, draw_polygon=True)
    
    return results


if __name__ == "__main__":
    main()
