import math
import os
import threading
import time
from datetime import datetime
from queue import Queue

import cv2
import numpy as np
from PIL import Image
from PySide6 import QtCore
from PySide6.QtCore import Signal, Slot

from utils import AutoFocus
from concurrent.futures import ThreadPoolExecutor


def get_time_2():
    # 获取当前系统时间
    current_time = datetime.now()
    # 格式化时间显示
    year = current_time.strftime("%Y")
    month = current_time.strftime("%m")
    day = current_time.strftime("%d")
    return year, month, day


class ScanManager(QtCore.QObject):
    scan_img = Signal(np.ndarray, int, list, bool, int, int, int, int)
    scan_info = Signal(str)
    progress_signal = Signal(int)

    def __init__(self, microscope, scan_camera, ocr_camera, my_devices_info, logger, requester):
        super().__init__()
        self.Image_Saver = None
        self.high_points = None
        self.high_points_px = None
        self.requester = requester
        self.step = 0.001
        self.number = 20

        self.microscope = microscope
        self.scan_camera = scan_camera
        self.ocr_camera = ocr_camera
        self.my_devices_info = my_devices_info
        self.logger = logger
        self.run_scan_flag = True
        self.is_running = False

        # 对焦线程
        self.threshold_fcous = 0.85
        self.queue = Queue(200)
        self.focus_score = [0] * self.number
        self.focus_img = [None] * self.number
        self.pos_z_all = [0] * self.number

        self.executor = ThreadPoolExecutor(max_workers=3)

    def check_laserz(self, laserz_list):
        if len(laserz_list) < 2:
            return 0, laserz_list
        max_value = max(laserz_list)
        min_value = min(laserz_list)
        return max_value - min_value, sum(laserz_list) / len(laserz_list)

    @Slot(list, list)
    def updata_high_points(self, points, points_px):
        self.high_points = points
        self.high_points_px = points_px

    def get_route(self, h, w, center_x, center_y, region_w, region_h, calibration):
        points_xy_real = []
        points_xy = []

        view_w_mm = w * calibration
        view_h_mm = h * calibration

        # 起始点
        x_start_mm = center_x + region_w / 2
        y_start_mm = center_y + region_h / 2

        # 视野个数
        number_x = math.ceil(region_w / (w * calibration))
        number_y = math.ceil(region_h / (h * calibration))
        # 路径坐标
        for i in range(int(number_y)):
            if i % 2 == 0:
                for j in range(int(number_x)):
                    points_xy_real.append([x_start_mm - (j + 0.5) * view_w_mm, y_start_mm - (i + 0.5) * view_w_mm])
                    points_xy.append([i, j])
            else:
                for j in range(int(number_x) - 1, -1, -1):
                    points_xy_real.append([x_start_mm - (j + 0.5) * view_w_mm, y_start_mm - (i + 0.5) * view_w_mm])
                    points_xy.append([i, j])
        del h
        del w
        del center_x
        del center_y
        del region_w
        del region_h
        del calibration
        return points_xy, points_xy_real, number_x, number_y, x_start_mm, y_start_mm

    def read_scan_image(self, rgbw):
        self.microscope.led_rgbw_ctrl(rgbw[0], rgbw[1], rgbw[2], rgbw[3])  # rgbw
        # time.sleep(0.005)
        self.scan_camera.send_trigger()
        image = self.scan_camera.read_frame()
        self.microscope.led_rgbw_ctrl(0, 0, 0, 0)
        return image

    def start_processing(self):
        # 创建并启动单个工作线程
        # self.focus_thread = threading.Thread(target=self.process_queue, daemon=True)
        # self.focus_thread.start()

        futures = [self.executor.submit(self.process_queue) for _ in range(3)]
        return futures

    def enqueue(self, is_first, i, image, count, posz):
        try:
            self.queue.put_nowait([is_first, i, image, count, posz])
        except:
            print('imageSaver queue is full, image discarded')

    def process_queue(self):
        while not self.stopped:
            try:
                [is_first, i, image, count, posz] = self.queue.get(timeout=0.1)
                if image is not None:
                    if i == 0:
                        self.focus_img = []
                        self.focus_score = []
                        self.pos_z_all = []
                    definition = AutoFocus.Sharpness(image)
                    self.focus_img.append(image)
                    self.focus_score.append(definition)
                    self.pos_z_all.append(posz)

                    if definition < max(self.focus_score) * self.threshold_fcous and count > 50:
                        index_max_definition = self.focus_score.index(max(self.focus_score))
                        if i > index_max_definition:
                            self.stopped = True
                            self.max_pos = self.pos_z_all[index_max_definition]
                            self.max_focus_score_img = self.focus_img[index_max_definition]
                            #
                            left_start = max(0, index_max_definition - 2)  # 左边起始索引
                            right_end = min(len(self.focus_score), index_max_definition + 3)  # 右边结束索引（不包含）
                            self.focus_imgs_list = self.focus_img[left_start:right_end]
                            self.focus_imgs_index = index_max_definition - left_start

                            self.Autofocus_flag = False
                            self.focus_img.clear()
                            self.focus_score.clear()
                            self.pos_z_all.clear()

                    if i == count:
                        self.stopped = True
                        self.max_pos = self.pos_z_all[self.focus_score.index(max(self.focus_score))]
                        #
                        index_max_definition = self.focus_score.index(max(self.focus_score))
                        self.max_focus_score_img = self.focus_img[index_max_definition]
                        #
                        left_start = max(0, index_max_definition - 2)  # 左边起始索引
                        right_end = min(len(self.focus_score), index_max_definition + 3)  # 右边结束索引（不包含）
                        self.focus_imgs_list = self.focus_img[left_start:right_end]
                        self.focus_imgs_index = index_max_definition - left_start

                        self.Autofocus_flag = False
                        self.focus_img.clear()
                        self.focus_score.clear()
                        self.pos_z_all.clear()
                del image
                del is_first
                del i
                del count
                del posz
                self.queue.task_done()
            except Exception as e:
                pass

    def AutofocusWorker(self, start, is_first, rgbw, stitch_flag):
        self.focus_img = []
        self.focus_score = []
        self.pos_z_all = []

        # 对焦队列
        self.focus_imgs_list = []
        self.focus_imgs_index = None

        self.max_focus_score_img = None
        self.stopped = False
        self.Autofocus_flag = True
        self.max_pos = start

        futures = self.start_processing()

        for i in range(self.number):
            self.microscope.set_delivery_abs_z(start + self.step * i)
            img = self.read_scan_image(rgbw)
            resize_img = cv2.resize(img, (640, 640))
            self.enqueue(is_first, i, img, self.number - 1, start + self.step * i)
            self.scan_img.emit(resize_img, 0, [], stitch_flag, 0, 0, 640, 640)
            if self.Autofocus_flag:
                pass
            else:
                break

        # 等待任务完成，不需要限制时间
        while self.Autofocus_flag:
            time.sleep(0.005)

        # self.focus_thread.join(timeout=3.0)
        for future in futures:
            try:
                future.result(timeout=5)  # 设置超时时间为 5 秒
            except TimeoutError:
                print("A task timed out!")

        # del self.focus_thread
        del futures

        del img
        del resize_img
        del start
        del is_first
        del rgbw
        del stitch_flag

        return self.max_pos, self.max_focus_score_img, self.focus_imgs_list, self.focus_imgs_index

    def run_scan(self, scan_info, user_id, task_id):
        # 1是否需要推荐视野
        # 如果需要则是先低倍，然后等待高倍返回坐标继续扫描高倍
        # 如果不需要则直接扫描，配置需要扫几个物镜就扫多少。
        # 判断是否停止
        # self.is_running = True
        # 暂停卡住
        if self.is_running:
            pass
        else:
            self.requester.update_slide_info(scan_info['slide_id'], 'pause', '用户暂停', user_id)
            while not self.is_running:
                time.sleep(0.1)
            self.requester.update_slide_info(scan_info['slide_id'], 'scanning', '扫描中', user_id)
            self.requester.update_task_info(task_id, 'scanning', '扫描中', user_id)
        if self.run_scan_flag:
            pass
        else:
            self.requester.update_slide_info(scan_info['slide_id'], 'canceled', '用户取消', user_id)
            return False
        try:
            self.logger.info('开始扫描')
            self.logger.info('扫描方案：' + str(scan_info))
            flag = False
            self.Image_Saver.image_stitch_flag = False
            # 判断是否是推荐视野
            if scan_info['field_recommend']:
                self.requester.update_slide_info(scan_info['slide_id'], 'low_scanning', '低倍扫描中', user_id)
                # 低倍预扫镜头
                objective = scan_info['field_scan']['len_position']
                # 切换物镜获取对应物镜的光源强度
                if objective == 1:
                    self.microscope.select_objective_num1()
                elif objective == 2:
                    self.microscope.select_objective_num2()
                elif objective == 3:
                    self.microscope.select_objective_num3()
                elif objective == 4:
                    self.microscope.select_objective_num4()
                rgbw = scan_info['field_scan']['len_params']['IlluminationIntensity']
                calibration = float(scan_info['field_scan']['len_params']['calibration'])
                ExposureTime = float(scan_info['field_scan']['len_params']['ExposureTime'])
                WB = scan_info['field_scan']['len_params']['WB']

                # 设置对应曝光
                self.scan_camera.set_exposure_time(ExposureTime)
                self.scan_camera.set_wb_ratios(WB['R'], WB['G'], WB['B'])
                img = self.read_scan_image(rgbw)
                del img
                # 对焦设置
                self.number = int(scan_info['field_scan']['len_params']['first_focus_number'])
                self.step = float(scan_info['field_scan']['len_params']['first_focus_step'])

                # 扫描中心(系统返回xy相对位置，且xy是反的)
                scan_center_x = (float(self.my_devices_info['microscope']['scan_reference_point_x']) +
                                 float(scan_info['field_scan']['scan_center_y']))
                scan_center_y = (float(self.my_devices_info['microscope']['scan_reference_point_y']) -
                                 float(scan_info['field_scan']['scan_center_x']))
                if ((scan_center_x - float(scan_info['field_scan']['scan_width']) / 2) < 0 or
                        (scan_center_y - float(scan_info['field_scan']['scan_height']) / 2) < 0 or
                        (scan_center_y + float(scan_info['field_scan']['scan_height']) / 2) > 60 or
                        (scan_center_x + float(scan_info['field_scan']['scan_width']) / 2) > 60):
                    self.logger.info('坐标超出范围')
                    return False
                # self.microscope.set_delivery_abs_x(scan_center_x)
                # self.microscope.set_delivery_abs_y(scan_center_y)

                # 推荐高度
                self.microscope.set_delivery_abs_x(float(self.my_devices_info['laser']['laserX']))
                self.microscope.set_delivery_abs_y(float(self.my_devices_info['laser']['laserY']))
                z_start = float(scan_info['field_scan']['len_params']['zstart'])
                self.microscope.set_delivery_abs_z(z_start)
                # 检测玻片平整
                focus_val1 = self.microscope.read_focus_val()
                self.microscope.set_delivery_abs_x(float(self.my_devices_info['laser']['laserX']) - 4)
                self.microscope.set_delivery_abs_y(float(self.my_devices_info['laser']['laserY']) + 4)
                focus_val2 = self.microscope.read_focus_val()
                self.microscope.set_delivery_abs_x(float(self.my_devices_info['laser']['laserX']) + 4)
                self.microscope.set_delivery_abs_y(float(self.my_devices_info['laser']['laserY']) + 4)
                focus_val3 = self.microscope.read_focus_val()
                max_diff, average = self.check_laserz([focus_val1, focus_val2, focus_val3])
                self.logger.info('玻片平整度测量数值：' + str([focus_val1, focus_val2, focus_val3]))
                if max_diff > 0.2:
                    self.requester.update_slide_info(scan_info['slide_id'], 'flatness_fail',
                                                     str('请将玻片平整后再进行扫描'), user_id)
                    self.logger.info('请将玻片平整后再进行扫描')
                    return False
                z_start = (z_start - (float(scan_info['field_scan']['len_params']['laserZ']) - average) -
                           float(scan_info['field_scan']['len_params']['first_focus_step']) * (
                                   float(scan_info['field_scan']['len_params']['first_focus_number']) / 2))
                self.microscope.set_delivery_abs_z(0)
                self.microscope.set_delivery_abs_x(scan_center_x)
                self.microscope.set_delivery_abs_y(scan_center_y)
                h, w = (int(scan_info['field_scan']['len_params']['cropimg']['h']),
                        int(scan_info['field_scan']['len_params']['cropimg']['w']))
                self.Image_Saver.h = h
                self.Image_Saver.w = w
                self.Image_Saver.PixelFormat = scan_info['field_scan']['img_format']
                # 宽高和制作方案相反
                points_xy, points_xy_real, number_x, number_y, x_start_mm, y_start_mm = self.get_route(h, w,
                                                                                                       scan_center_x,
                                                                                                       scan_center_y,
                                                                                                       float(scan_info[
                                                                                                                 'field_scan'][
                                                                                                                 'scan_height']),
                                                                                                       float(scan_info[
                                                                                                                 'field_scan'][
                                                                                                                 'scan_width']),
                                                                                                       calibration)
                if scan_info['field_stitch']:
                    scan_info['field_scan_startX'] = x_start_mm
                    scan_info['field_scan_startY'] = y_start_mm
                    self.Image_Saver.image_stitch_all = Image.new("RGB",
                                                                  (number_x * int(
                                                                      scan_info[
                                                                          'field_stitch_size']),
                                                                   number_y * int(
                                                                       scan_info[
                                                                           'field_stitch_size'])))
                if scan_info['field_scan']['focus_mode'] == "center":
                    Magnification = scan_info['field_scan']['len_name']
                    self.scan_info.emit('正在使用' + str(Magnification) + '扫描')
                    flag = self.Scan_Mode_one(z_start, points_xy, points_xy_real, objective, rgbw, scan_info,
                                              Magnification, number_x, number_y, 0, w, h, user_id, 1, 1, task_id,
                                              'low_scanning')
                    del Magnification
                elif scan_info['field_scan']['focus_mode'] == "gap":
                    Focus_Gap = scan_info['field_scan']['focus_gap'] + 1
                    Magnification = scan_info['field_scan']['len_name']
                    step = float(scan_info['field_scan']['len_params']['focus_step'])
                    number = int(scan_info['field_scan']['len_params']['focus_number'])
                    offset = float(scan_info['field_scan']['len_params']['offset'])
                    HD_focus = scan_info['field_scan']['high_focous']
                    self.scan_info.emit('正在使用' + str(Magnification) + '扫描')
                    flag = self.Scan_Mode_two(z_start, points_xy, points_xy_real, objective, rgbw, scan_info, step,
                                              number,
                                              offset, Magnification, Focus_Gap, number_x, number_y, 0, w, h, user_id, 1,
                                              1, task_id, 'low_scanning', HD_focus)
                self.microscope.set_delivery_abs_z(0)

                if self.run_scan_flag:
                    self.requester.update_slide_info(scan_info['slide_id'], 'low_scanned', '低倍扫描完成', user_id)
                else:
                    # self.requester.update_slide_info(scan_info['slide_id'], 'canceled', '用户取消', user_id)
                    return False

                # 等待拼图完成
                if scan_info['field_stitch']:
                    # 拼图等待60s
                    t_start = time.time()
                    while not self.Image_Saver.image_stitch_flag:
                        time.sleep(0.005)
                        if time.time() - t_start > 30:
                            self.scan_info.emit('等待低倍拼图完成')
                            break
                    self.high_points = self.Image_Saver.high_points
                    self.high_points_px = self.Image_Saver.high_points_px
                    self.Image_Saver.clear_stitch_all()

                    if self.high_points is None or self.high_points_px is None:
                        self.requester.update_slide_info(scan_info['slide_id'], 'view_recommend_fail',
                                                         '没有合格视野推荐', user_id)
                        self.logger.info('高低倍坐标有问题')
                        pass
                    else:
                        self.requester.update_slide_info(scan_info['slide_id'], 'high_scanning',
                                                         '高倍扫描中', user_id)
                        # 使用高倍扫描
                        objective = scan_info['detail_scan']['len_position']
                        # 切换物镜获取对应物镜的光源强度
                        if objective == 1:
                            self.microscope.select_objective_num1()
                        elif objective == 2:
                            self.microscope.select_objective_num2()
                        elif objective == 3:
                            self.microscope.select_objective_num3()
                        elif objective == 4:
                            self.microscope.select_objective_num4()
                        rgbw = scan_info['detail_scan']['len_params']['IlluminationIntensity']
                        calibration = float(scan_info['detail_scan']['len_params']['calibration'])
                        ExposureTime = float(scan_info['detail_scan']['len_params']['ExposureTime'])
                        WB = scan_info['detail_scan']['len_params']['WB']
                        # 设置对应曝光
                        self.scan_camera.set_exposure_time(ExposureTime)
                        self.scan_camera.set_wb_ratios(WB['R'], WB['G'], WB['B'])
                        img = self.read_scan_image(rgbw)
                        # 对焦设置
                        self.number = int(scan_info['detail_scan']['len_params']['first_focus_number'])
                        self.step = float(scan_info['detail_scan']['len_params']['first_focus_step'])

                        # 推荐高度
                        self.microscope.set_delivery_abs_x(float(self.my_devices_info['laser']['laserX']))
                        self.microscope.set_delivery_abs_y(float(self.my_devices_info['laser']['laserY']))
                        z_start = float(scan_info['detail_scan']['len_params']['zstart'])
                        self.logger.info('z轴移动至' + str(z_start))
                        self.microscope.set_delivery_abs_z(z_start)
                        self.logger.info('Z轴移动完毕')
                        focus_val = self.microscope.read_focus_val()
                        z_start = (z_start - (float(scan_info['detail_scan']['len_params']['laserZ']) - focus_val) -
                                   float(scan_info['detail_scan']['len_params']['first_focus_step']) * (
                                           float(scan_info['detail_scan']['len_params']['first_focus_number']) / 2))

                        self.logger.info('玻片平整度高倍测量数值：' + str([focus_val]))
                        self.logger.info('ZSTART' + str([z_start]))
                        self.microscope.set_delivery_abs_z(0)
                        if abs(float(scan_info['detail_scan']['len_params']['laserZ']) - focus_val) > 2:
                            self.logger.info('玻片平整度测量数值error')
                            self.requester.update_slide_info(scan_info['slide_id'], 'flatness_fail',
                                                             '玻片平整度高倍测量数值error', user_id)
                            return False

                        # self.microscope.set_delivery_abs_x(float(scan_info['detail_scan']['scan_center_x']))
                        # self.microscope.set_delivery_abs_y(float(scan_info['detail_scan']['scan_center_y']))
                        h, w = (int(scan_info['detail_scan']['len_params']['cropimg']['h']),
                                int(scan_info['detail_scan']['len_params']['cropimg']['w']))
                        offsetX, offsetY = scan_info['detail_scan']['len_params']['offsetX'], \
                            scan_info['detail_scan']['len_params']['offsetY']
                        self.Image_Saver.h = h
                        self.Image_Saver.w = w
                        self.Image_Saver.PixelFormat = scan_info['detail_scan']['img_format']
                        group = 1
                        max_group = len(self.high_points)
                        for point, point_pix in zip(self.high_points, self.high_points_px):
                            self.number = int(scan_info['detail_scan']['len_params']['first_focus_number'])
                            self.step = float(scan_info['detail_scan']['len_params']['first_focus_step'])
                            point_x = point[0] + offsetX
                            point_y = point[1] + offsetY
                            if point_x > 60 or point_y > 60:
                                self.logger.info('推荐视野中心点超出界限')
                                return False

                            region_w = (scan_info['detail_scan']['field_area_matrix'] *
                                        calibration * w)
                            region_h = (scan_info['detail_scan']['field_area_matrix'] *
                                        calibration * h)
                            points_xy, points_xy_real, number_x, number_y, x_start_mm, y_start_mm = self.get_route(h, w,
                                                                                                                   float(
                                                                                                                       point_x),
                                                                                                                   float(
                                                                                                                       point_y),
                                                                                                                   float(
                                                                                                                       region_w),
                                                                                                                   float(
                                                                                                                       region_h),
                                                                                                                   calibration)
                            if scan_info['detail_scan']['focus_mode'] == "center":
                                Magnification = scan_info['detail_scan']['len_name']
                                self.scan_info.emit('正在使用' + str(Magnification) + '扫描')
                                flag = self.Scan_Mode_one(z_start, points_xy, points_xy_real, objective, rgbw,
                                                          scan_info,
                                                          Magnification, number_x, number_y, group, w, h, user_id,
                                                          group, max_group, task_id, 'high_scanning')
                                del Magnification
                            elif scan_info['detail_scan']['focus_mode'] == "gap":
                                Focus_Gap = scan_info['detail_scan']['focus_gap'] + 1
                                Magnification = scan_info['detail_scan']['len_name']
                                step = float(scan_info['detail_scan']['len_params']['focus_step'])
                                number = int(scan_info['detail_scan']['len_params']['focus_number'])
                                offset = float(scan_info['detail_scan']['len_params']['offset'])
                                HD_focus = scan_info['detail_scan']['high_focous']
                                self.scan_info.emit('正在使用' + str(Magnification) + '扫描')
                                flag = self.Scan_Mode_two(z_start, points_xy, points_xy_real, objective, rgbw,
                                                          scan_info,
                                                          step,
                                                          number,
                                                          offset, Magnification, Focus_Gap, number_x, number_y, group,
                                                          w, h, user_id, group, max_group, task_id, 'high_scanning',
                                                          HD_focus)
                            if self.run_scan_flag:
                                pass
                            else:
                                break
                            group = group + 1
                        self.high_points = None
                        del group
                del rgbw
                del calibration
                del ExposureTime
                del WB
                del z_start
                del h
                del w
                del points_xy
                del points_xy_real
                del number_x
                del number_y
                del x_start_mm
                del y_start_mm
                del scan_center_x
                del scan_center_y
                del focus_val1
                del focus_val2
                del focus_val3
                if self.run_scan_flag:
                    self.requester.update_slide_info(scan_info['slide_id'], 'high_scanned',
                                                     '高倍扫描完成', user_id)
                self.microscope.set_delivery_abs_z(0)


            else:
                self.requester.update_slide_info(scan_info['slide_id'], 'scanning', '扫描中(没有高低倍配合)', user_id)
                # 指定扫描
                objective = scan_info['scan']['len_position']
                # 切换物镜获取对应物镜的光源强度
                if objective == 1:
                    self.microscope.select_objective_num1()
                elif objective == 2:
                    self.microscope.select_objective_num2()
                elif objective == 3:
                    self.microscope.select_objective_num3()
                elif objective == 4:
                    self.microscope.select_objective_num4()

                rgbw = scan_info['scan']['len_params']['IlluminationIntensity']
                calibration = float(scan_info['scan']['len_params']['calibration'])
                ExposureTime = float(scan_info['scan']['len_params']['ExposureTime'])
                WB = scan_info['scan']['len_params']['WB']
                # 设置对应曝光
                self.scan_camera.set_exposure_time(ExposureTime)
                self.scan_camera.set_wb_ratios(WB['R'], WB['G'], WB['B'])
                img = self.read_scan_image(rgbw)
                del img
                # 对焦设置
                self.number = int(scan_info['scan']['len_params']['first_focus_number'])
                self.step = float(scan_info['scan']['len_params']['first_focus_step'])

                # 扫描中心
                # 扫描中心(系统返回xy相对位置，且xy是反的)
                scan_center_x = (float(self.my_devices_info['microscope']['scan_reference_point_x']) +
                                 float(scan_info['scan']['scan_center_y']))
                scan_center_y = (float(self.my_devices_info['microscope']['scan_reference_point_y']) -
                                 float(scan_info['scan']['scan_center_x']))
                if ((scan_center_x - float(scan_info['scan']['scan_width']) / 2) < 0 or
                        (scan_center_y - float(scan_info['scan']['scan_height']) / 2) < 0 or
                        (scan_center_y + float(scan_info['scan']['scan_height']) / 2) > 60 or
                        (scan_center_x + float(scan_info['scan']['scan_width']) / 2) > 60):
                    self.logger.info('坐标超出范围')
                    return False
                # self.microscope.set_delivery_abs_x(scan_center_x)
                # self.microscope.set_delivery_abs_y(scan_center_y)
                # 推荐高度
                self.microscope.set_delivery_abs_x(float(self.my_devices_info['laser']['laserX']))
                self.microscope.set_delivery_abs_y(float(self.my_devices_info['laser']['laserY']))
                z_start = float(scan_info['scan']['len_params']['zstart'])
                self.microscope.set_delivery_abs_z(z_start)
                # 检测玻片平整
                focus_val1 = self.microscope.read_focus_val()
                self.microscope.set_delivery_abs_x(float(self.my_devices_info['laser']['laserX']) - 4)
                self.microscope.set_delivery_abs_y(float(self.my_devices_info['laser']['laserY']) + 4)
                focus_val2 = self.microscope.read_focus_val()
                self.microscope.set_delivery_abs_x(float(self.my_devices_info['laser']['laserX']) + 4)
                self.microscope.set_delivery_abs_y(float(self.my_devices_info['laser']['laserY']) + 4)
                focus_val3 = self.microscope.read_focus_val()

                max_diff, average = self.check_laserz([focus_val1, focus_val2, focus_val3])
                self.logger.info('玻片平整度测量数值：' + str([focus_val1, focus_val2, focus_val3]))
                if max_diff > 0.2:
                    self.requester.update_slide_info(scan_info['slide_id'], 'error',
                                                     str('请将玻片平整后再进行扫描'), user_id)
                    self.logger.info('请将玻片平整后再进行扫描')
                    return False
                z_start = (z_start - (float(scan_info['scan']['len_params']['laserZ']) - average) -
                           float(scan_info['scan']['len_params']['first_focus_step']) * (
                                   float(scan_info['scan']['len_params']['first_focus_number']) / 2))
                self.microscope.set_delivery_abs_z(0)
                self.microscope.set_delivery_abs_x(scan_center_x)
                self.microscope.set_delivery_abs_y(scan_center_y)

                h, w = (int(scan_info['scan']['len_params']['cropimg']['h']),
                        int(scan_info['scan']['len_params']['cropimg']['w']))
                self.Image_Saver.h = h
                self.Image_Saver.w = w
                self.Image_Saver.PixelFormat = scan_info['scan']['img_format']

                points_xy, points_xy_real, number_x, number_y, x_start_mm, y_start_mm = self.get_route(h, w,
                                                                                                       scan_center_x,
                                                                                                       scan_center_y,
                                                                                                       float(scan_info[
                                                                                                                 'scan'][
                                                                                                                 'scan_height']),
                                                                                                       float(scan_info[
                                                                                                                 'scan'][
                                                                                                                 'scan_width']),
                                                                                                       calibration)
                if scan_info['field_stitch']:
                    scan_info['field_scan_startX'] = x_start_mm
                    scan_info['field_scan_startY'] = y_start_mm
                    self.Image_Saver.image_stitch_all = Image.new("RGB",
                                                                  (number_x * int(
                                                                      scan_info[
                                                                          'field_stitch_size']),
                                                                   number_y * int(
                                                                       scan_info[
                                                                           'field_stitch_size'])))
                if scan_info['scan']['focus_mode'] == "center":
                    Magnification = scan_info['scan']['len_name']
                    self.scan_info.emit('正在使用' + str(Magnification) + '扫描')
                    flag = self.Scan_Mode_one(z_start, points_xy, points_xy_real, objective, rgbw, scan_info,
                                              Magnification, number_x, number_y, 0, w, h, user_id, 1, 1, task_id,
                                              'scanning')
                    del Magnification
                elif scan_info['scan']['focus_mode'] == "gap":
                    Focus_Gap = scan_info['scan']['focus_gap'] + 1
                    Magnification = scan_info['scan']['len_name']
                    step = float(scan_info['scan']['len_params']['focus_step'])
                    number = int(scan_info['scan']['len_params']['focus_number'])
                    offset = float(scan_info['scan']['len_params']['offset'])
                    HD_focus = scan_info['scan']['high_focous']
                    self.scan_info.emit('正在使用' + str(Magnification) + '扫描')
                    flag = self.Scan_Mode_two(z_start, points_xy, points_xy_real, objective, rgbw, scan_info, step,
                                              number,
                                              offset, Magnification, Focus_Gap, number_x, number_y, 0, w, h, user_id, 1,
                                              1, task_id, 'scanning', HD_focus)
                    del Magnification
                    del Focus_Gap
                    del step
                    del number
                    del offset
                if self.run_scan_flag:
                    self.requester.update_slide_info(scan_info['slide_id'], 'scanned', '扫描完成(没有高低倍配合)',
                                                     user_id)
                self.microscope.set_delivery_abs_z(0)

                del objective
                del rgbw
                del calibration
                del ExposureTime
                del WB
                del z_start
                del h
                del w
                del points_xy
                del points_xy_real
                del number_x
                del number_y
                del scan_info
                del x_start_mm
                del y_start_mm
                del scan_center_x
                del scan_center_y
                del focus_val1
                del focus_val2
                del focus_val3

            return flag
        except Exception as e:
            self.logger.info('扫描失败' + str(e))
            self.microscope.set_delivery_abs_z(0)
            self.requester.update_slide_info(scan_info['slide_id'], 'error',
                                             str(e), user_id)
            return False

    def Scan_Mode_one(self, zpos_start, points_xy, points_xy_real, objective, rgbw, scan_info, Magnification, number_x,
                      number_y, view_filed_group, crop_w, crop_h, user_id, scan_number, max_scan_number, task_id,
                      scan_info_str):
        if self.is_running:
            pass
        else:
            self.requester.update_slide_info(scan_info['slide_id'], 'pause', '用户暂停', user_id)
            while not self.is_running:
                time.sleep(0.1)
            self.requester.update_task_info(task_id, 'scanning', '扫描中', user_id)
            if scan_info_str == 'scanning':
                self.requester.update_slide_info(scan_info['slide_id'], 'scanning', '扫描中(没有高低倍配合)', user_id)
            elif scan_info_str == 'low_scanning':
                self.requester.update_slide_info(scan_info['slide_id'], 'low_scanning', '低倍扫描中', user_id)
            elif scan_info_str == 'high_scanning':
                self.requester.update_slide_info(scan_info['slide_id'], 'high_scanning', '高倍扫描中', user_id)

        if self.run_scan_flag:
            pass
        else:
            self.requester.update_slide_info(scan_info['slide_id'], 'canceled', '用户取消', user_id)
            return False
        Img_Number = 1
        zpos = zpos_start
        zpos, img, focus_imgs_list, focus_imgs_best_index = self.AutofocusWorker(zpos_start, True, rgbw, False)
        self.microscope.set_delivery_abs_z(zpos)
        for point, Point_real in zip(points_xy, points_xy_real):
            if self.is_running:
                pass
            else:
                self.requester.update_slide_info(scan_info['slide_id'], 'pause', '用户暂停', user_id)
                while not self.is_running:
                    time.sleep(0.1)
                self.requester.update_task_info(task_id, 'scanning', '扫描中', user_id)
                if scan_info_str == 'scanning':
                    self.requester.update_slide_info(scan_info['slide_id'], 'scanning', '扫描中(没有高低倍配合)',
                                                     user_id)
                elif scan_info_str == 'low_scanning':
                    self.requester.update_slide_info(scan_info['slide_id'], 'low_scanning', '低倍扫描中', user_id)
                elif scan_info_str == 'high_scanning':
                    self.requester.update_slide_info(scan_info['slide_id'], 'high_scanning', '高倍扫描中', user_id)
            if self.run_scan_flag:
                pass
            else:
                self.requester.update_slide_info(scan_info['slide_id'], 'canceled', '用户取消', user_id)
                return False
            self.microscope.set_delivery_abs_x(Point_real[0])
            self.microscope.set_delivery_abs_y(Point_real[1])
            img = self.read_scan_image(rgbw)
            self.scan_img.emit(img, Img_Number, point, True, number_x, number_y, crop_w, crop_h)
            if Img_Number == len(points_xy_real) and scan_number == max_scan_number:
                is_end = True
            else:
                is_end = False
            if view_filed_group == 0:
                self.Image_Saver.enqueue(Img_Number, img, str(Magnification),
                                         False, [point[0] * int(scan_info['field_stitch_size']),
                                                 point[1] * int(scan_info['field_stitch_size']),
                                                 int(scan_info['field_stitch_size']),
                                                 int(scan_info['field_stitch_size'])], is_end, view_filed_group,
                                         scan_info, [], 0)
            else:
                w_region = float(scan_info['detail_scan']['len_params']['calibration']) * crop_w
                h_region = float(scan_info['detail_scan']['len_params']['calibration']) * crop_h
                x_left_px = int((abs(scan_info['field_scan_startX'] - (
                        Point_real[0] - scan_info['detail_scan']['len_params']['offsetX']) - w_region / 2) / float(
                    scan_info['field_scan']['len_params']['calibration'])) / (
                                        int(scan_info['field_scan']['len_params']['cropimg']['w']) / scan_info[
                                    'field_stitch_size']))
                y_left_px = int((abs(scan_info['field_scan_startY'] - (
                        Point_real[1] - scan_info['detail_scan']['len_params']['offsetY']) - h_region / 2) / float(
                    scan_info['field_scan']['len_params']['calibration'])) / (
                                        int(scan_info['field_scan']['len_params']['cropimg']['h']) / scan_info[
                                    'field_stitch_size']))
                w_region_px = int((int(scan_info['field_scan']['len_params']['cropimg']['w']) * (
                        float(scan_info['detail_scan']['len_params']['calibration']) / float(
                    scan_info['field_scan']['len_params']['calibration']))) / (
                                          int(scan_info['field_scan']['len_params']['cropimg']['w']) / scan_info[
                                      'field_stitch_size']))
                h_region_px = int((int(scan_info['field_scan']['len_params']['cropimg']['h']) * (
                        float(scan_info['detail_scan']['len_params']['calibration']) / float(
                    scan_info['field_scan']['len_params']['calibration']))) / (
                                          int(scan_info['field_scan']['len_params']['cropimg']['h']) / scan_info[
                                      'field_stitch_size']))

                self.Image_Saver.enqueue(Img_Number, img, str(Magnification),
                                         False, [x_left_px, y_left_px,
                                                 w_region_px, h_region_px], is_end, view_filed_group, scan_info, [], 0)
                del w_region
                del h_region
                del x_left_px
                del y_left_px
                del w_region_px
                del h_region_px
            del img
            self.progress_signal.emit(int(Img_Number * 100 / len(points_xy_real)))
            Img_Number = Img_Number + 1
        del Img_Number
        del zpos
        del point
        del Point_real
        del zpos_start
        del points_xy
        del points_xy_real
        del objective
        del rgbw
        del scan_info
        del Magnification
        del number_x
        del number_y
        del is_end
        del crop_w
        del crop_h
        del focus_imgs_list
        return True

    def Scan_Mode_two(self, zpos_start, points_xy, points_xy_real, objective, rgbw, scan_info, step, number, offset,
                      Magnification, Focus_Gap, number_x, number_y, view_filed_group, crop_w, crop_h, user_id,
                      scan_number, max_scan_number, task_id,
                      scan_info_str, HD_focus):
        Img_Number = 1
        zpos = zpos_start
        for point, Point_real in zip(points_xy, points_xy_real):
            if self.is_running:
                pass
            else:
                self.requester.update_slide_info(scan_info['slide_id'], 'pause', '用户暂停', user_id)
                while not self.is_running:
                    time.sleep(0.1)
                self.requester.update_task_info(task_id, 'scanning', '扫描中', user_id)
                if scan_info_str == 'scanning':
                    self.requester.update_slide_info(scan_info['slide_id'], 'scanning', '扫描中(没有高低倍配合)',
                                                     user_id)
                elif scan_info_str == 'low_scanning':
                    self.requester.update_slide_info(scan_info['slide_id'], 'low_scanning', '低倍扫描中', user_id)
                elif scan_info_str == 'high_scanning':
                    self.requester.update_slide_info(scan_info['slide_id'], 'high_scanning', '高倍扫描中', user_id)
            if self.run_scan_flag:
                pass
            else:
                self.requester.update_slide_info(scan_info['slide_id'], 'canceled', '用户取消', user_id)
                return False
            self.microscope.set_delivery_abs_x(Point_real[0])
            self.microscope.set_delivery_abs_y(Point_real[1])
            focus_imgs_list = []
            focus_imgs_best_index = 0
            if Img_Number == 1:
                zpos, img, focus_imgs_list, focus_imgs_best_index = self.AutofocusWorker(zpos, True, rgbw, False)
                self.step = step
                self.number = number
                zpos, img, focus_imgs_list, focus_imgs_best_index = self.AutofocusWorker(zpos - offset, True, rgbw,
                                                                                         False)
            elif Img_Number % Focus_Gap == 0:
                zpos, img, focus_imgs_list, focus_imgs_best_index = self.AutofocusWorker(zpos - offset, True, rgbw,
                                                                                         False)
            else:
                self.microscope.set_delivery_abs_z(zpos)
                img = self.read_scan_image(rgbw)
            img_resize = cv2.resize(img, (640, 640))
            self.scan_img.emit(img_resize, Img_Number, point, False, number_x, number_y, crop_w, crop_h)
            del img_resize
            if Img_Number == len(points_xy_real) and scan_number == max_scan_number:
                is_end = True
            else:
                is_end = False

            if view_filed_group == 0:
                if HD_focus:
                    if len(focus_imgs_list) > 0:
                        pass
                    else:
                        focus_imgs_list = [img]
                else:
                    focus_imgs_list = []

                self.Image_Saver.enqueue(Img_Number, img, str(Magnification),
                                         False, [point[0] * int(scan_info['field_stitch_size']),
                                                 point[1] * int(scan_info['field_stitch_size']),
                                                 int(scan_info['field_stitch_size']),
                                                 int(scan_info['field_stitch_size'])], is_end, view_filed_group,
                                         scan_info, focus_imgs_list, focus_imgs_best_index)
            else:
                if HD_focus:
                    if len(focus_imgs_list) > 0:
                        pass
                    else:
                        focus_imgs_list = [img]
                else:
                    focus_imgs_list = []
                w_region = float(scan_info['detail_scan']['len_params']['calibration']) * crop_w
                h_region = float(scan_info['detail_scan']['len_params']['calibration']) * crop_h
                x_left_px = int((abs(scan_info['field_scan_startX'] - (
                        Point_real[0] - scan_info['detail_scan']['len_params']['offsetX']) - w_region / 2) / float(
                    scan_info['field_scan']['len_params']['calibration'])) / (
                                        int(scan_info['field_scan']['len_params']['cropimg']['w']) / scan_info[
                                    'field_stitch_size']))
                y_left_px = int((abs(scan_info['field_scan_startY'] - (
                        Point_real[1] - scan_info['detail_scan']['len_params']['offsetY']) - h_region / 2) / float(
                    scan_info['field_scan']['len_params']['calibration'])) / (
                                        int(scan_info['field_scan']['len_params']['cropimg']['h']) / scan_info[
                                    'field_stitch_size']))
                w_region_px = int((int(scan_info['field_scan']['len_params']['cropimg']['w']) * (
                        float(scan_info['detail_scan']['len_params']['calibration']) / float(
                    scan_info['field_scan']['len_params']['calibration']))) / (
                                          int(scan_info['field_scan']['len_params']['cropimg']['w']) / scan_info[
                                      'field_stitch_size']))
                h_region_px = int((int(scan_info['field_scan']['len_params']['cropimg']['h']) * (
                        float(scan_info['detail_scan']['len_params']['calibration']) / float(
                    scan_info['field_scan']['len_params']['calibration']))) / (
                                          int(scan_info['field_scan']['len_params']['cropimg']['h']) / scan_info[
                                      'field_stitch_size']))

                self.Image_Saver.enqueue(Img_Number, img, str(Magnification),
                                         False, [x_left_px, y_left_px,
                                                 w_region_px, h_region_px], is_end, view_filed_group, scan_info,
                                         focus_imgs_list,focus_imgs_best_index)
                del w_region
                del h_region
                del x_left_px
                del y_left_px
                del w_region_px
                del h_region_px
            img = None
            self.progress_signal.emit(int(Img_Number * 100 / len(points_xy_real)))
            Img_Number = Img_Number + 1
        del Img_Number
        del zpos
        del point
        del Point_real
        del zpos_start
        del points_xy
        del points_xy_real
        del objective
        del rgbw
        del scan_info
        del Magnification
        del number_x
        del number_y
        del is_end
        del crop_w
        del crop_h
        return True
