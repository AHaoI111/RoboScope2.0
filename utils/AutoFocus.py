import cv2
import numpy as np


# def Sharpness(image):
#     # 将图像转换为灰度图像
#     if len(image.shape) == 3:
#         gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#     else:
#         gray = image
#     # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#
#     # 计算Sobel算子在x和y方向上的梯度
#     sharpness = np.std(gray)
#
#     return sharpness

def Sharpness(image):
    """计算图像清晰度（使用Sobel算子）"""
    # 转换为灰度图像（如果原始是彩色图）
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # 应用Sobel算子计算x和y方向的梯度
    sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

    # 计算梯度幅值
    gradient_magnitude = np.sqrt(sobel_x ** 2 + sobel_y ** 2)

    # 计算清晰度指标（平均梯度幅值）
    # sharpness = np.mean(gradient_magnitude)
    # 计算清晰度指标
    weighted_sharpness = np.sum(gradient_magnitude ** 2) / np.sum(gradient_magnitude)

    return weighted_sharpness
