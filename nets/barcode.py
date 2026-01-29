"""
使用 hexai_backend 支持 CPU/GPU/NPU 推理
"""

from hexai_backend import build_backend
import numpy as np
import cv2, os

device = os.getenv("DEVICE", "cpu")

class BarcodeModel:
    """
    条形码检测模型类
    负责模型加载和推理
    """
    
    def __init__(self, model_path, conf_threshold=0.5, iou_threshold=0.7, gpu_m_fraction=0.8):
        """
        初始化模型
        
        Args:
            model_path: ONNX 模型路径
            conf_threshold: 置信度阈值
            iou_threshold: IOU 阈值 (用于 NMS)
            gpu_m_fraction: GPU/NPU 显存比例
        """
        # 使用 hexai_backend 统一加载模型，支持 CPU/GPU/NPU
        if device != "gpu":
            gpu_m_fraction = None
        self.sess = build_backend(
            model_path,
            device,
            input_names=['input'],
            output_names=['output0', 'output1'],
            pgpu=gpu_m_fraction
        )
        
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        
        # 类别定义
        self.classes = ["barcode"]
        self.num_classes = len(self.classes)
        
        print(f"模型加载成功: {model_path}")
        print(f"device: {device}")
    
    def infer(self, input_tensor):
        """
        执行模型推理
        
        Args:
            input_tensor: 模型输入张量
            
        Returns:
            outputs: 模型输出
        """
        return self.sess([input_tensor])
    
    def sigmoid(self, z):
        """Sigmoid 激活函数"""
        return 1 / (1 + np.exp(-z))
    
    def intersection(self, box1, box2):
        """计算两个框的交集面积"""
        box1_x1, box1_y1, box1_x2, box1_y2 = box1[:4]
        box2_x1, box2_y1, box2_x2, box2_y2 = box2[:4]
        x1 = max(box1_x1, box2_x1)
        y1 = max(box1_y1, box2_y1)
        x2 = min(box1_x2, box2_x2)
        y2 = min(box1_y2, box2_y2)
        return max(0, (x2 - x1)) * max(0, (y2 - y1))
    
    def union(self, box1, box2):
        """计算两个框的并集面积"""
        box1_x1, box1_y1, box1_x2, box1_y2 = box1[:4]
        box2_x1, box2_y1, box2_x2, box2_y2 = box2[:4]
        box1_area = (box1_x2 - box1_x1) * (box1_y2 - box1_y1)
        box2_area = (box2_x2 - box2_x1) * (box2_y2 - box2_y1)
        return box1_area + box2_area - self.intersection(box1, box2)
    
    def iou(self, box1, box2):
        """计算两个框的 IOU"""
        intersection_area = self.intersection(box1, box2)
        union_area = self.union(box1, box2)
        if union_area == 0:
            return 0
        return intersection_area / union_area
    
    def get_mask(self, mask_row, box, img_width, img_height):
        """
        处理分割掩码
        
        Args:
            mask_row: 掩码数据 (展平的)
            box: 边界框坐标 [x1, y1, x2, y2]
            img_width: 原始图像宽度
            img_height: 原始图像高度
            
        Returns:
            mask: 处理后的掩码数组
        """
        from PIL import Image
        
        # 重塑为 160x160
        mask = mask_row.reshape(160, 160)
        
        # 应用 sigmoid 激活
        mask = self.sigmoid(mask)
        
        # 二值化 (阈值 0.5)
        mask = (mask > 0.5).astype('uint8') * 255
        
        # 获取边界框坐标
        x1, y1, x2, y2 = box
        
        # 将坐标缩放到 mask 尺寸
        mask_x1 = max(0, min(159, round(x1 / img_width * 160)))
        mask_y1 = max(0, min(159, round(y1 / img_height * 160)))
        mask_x2 = max(0, min(159, round(x2 / img_width * 160)))
        mask_y2 = max(0, min(159, round(y2 / img_height * 160)))
        
        # 裁剪掩码
        if mask_y2 > mask_y1 and mask_x2 > mask_x1:
            mask = mask[mask_y1:mask_y2, mask_x1:mask_x2]
            
            # 转换为 PIL Image 并调整大小到边界框尺寸
            if mask.size > 0:
                img_mask = Image.fromarray(mask, "L")
                target_width = max(1, round(x2 - x1))
                target_height = max(1, round(y2 - y1))
                img_mask = img_mask.resize((target_width, target_height))
                
                # 转回 numpy 数组
                mask = np.array(img_mask)
            else:
                mask = np.zeros((round(y2 - y1), round(x2 - x1)), dtype=np.uint8)
        else:
            mask = np.zeros((round(y2 - y1), round(x2 - x1)), dtype=np.uint8)
        
        return mask
    
    def mask_to_polygon(self, mask, box, min_points=4, max_points=8):
        """
        从掩码中提取多边形轮廓
        
        Args:
            mask: 二值化掩码数组 (uint8, 0或255)
            box: 边界框坐标 [x1, y1, x2, y2]，用于计算重合度（可选）
            min_points: 多边形最小点数 (默认4)
            max_points: 多边形最大点数限制 (默认8)
            
        Returns:
            polygon: 与box重合最多的多边形点列表，格式为 [[x1,y1], [x2,y2], ...]，如果没有有效多边形则返回[]
        """
        # 确保掩码是二值的
        if mask.dtype != np.uint8:
            mask = mask.astype(np.uint8)
        
        # 检查掩码是否有效
        if mask is None or mask.size == 0 or np.sum(mask) == 0:
            return []
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) == 0:
            return []
        
        # 简化轮廓（减少点数）
        polygons = []
        polygon_boxes = []  # 存储每个多边形的边界框
        for contour in contours:
            # 计算轮廓面积，过滤掉太小的轮廓（小于box面积的四分之一）
            area = cv2.contourArea(contour)
            if area < (box[2] - box[0]) * (box[3] - box[1]) / 4:
                continue
            # 初始 epsilon 值 - 使用周长的比例
            epsilon = 0.01 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            # 如果点数超过最大值，逐步简化
            while len(approx) > max_points:
                epsilon *= 1.5
                approx = cv2.approxPolyDP(contour, epsilon, True)
                # 防止死循环
                if len(approx) <= max_points:
                    break
            # 确保至少有4个点（条形码一般是矩形/四边形）
            if len(approx) < min_points:
                # 如果点数不足4个，尝试使用边界框作为多边形
                x, y, w, h = cv2.boundingRect(contour)
                if w > 0 and h > 0:
                    polygon = [
                        [int(x), int(y)],
                        [int(x + w), int(y)],
                        [int(x + w), int(y + h)],
                        [int(x), int(y + h)]
                    ]
                    polygons.append(polygon)
                    polygon_boxes.append([x, y, x + w, y + h])
                continue
            
            # 将轮廓点转换为列表格式 [[x1, y1], [x2, y2], ...]
            polygon = []
            for point in approx:
                x, y = point[0]
                polygon.append([int(x), int(y)])
            
            # 计算多边形的边界框
            poly_x = [p[0] for p in polygon]
            poly_y = [p[1] for p in polygon]
            poly_box = [min(poly_x), min(poly_y), max(poly_x), max(poly_y)]
            polygon_boxes.append(poly_box)
            
            # 最终检查点数范围
            if min_points <= len(polygon) <= max_points:
                polygons.append(polygon)
            elif len(polygon) > max_points:
                # 如果还是太多，截取前max_points-1个点并闭合
                polygon = polygon[:max_points-1] + [polygon[0]]
                polygons.append(polygon)
        
        # 如果只有一个多边形，直接返回
        if len(polygons) == 0 or len(polygons) == 1:
            return polygons[0] if polygons else []
        
        # 计算每个多边形与box的重合度（IOU），返回重合最多的那一个
        best_polygon = polygons[0]
        best_iou = -1
        
        for polygon, poly_box in zip(polygons, polygon_boxes):
            iou = self.iou(box, poly_box)
            if iou > best_iou:
                best_iou = iou
                best_polygon = polygon
        
        return best_polygon