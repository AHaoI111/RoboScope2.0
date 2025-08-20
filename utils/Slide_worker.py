import copy
import os
import threading
import time

import numpy as np
from PySide6 import QtCore
from PySide6.QtCore import Signal

from utils import Scan
import cv2
from datetime import datetime


def get_year_month_day():
    # 获取当前系统时间
    current_time = datetime.now()
    # 格式化时间显示
    year = current_time.strftime("%Y")
    month = current_time.strftime("%m")
    day = current_time.strftime("%d")
    return year, month, day


class worker(QtCore.QObject):
    worker_Progress = Signal(list)
    worker_info = Signal(list)
    finished = Signal(list, str)
    display_slide_image = Signal(np.ndarray)

    def __init__(self, microscope, scan_camera, ocr_camera, logger, my_devices_info, disconnect, requester):
        super().__init__()
        self.slides = [0] * 24
        self.i = None
        # self.t = None
        self.requester = requester
        self.scan_camera = scan_camera
        self.ocr_camera = ocr_camera
        self.microscope = microscope
        self.ScanManager = Scan.ScanManager(self.microscope, self.scan_camera, self.ocr_camera, my_devices_info, logger,
                                            requester)
        self.run_flag = True
        self.is_running = False
        self.logger = logger
        self.my_devices_info = my_devices_info
        self.disconnect = disconnect

    def pause_work(self):
        # 暂停
        self.is_running = False
        self.run_flag = True

        self.ScanManager.is_running = False
        self.ScanManager.run_scan_flag = True

    def recover_work(self):
        self.is_running = True
        self.run_flag = True

        self.ScanManager.is_running = True
        self.ScanManager.run_scan_flag = True

    def stop_work(self):

        # 停止

        self.run_flag = False
        self.is_running = True

        self.ScanManager.run_scan_flag = False
        self.ScanManager.is_running = True

        # if self.t is not None:
        #     self.t.join()
        #     self.t = None

    def read_slide_number(self):
        # 下降
        # 数片
        # 获得片数和对应位置
        # slides = [0] * 24
        slides = self.microscope.read_slide_nums(self.my_devices_info['loader']['readslide_start'],
                                                 self.my_devices_info['loader']['readslide_end'])
        return slides

    def _apply_ocr_processing(self, image, rotate, mask_label):
        """应用OCR预处理"""
        try:
            if image is None:
                return None, None

            processed_img = image.copy()

            # 应用旋转
            if rotate:
                rotate_image = cv2.rotate(processed_img, cv2.ROTATE_90_CLOCKWISE)
            else:
                rotate_image = image
            # 应用掩码
            processed_img = rotate_image.copy()
            if mask_label == "left":
                cv2.rectangle(processed_img, (0, 0),
                              (processed_img.shape[1] // 2, processed_img.shape[0]),
                              (0, 0, 0), cv2.FILLED)
            elif mask_label == "right":
                cv2.rectangle(processed_img, (processed_img.shape[1] // 2, 0),
                              (processed_img.shape[1], processed_img.shape[0]),
                              (0, 0, 0), cv2.FILLED)

            return rotate_image, processed_img
        except Exception as e:
            self.logger.error(f"OCR processing error: {str(e)}")
            return image, image

    def get_ocr_text_safe(self, ocr_text, position):
        if position is None or position < 0 or len(ocr_text) <= position:
            return ''
        return ocr_text[position]

    def process_slide(self, number, plan_data, task_id, slide_save_path_date, is_last_slide, user_id):
        # 移动该玻片到交接位置
        self.microscope.set_delivery_abs_lz(float(self.my_devices_info['loader']['z'])
                                            - (float(self.my_devices_info['loader']['slidegap']) * number))
        # 载物台移动接片
        self.microscope.set_delivery_abs_x(float(self.my_devices_info['microscope']['slidextransfer']))
        self.microscope.set_delivery_abs_y(float(self.my_devices_info['microscope']['slideytransfer']))
        self.microscope.set_delivery_abs_z(float(self.my_devices_info['microscope']['slideztransfer']))
        # 推片
        self.microscope.set_delivery_abs_ly(float(self.my_devices_info['loader']['slidepushly']))
        # y推回
        self.microscope.set_delivery_abs_y(float(self.my_devices_info['microscope']['ocrytransfer']))
        self.microscope.light_ocr_ctrl(1)
        ocr_img = self.ocr_camera.read_image()
        self.microscope.light_ocr_ctrl(0)
        # 载物台缩回
        self.microscope.set_delivery_abs_x(float(self.my_devices_info['microscope']['scan_reference_point_x']))
        self.microscope.set_delivery_abs_y(float(self.my_devices_info['microscope']['scan_reference_point_y']))
        # 回1mm
        self.microscope.set_delivery_abs_ly(float(self.my_devices_info['loader']['slidepushly']) - 1)

        ocr_flag = False
        scaninfo = None
        rotate_img = None
        try:
            rotate_image = plan_data['rotate_image']
            mask_label = plan_data['mask_label']
            rotate_img, processed_img = self._apply_ocr_processing(ocr_img, rotate_image, mask_label)
            # 判断是否需要ocr识别
            if plan_data['label_model_id'] is None:
                self.logger.info("未选择OCR模型")
                if rotate_img is None:
                    ocr_flag = False
                else:
                    # 申请slide——id
                    slide_id = self.requester.create_slide_id(task_id, slide_save_path_date, number + 1, is_last_slide)
                    self.logger.info("申请slide_id: " + str(slide_id))
                    # 获取扫描流程
                    scaninfo = self.requester.get_scan_info(plan_data['flows'][0])

                    ocr_flag = True
                    directory_path = (
                            plan_data['storage_path'] + slide_save_path_date + '/' + task_id + '/' + slide_id + '/')
                    # 检查目录是否存在
                    if not os.path.exists(directory_path):
                        # 目录不存在，创建目录
                        os.makedirs(directory_path)
                    name_label_img = slide_id + "_label.jpg"
                    encoded_stitch_image = cv2.imencode('.jpg', ocr_img, [cv2.IMWRITE_JPEG_QUALITY, 100])[
                        1]
                    encoded_stitch_image.tofile(os.path.join(directory_path, name_label_img))

                    scaninfo['slide_id'] = slide_id
                    scaninfo['save_path'] = directory_path
                    scaninfo['save_path_date'] = slide_save_path_date

                    data = self.requester.create_slide_label_flow(slide_id, plan_data['flows'][0], name_label_img, '',
                                                                  '',
                                                                  '',
                                                                  '', '')
            else:
                if rotate_img is None:
                    ocr_flag = False
                else:
                    self.logger.info("使用OCR模型")
                    # 识别ocr
                    sample_category_label_position = int(plan_data['sample_category_label_position'])
                    preparation_method_label_position = int(plan_data['preparation_method_label_position'])
                    sample_no_label_position = int(plan_data['sample_no_label_position'])
                    name_label_position = int(plan_data['name_label_position'])
                    patient_no_label_position = int(plan_data['patient_no_label_position'])
                    ocr_text = self.requester.send_ocr_label_image(processed_img, plan_data['label_model_id'])
                    if ocr_text is None:
                        self.logger.info("识别结果为空")
                    else:
                        self.logger.info("识别结果：" + str(ocr_text))
                    # 判断是否需要匹配ocr信息
                    if len(plan_data['tags']) > 0:
                        if len(ocr_text) >= sample_category_label_position + 1:
                            sample_text = ocr_text[sample_category_label_position]
                            match_flag = False
                            for index, tag in enumerate(plan_data['tags']):
                                if match_flag:
                                    break
                                split_string = tag.split(',')
                                for tag_item in split_string:
                                    if tag_item == sample_text:
                                        slide_id = self.requester.create_slide_id(task_id, slide_save_path_date,
                                                                                  number + 1, is_last_slide)
                                        self.logger.info("申请slide_id: " + slide_id)
                                        # 获取扫描流程
                                        scaninfo = self.requester.get_scan_info(plan_data['flows'][index])
                                        self.logger.info("匹配到的ocr：" + str(sample_text))
                                        self.logger.info("匹配到的flows index：" + str(index))
                                        scaninfo['slide_id'] = slide_id
                                        ocr_flag = True
                                        match_flag = True
                                        directory_path = (
                                                plan_data['storage_path'] + slide_save_path_date + '/' + task_id + '/' +
                                                scaninfo[
                                                    'slide_id'] + '/')
                                        # 检查目录是否存在
                                        if not os.path.exists(directory_path):
                                            # 目录不存在，创建目录
                                            os.makedirs(directory_path)
                                        name_label_img = slide_id + "_label.jpg"
                                        encoded_stitch_image = \
                                            cv2.imencode('.jpg', ocr_img, [cv2.IMWRITE_JPEG_QUALITY, 100])[
                                                1]
                                        encoded_stitch_image.tofile(os.path.join(directory_path, name_label_img))
                                        scaninfo['save_path'] = directory_path
                                        scaninfo['save_path_date'] = slide_save_path_date
                                        sample_category_label_position_str = self.get_ocr_text_safe(ocr_text,
                                                                                                    sample_category_label_position)
                                        preparation_method_label_position_str = self.get_ocr_text_safe(ocr_text,
                                                                                                       preparation_method_label_position)
                                        sample_no_label_position_str = self.get_ocr_text_safe(ocr_text,
                                                                                              sample_no_label_position)
                                        name_label_position_str = self.get_ocr_text_safe(ocr_text, name_label_position)
                                        patient_no_label_position_str = self.get_ocr_text_safe(ocr_text,
                                                                                               patient_no_label_position)
                                        data = self.requester.create_slide_label_flow(slide_id,
                                                                                      plan_data['flows'][index],
                                                                                      name_label_img,
                                                                                      name_label_position_str,
                                                                                      sample_no_label_position_str,
                                                                                      patient_no_label_position_str,
                                                                                      sample_category_label_position_str,
                                                                                      preparation_method_label_position_str)
                                        break
                                    else:
                                        ocr_flag = False
                        else:
                            ocr_flag = False
                    else:
                        # 申请slide——id
                        slide_id = self.requester.create_slide_id(task_id, slide_save_path_date, number + 1,
                                                                  is_last_slide)
                        self.logger.info("申请slide_id: " + slide_id)
                        scaninfo = self.requester.get_scan_info(plan_data['flows'][0])
                        scaninfo['slide_id'] = slide_id
                        ocr_flag = True
                        directory_path = (
                                plan_data['storage_path'] + slide_save_path_date + '/' + task_id + '/' + scaninfo[
                            'slide_id'] + '/')
                        # 检查目录是否存在
                        if not os.path.exists(directory_path):
                            # 目录不存在，创建目录
                            os.makedirs(directory_path)
                        name_label_img = slide_id + "_label.jpg"
                        encoded_stitch_image = cv2.imencode('.jpg', ocr_img, [cv2.IMWRITE_JPEG_QUALITY, 100])[
                            1]
                        encoded_stitch_image.tofile(os.path.join(directory_path, name_label_img))
                        scaninfo['save_path'] = directory_path
                        scaninfo['save_path_date'] = slide_save_path_date
                        sample_category_label_position_str = self.get_ocr_text_safe(ocr_text,
                                                                                    sample_category_label_position)
                        preparation_method_label_position_str = self.get_ocr_text_safe(ocr_text,
                                                                                       preparation_method_label_position)
                        sample_no_label_position_str = self.get_ocr_text_safe(ocr_text,
                                                                              sample_no_label_position)
                        name_label_position_str = self.get_ocr_text_safe(ocr_text, name_label_position)
                        patient_no_label_position_str = self.get_ocr_text_safe(ocr_text,
                                                                               patient_no_label_position)
                        data = self.requester.create_slide_label_flow(slide_id, plan_data['flows'][0],
                                                                      name_label_img,
                                                                      name_label_position_str,
                                                                      sample_no_label_position_str,
                                                                      patient_no_label_position_str,
                                                                      sample_category_label_position_str,
                                                                      preparation_method_label_position_str)
        except Exception as e:
            self.logger.info(str(e))

        try:
            if ocr_flag and scaninfo and scaninfo['slide_id'] is not None:
                ocr_img = cv2.rotate(ocr_img, cv2.ROTATE_90_CLOCKWISE)
                self.display_slide_image.emit(ocr_img)
                process_flag = True
                # 开始扫描
                scan_flag = self.ScanManager.run_scan(scaninfo, user_id,task_id)
                if scan_flag:
                    self.logger.info('扫描完成')
                else:
                    # self.run_flag = False
                    # self.is_running = True
                    # self.ScanManager.run_scan_flag = False
                    # self.ScanManager.is_running = True
                    process_flag = False

            else:
                process_flag = False
        except Exception as e:
            self.logger.info(str(e))
        self.microscope.set_delivery_abs_z(float(self.my_devices_info['microscope']['slideztransfer']))
        self.microscope.set_delivery_abs_y(float(self.my_devices_info['microscope']['slideytransfer']))
        self.microscope.set_delivery_abs_x(float(self.my_devices_info['microscope']['slidextransfer']))

        # 扫描完成送片
        self.microscope.set_delivery_abs_ly(float(self.my_devices_info['loader']['slidepullly']))
        self.microscope.set_delivery_abs_ly(float(self.my_devices_info['loader']['slidepullly_offset']))

        del rotate_img
        del ocr_img
        del processed_img

        return process_flag

    def run(self, plan_data, task_id, slides, user_id):
        self.run_flag = True
        self.is_running = True
        self.ScanManager.run_scan_flag = True
        self.ScanManager.is_running = True
        # 分配扫描参数

        # 开始扫描整个玻片仓任务
        count_ones = slides.count(1)
        if count_ones > 0:
            # 检测上次未扫描完成的需续扫
            self.logger.info("检测到用户使用继续上一次扫描")
            self.slides = slides
            self.requester.update_task_info(task_id, 'rescanning', '扫描中', user_id)
        else:
            self.logger.info("自动数玻片")
            self.slides = self.read_slide_number()
            self.requester.update_task_info(task_id, 'scanning', '扫描中', user_id)

        self.logger.info(str(self.slides))
        count_ones = self.slides.count(1)
        self.requester.create_slide_count(task_id, count_ones)

        year, month, day = get_year_month_day()
        slide_save_path_date = '/' + year + '/' + month + '/' + day + '/'
        self.worker_Progress.emit(self.slides)
        self.worker_info.emit(self.slides)
        for i, slide in enumerate(self.slides, start=0):  # i 从 1 开始
            if self.is_running:
                pass
            else:
                while not self.is_running:
                    time.sleep(0.1)
            if not self.run_flag:
                self.logger.info('停止扫描')
                break
            self.i = i + 1
            self.worker_Progress.emit(self.slides)
            self.worker_info.emit(self.slides)
            if slide == 1:
                self.logger.info("Slide {} is running".format(i + 1))  # 记录第 i 片玻片正在运行
                self.slides[i] = 4
                self.worker_Progress.emit(self.slides)
                self.worker_info.emit(self.slides)
                count_ones = self.slides.count(1)
                if count_ones > 0:
                    is_last_slide = False
                else:
                    is_last_slide = True
                process_flag = self.process_slide(i, plan_data, task_id,
                                                  slide_save_path_date, is_last_slide,
                                                  user_id)  # 假设 process_slide 接受玻片编号
                if process_flag:
                    self.slides[i] = 2
                    self.worker_Progress.emit(self.slides)
                else:
                    self.slides[i] = 3
                    self.worker_Progress.emit(self.slides)
                if not self.run_flag:
                    # 停止的算没扫完
                    self.slides[i] = 1

                self.worker_Progress.emit(self.slides)
                self.worker_info.emit(self.slides)
            else:
                self.logger.info("Slide {} does not exist".format(i + 1))  # 记录第 i 片玻片不存在
        self.worker_Progress.emit(self.slides)
        self.worker_info.emit(self.slides)
        # 扫描完毕
        if self.run_flag:
            # 正常完成
            self.logger.info('任务扫描完成，taskid:' + str(task_id))
            self.slides = [0] * 24
        else:
            # 异常退出
            self.logger.info('任务扫描停止，taskid:' + str(task_id))
        self.microscope.motor_reset("z")
        self.microscope.motor_reset("w")
        self.microscope.motor_reset("y")
        self.microscope.motor_reset("ly")
        self.microscope.set_delivery_abs_ly(float(self.my_devices_info['loader']['slidepullly_offset']))
        self.microscope.motor_reset("x")
        self.microscope.motor_reset("lz")
        self.finished.emit(self.slides, str(task_id))
        self.logger.info('复位完毕')
        # self.disconnect()

    # def start_running(self, plan_data, task_id):
    #     self.t = None
    #     self.t = threading.Thread(target=self.run, args=(plan_data, task_id))
    #     self.t.start()
    #     self.logger.info('开始任务:' + str(task_id))
