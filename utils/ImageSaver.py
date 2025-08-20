# -*- encoding: utf-8 -*-
import os
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

import cv2
import numpy as np
from PIL import Image
from datetime import datetime
from utils import MessageWoker
from PySide6 import QtCore
from PySide6.QtCore import Signal


# from processing import main_stitch
def adjust_contrast_saturation(image, contrast_factor=1.0, saturation_factor=1.0):
    """
    调整图像的对比度和饱和度
    参数:
        image: 输入BGR图像
        contrast_factor: 对比度调整因子(>1增强, <1减弱)
        saturation_factor: 饱和度调整因子(>1增强, <1减弱)
    返回:
        调整后的BGR图像
    """
    # 验证输入参数
    if contrast_factor <= 0 or saturation_factor <= 0:
        raise ValueError("Factors must be positive numbers")

    # 深拷贝原始图像
    result = image.copy().astype(np.float32)

    # === 对比度调整 ===
    # 计算均值图像（使用大核模糊模拟全局均值）
    mean_blur = cv2.blur(result, (35, 35))  # 核大小可根据需要调整

    # 应用对比度公式：output = (input - mean) * factor + mean
    result = (result - mean_blur) * contrast_factor + mean_blur

    # 确保像素值在0-255范围内
    result = np.clip(result, 0, 255)

    # === 饱和度调整 ===
    # 转换到HSV空间
    hsv = cv2.cvtColor(result.astype(np.uint8), cv2.COLOR_BGR2HSV)
    hsv = hsv.astype(np.float32)  # 转换为浮点型以便运算

    # 调整饱和度通道(S)
    hsv[:, :, 1] *= saturation_factor
    hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)  # 确保饱和度在0-255

    # 转换回BGR空间
    result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    return result


class Image_Saver(QtCore.QObject):
    high_points_signal = Signal(list, list)
    # 信号
    """
    该类用于处理图像保存和拼接的任务。
    它包含一个队列来管理待处理的图像数据，
    并使用线程池来并发处理这些任务。
    self.correction_model:   0(不做平场校正) 1(做低倍平场校正) 2(做高倍平场校正) 3(高低倍都做平场校正)
    """

    def __init__(self, saver_info, requester):
        """
        初始化Saver对象。
        这包括读取配置、初始化队列和线程池，
        以及设置图像处理的相关参数。
        """
        super().__init__()
        self.requester = requester
        # 初始化图像变量
        self.main_stitch_xy = []
        self.width = None
        self.height = None
        self.base_img_low = None
        self.base_img_high = None
        self.high_points = []
        self.high_points_px = []

        # 读取配置文件
        self.maxworkers = saver_info['maxworkers']
        self.ImageStitchSize = saver_info['imagestitchsize']
        self.queuenumber = saver_info['queuenumber']
        self.PixelFormat = 'jpg'
        self.ImageQuailty = saver_info['imagequailty']
        self.correction_model = saver_info['correction_model']
        print(self.correction_model)
        self.stitcher = saver_info['stitcher']
        self.w, self.h = 2560, 2560
        self.angle = int(saver_info['angle'])

        # 初始化队列
        self.queue = Queue(self.queuenumber)

        # 初始化状态变量
        self.stopped = False  # 停止标志
        self.executor = ThreadPoolExecutor(max_workers=self.maxworkers)
        self.start_processing()

        # self.main_stitch = main_stitch.ImageStitcher()
        # self.main_stitch_images = []

        # 初始化图像拼接和数据处理变量
        self.image_stitch_all = None
        self.image_stitch_flag = False
        if self.correction_model == 0:
            pass
        elif self.correction_model == 1:
            self.base_img_low = cv2.imread('7k.jpg')

        elif self.correction_model == 2:
            self.base_img_high = cv2.imread('base_high.png')
        elif self.correction_model == 3:
            self.base_img_low = cv2.imread('base_low.png')
            self.base_img_high = cv2.imread('base_high.png')

        self.Message_Woker = MessageWoker.Message_Woker(self.maxworkers, self.queuenumber, requester)

    def flat_field_correction(self, image, flat_field):
        """
        对图像进行平场矫正。

        参数:
        image (numpy.ndarray): 输入的待矫正图像（BGR格式）。
        flat_field (numpy.ndarray): 平场图像（BGR格式）。

        返回:
        numpy.ndarray: 平场矫正后的图像（BGR格式）。
        """
        # 将图像和平场图像转换为浮点型
        image = image.astype(np.float32)
        flat_field = flat_field.astype(np.float32)

        # 避免除以零的情况，将平场图像中的零值替换为一个很小的正数
        flat_field = np.where(flat_field == 0, 1e-10, flat_field)

        # 进行平场矫正：输入图像除以平场图像
        corrected_image = image / flat_field

        # 计算平场图像的平均值，并乘以矫正后的图像以保持亮度
        scale_factor = np.mean(flat_field, axis=(0, 1))
        corrected_image = corrected_image * scale_factor

        # 将结果限制在0-255范围内，并转换为uint8类型
        corrected_image = np.clip(corrected_image, 0, 255).astype(np.uint8)

        return corrected_image

    def process_queue(self):
        """
        持续处理队列中的图像保存任务。
        3表示正常的扫描
        4表示xywh，高低倍配合扫描
                    self.Image_Saver.enqueue(Img_Number, img, str(Magnification), False, point,
                                     is_end, view_filed_group, scan_info)
        """
        while not self.stopped:
            try:
                # 从队列中获取任务数据
                [Img_Number, image, multiple, base_flag, location, is_end,
                 view_filed_group, scan_info, focus_imgs_list, best_focus_img_index] = self.queue.get(
                    timeout=0.1)
                if image is not None:
                    try:
                        stitch_flag = scan_info['field_stitch']
                        slide_id = scan_info['slide_id']
                        path_save = scan_info['save_path']
                        field_recommend = scan_info['field_recommend']
                        field_stitch = scan_info['field_stitch']
                        # 根据不同的图片格式设置编码参数
                        if self.PixelFormat.lower() == 'jpg':
                            encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.ImageQuailty]
                        elif self.PixelFormat.lower() == 'png':
                            encode_params = [cv2.IMWRITE_PNG_COMPRESSION,
                                             9 - self.ImageQuailty // 10]  # PNG uses compression level 0-9
                        elif self.PixelFormat.lower() == 'bmp':
                            encode_params = []
                        else:
                            encode_params = []
                        #
                        bgr_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                        bgr_image = adjust_contrast_saturation(bgr_image, 1.2, 0.82)
                        if self.angle == 90:
                            bgr_image = cv2.rotate(bgr_image, cv2.ROTATE_90_CLOCKWISE)
                        elif self.angle == 180:
                            bgr_image = cv2.rotate(bgr_image, cv2.ROTATE_180)
                        elif self.angle == 270 or self.angle == -90:
                            bgr_image = cv2.rotate(bgr_image, cv2.ROTATE_90_COUNTERCLOCKWISE)
                        height, width = bgr_image.shape[:2]
                        if height > self.h and width > self.w:
                            bgr_image = bgr_image[
                                        int((height - self.h) / 2):self.h + int((height - self.h) / 2),
                                        int((width - self.w) / 2):self.w + int((width - self.w) / 2)]
                        if len(focus_imgs_list) > 0:
                            # 高清对焦
                            multiple_str = str(multiple)
                            view_filed_group_str = str(view_filed_group)
                            names = []
                            for i in range(len(focus_imgs_list)):
                                name = f"{slide_id}_{view_filed_group_str}_{multiple_str}_{Img_Number}_{str(i + 1)}.{self.PixelFormat}"
                                names.append(name)
                                focus_img = focus_imgs_list[i]
                                if focus_img is not None:
                                    focus_img = cv2.cvtColor(focus_img, cv2.COLOR_RGB2BGR)
                                    focus_img = adjust_contrast_saturation(focus_img, 1.2, 0.82)
                                    if self.angle == 90:
                                        focus_img = cv2.rotate(focus_img, cv2.ROTATE_90_CLOCKWISE)
                                    elif self.angle == 180:
                                        focus_img = cv2.rotate(focus_img, cv2.ROTATE_180)
                                    elif self.angle == 270 or self.angle == -90:
                                        focus_img = cv2.rotate(focus_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                                    height, width = focus_img.shape[:2]
                                    if height > self.h and width > self.w:
                                        focus_img = focus_img[
                                                    int((height - self.h) / 2):self.h + int((height - self.h) / 2),
                                                    int((width - self.w) / 2):self.w + int((width - self.w) / 2)]
                                    focus_imgs_list[i] = focus_img
                                    # 编码并保存图像
                                    if field_recommend:
                                        if view_filed_group != 0:
                                            encoded_image = \
                                                cv2.imencode('.' + self.PixelFormat, focus_img, encode_params)[1]
                                            encoded_image.tofile(os.path.join(path_save, name))
                                    else:
                                        if view_filed_group == 0:
                                            encoded_image = \
                                                cv2.imencode('.' + self.PixelFormat, focus_img, encode_params)[1]
                                            encoded_image.tofile(os.path.join(path_save, name))
                            name_best = f"{slide_id}_{view_filed_group_str}_{multiple_str}_{Img_Number}_{str(best_focus_img_index + 1)}.{self.PixelFormat}"
                            self.Message_Woker.enqueue(scan_info, name_best, names,
                                                       location,
                                                       view_filed_group, None, is_end)
                            del encoded_image
                        else:
                            multiple_str = str(multiple)
                            view_filed_group_str = str(view_filed_group)
                            name = f"{slide_id}_{view_filed_group_str}_{multiple_str}_{Img_Number}.{self.PixelFormat}"
                            # 编码并保存图像
                            if field_recommend:
                                if view_filed_group != 0:
                                    encoded_image = \
                                        cv2.imencode('.' + self.PixelFormat, bgr_image, encode_params)[1]
                                    encoded_image.tofile(os.path.join(path_save, name))
                                    self.Message_Woker.enqueue(scan_info, name,[name],
                                                               location,
                                                               view_filed_group, None, is_end)

                                    del encoded_image
                            else:
                                if view_filed_group == 0:
                                    encoded_image = \
                                        cv2.imencode('.' + self.PixelFormat, bgr_image, encode_params)[1]
                                    encoded_image.tofile(os.path.join(path_save, name))
                                    self.Message_Woker.enqueue(scan_info, name,[name],
                                                               location,
                                                               view_filed_group, None, is_end)
                                    del encoded_image

                        # 判断是否需要平场矫正

                        # if self.correction_model == 1:
                        #     base_img = self.base_img_low
                        #     height, width = base_img.shape[:2]
                        #     if height > self.h and width > self.w:
                        #         base_img = base_img[int((height - self.h) / 2):self.h + int((height - self.h) / 2),
                        #                 int((width - self.w) / 2):self.w + int((width - self.w) / 2)]
                        #         if self.angle == 90:
                        #             base_img = cv2.rotate(base_img, cv2.ROTATE_90_CLOCKWISE)
                        #         elif self.angle == 180:
                        #             base_img = cv2.rotate(base_img, cv2.ROTATE_180)
                        #         elif self.angle == 270 or self.angle == -90:
                        #             base_img = cv2.rotate(base_img, cv2.ROTATE_90_COUNTERCLOCKWISE)

                        #     if base_img is not None:
                        #         bgr_image = self.flat_field_correction(bgr_image, base_img)
                        # 判断是否拼接
                        if stitch_flag:
                            if is_end:
                                if self.stitcher:
                                    self.add_stitch_image(Img_Number, image)
                                    cv_image = self.stitch_all()
                                    cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
                                else:
                                    self.stitch_part(location, bgr_image)
                                    cv_image = np.array(self.image_stitch_all)
                                name_stitch_img = slide_id + "_slide.jpg"
                                if field_recommend and view_filed_group == 0:
                                    if field_stitch:
                                        if self.correction_model == 1:
                                            if self.base_img_low is not None:
                                                cv_image = self.flat_field_correction(cv_image, self.base_img_low)
                                        data = self.requester.send_stitch_image(cv_image,
                                                                                scan_info['field_scan'][
                                                                                    'field_recommend_model_id'],
                                                                                scan_info['field_scan'][
                                                                                    'field_recommend_count'],
                                                                                slide_id, 'once',
                                                                                scan_info['field_scan_startX']
                                                                                , scan_info['field_scan_startY'],
                                                                                scan_info['field_scan']['len_params'][
                                                                                    'calibration'] * (
                                                                                        scan_info['field_scan'][
                                                                                            'len_params'][
                                                                                            'cropimg'][
                                                                                            'w'] / self.ImageStitchSize))

                                        self.high_points = data['data']['center_points']
                                        self.high_points_px = data['data']['center_points_px']
                                        # self.high_points_signal.emit(center_points,center_points_px)
                                        self.Message_Woker.enqueue(scan_info, name_stitch_img,[name_stitch_img],
                                                                   location,
                                                                   view_filed_group, cv_image, is_end)
                                        del data
                                        # del center_points
                                        # del center_points_px

                                encoded_stitch_image = cv2.imencode('.jpg', cv_image, [cv2.IMWRITE_JPEG_QUALITY, 100])[
                                    1]
                                encoded_stitch_image.tofile(os.path.join(path_save, name_stitch_img))
                                self.image_stitch_flag = True
                                del encoded_stitch_image
                                del cv_image
                                self.main_stitch_images = None
                                # self.image_stitch_all = None
                                del name_stitch_img
                            else:
                                if self.stitcher:
                                    self.add_stitch_image(Img_Number, image)
                                else:
                                    if field_recommend and view_filed_group == 0:
                                        self.stitch_part(location, bgr_image)
                        del Img_Number
                        del image
                        del bgr_image
                        del slide_id
                        del multiple
                        del base_flag
                        del location
                        del stitch_flag
                        del is_end
                        del path_save
                        del multiple_str
                        del name
                        del view_filed_group
                        del field_recommend
                        del height
                        del width
                    except Exception as e:
                        print(f"Error occurred: {e}")
                    # 标记任务完成
                self.queue.task_done()
            except Exception as e:
                pass

    def enqueue(self, Img_Number, image, multiple, base_flag, location, is_end,
                view_filed_group, scan_info, focus_imgs_list, best_focus_img_index):
        """
        将图像保存任务添加到队列中。
        """
        try:
            self.queue.put_nowait(
                [Img_Number, image, multiple, base_flag, location, is_end,
                 view_filed_group, scan_info, focus_imgs_list, best_focus_img_index])
        except:
            print('imageSaver queue is full, image discarded')

    def start_processing(self):
        """
        启动线程池执行队列中的任务。
        """
        for _ in range(self.maxworkers):
            self.executor.submit(self.process_queue)

    def stop(self):
        """
        停止处理队列中的任务。
        """
        self.stopped = True
        self.Message_Woker.stop()

    def stitch_part(self, Point_XY, image):
        """
        将小图像拼接到全局图像上。

        :param Point_XY: 小图像在全局图像中的位置。
        :param image: 待拼接的小图像。
        """
        try:
            image = cv2.resize(image, (self.ImageStitchSize, self.ImageStitchSize))
            # 将 OpenCV 图像转换为 Pillow Image 对象
            image_pil = Image.fromarray(image)
            self.image_stitch_all.paste(image_pil,
                                        (Point_XY[1], Point_XY[0]))
            del image
            del image_pil
        except Exception as e:
            pass

    def add_stitch_image(self, Img_Number, img):
        img = cv2.resize(img, (self.ImageStitchSize, self.ImageStitchSize))
        self.main_stitch_images[Img_Number - 1] = img

    def stitch_all(self):
        out = None
        try:
            if len(self.main_stitch_images) == self.main_stitch_xy[0] * self.main_stitch_xy[1]:
                row = 0
                images = []
                error_rows = []
                error_images = []
                success_average_dxs_1 = []
                success_average_dys_1 = []
                success_average_dxs_2 = []
                success_average_dys_2 = []

                for i in range(0, self.main_stitch_xy[0] * self.main_stitch_xy[1], self.main_stitch_xy[0]):
                    imgs = []
                    for j in range(self.main_stitch_xy[0]):
                        imgs.append(self.main_stitch_images[i + j])

                    if row % 2 == 0:
                        status, average_dx, average_dy, out = self.main_stitch.from_left_2_right_horizontal(imgs,
                                                                                                            (
                                                                                                                self.ImageStitchSize,
                                                                                                                self.ImageStitchSize))
                        if not status:
                            error_rows.append(row)
                            error_images.append(imgs)
                        else:
                            success_average_dxs_2.append(average_dx)
                            success_average_dys_2.append(average_dy)
                    else:
                        status, average_dx, average_dy, out = self.main_stitch.from_right_2_left_horizontal(imgs,
                                                                                                            (
                                                                                                                self.ImageStitchSize,
                                                                                                                self.ImageStitchSize))
                        if not status:
                            error_rows.append(row)
                            error_images.append(imgs)
                        else:
                            success_average_dxs_1.append(average_dx)
                            success_average_dys_1.append(average_dy)

                    images.append(out)
                    row = row + 1
                # 检查水平拼图是否有错误
                if 0 < len(error_rows) < row:
                    for error_row, error_image in zip(error_rows, error_images):
                        if error_row % 2 == 0:
                            if len(success_average_dxs_2) > 0:
                                success_average_dx_mean = np.mean(success_average_dxs_2)
                                success_average_dy_mean = np.mean(success_average_dys_2)
                                # offset = [int(success_average_dx_mean), int(success_average_dy_mean)]
                                offset = [-2, 268]
                                stitchResult = self.main_stitch.re_horizontal(2, offset, error_image,
                                                                              (self.ImageStitchSize,
                                                                               self.ImageStitchSize))
                                images[error_row] = stitchResult
                            else:
                                if len(success_average_dxs_1) > 0:
                                    success_average_dx_mean = np.mean(success_average_dxs_1)
                                    success_average_dy_mean = np.mean(success_average_dys_1)
                                    offset = [-int(success_average_dx_mean), -int(success_average_dy_mean)]
                                    stitchResult = self.main_stitch.re_horizontal(2, offset, error_image,
                                                                                  (self.ImageStitchSize,
                                                                                   self.ImageStitchSize))
                                    images[error_row] = stitchResult
                                else:
                                    pass
                        else:
                            if len(success_average_dxs_1) > 0:
                                success_average_dx_mean = np.mean(success_average_dxs_1)
                                success_average_dy_mean = np.mean(success_average_dys_1)
                                offset = [int(success_average_dx_mean), int(success_average_dy_mean)]
                                stitchResult = self.main_stitch.re_horizontal(4, offset, error_image,
                                                                              (self.ImageStitchSize,
                                                                               self.ImageStitchSize))
                                images[error_row] = stitchResult
                            else:
                                if len(success_average_dxs_2) > 0:
                                    success_average_dx_mean = np.mean(success_average_dxs_2)
                                    success_average_dy_mean = np.mean(success_average_dys_2)
                                    offset = [-int(success_average_dx_mean), -int(success_average_dy_mean)]
                                    stitchResult = self.main_stitch.re_horizontal(4, offset, error_image,
                                                                                  (self.ImageStitchSize,
                                                                                   self.ImageStitchSize))
                                    images[error_row] = stitchResult
                                else:
                                    pass
                else:
                    pass
            out = self.main_stitch.vertical(images)
        except Exception as e:
            print(str(e))
            return out
        return out

    def clear_stitch_all(self):
        """
        清除全局拼接图像。
        """
        self.image_stitch_all = None
        self.image_stitch_flag = False
        self.high_points = []
        self.high_points_px = []
