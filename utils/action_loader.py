# -*- encoding: utf-8 -*-
"""
@Description:
用于控制装载器的封装类
@File    :   action_loader.py
@Time    :   2024/07/16
@Author  :   Li QingHao
@Version :   2.0
@Time_END :  最后修改时间：
@Developers_END :  最后修改作者：
"""
import os

import cv2
import numpy as np


class Color(object):
    red = b"\x01"
    green = b"\x10"
    yellow = b"\x11"


class Key(object):
    none = b"\x00"
    pressed = b"\x01"
    released = b"\x02"


class ActionLoader(object):
    def __init__(self, loader_controller, config):
        self.set_slide_task = None
        self.slide_task = None
        self.key = Key()
        self.color = Color()
        self.loader = loader_controller
        self.config = config

        self.up_config()

        self.cap = None
        self.list_box_points = []
        self.create_box_points()
        self.open_camera()

    def up_config(self):
        # 加载参数
        self.x_start1 = float(self.config['Loader']['box1startxz']['x'])
        self.z_start1 = float(self.config['Loader']['box1startxz']['z'])
        self.x_start2 = float(self.config['Loader']['box2startxz']['x'])
        self.z_start2 = float(self.config['Loader']['box2startxz']['z'])
        self.x_start3 = float(self.config['Loader']['box3startxz']['x'])
        self.z_start3 = float(self.config['Loader']['box3startxz']['z'])
        self.x_start4 = float(self.config['Loader']['box4startxz']['x'])
        self.z_start4 = float(self.config['Loader']['box4startxz']['z'])
        self.slide_all = 24
        self.slide_number = 24
        self.box1_flag = True
        self.box2_flag = True
        self.box3_flag = True
        self.box4_flag = True
        # 盒子间隙参数
        self.boxzgap = float(self.config['Loader']['boxzgap'])
        # 显微镜交接参数
        self.x_end = float(self.config['Loader']['xend'])
        self.z_end = float(self.config['Loader']['zend'])
        self.z_microscope_lift = float(self.config['Loader']['zlift'])
        self.slide_return = float(self.config['Loader']['slidereturn'])
        self.slide_push = float(self.config['Loader']['slidepush'])
        # 扫描避位
        self.x_avoid = float(self.config['Loader']['xavoid'])
        # # 装载器的相机
        self.cameraexposure = int(self.config['Loader']['cameraexposure'])
        self.z_camera = float(self.config['Loader']['zcamera'])

    # box初始位置(准备取片)

    def create_box_points(self):
        self.list_box_points = []
        for i in range(1, 5):
            x_start = 0
            z_start = 0
            if i == 1:
                x_start = self.x_start1
                z_start = self.z_start1
            elif i == 2:
                x_start = self.x_start2
                z_start = self.z_start2
            elif i == 3:
                x_start = self.x_start3
                z_start = self.z_start3
            elif i == 4:
                x_start = self.x_start4
                z_start = self.z_start4
            if x_start > 0 and z_start > 0:
                list_points = []
                for j in range(self.slide_all):
                    list_points.append([x_start, z_start - j * self.boxzgap])
                self.list_box_points.append(list_points)

    def get_box_points(self, box):
        return self.list_box_points[box - 1]

    def pre_get_box_points(self, box):
        if box < 1 or box > len(self.slide_task):
            raise ValueError("Invalid box value")
        pre_slide_task = self.slide_task[box - 1].tolist()
        pre_slide_task[0] = 0
        pre_slide_task[1:] = [1] * (len(pre_slide_task) - 1)
        return pre_slide_task, self.slide_points[box - 1].tolist()

    def move_z_to(self, z):
        """
        将加载器移动到指定的(z)坐标。
        """
        self.loader.set_delivery_abs_z(z)

    def move_x_to(self, x):
        """
        将加载器移动到指定的(z)坐标。
        """
        self.loader.set_delivery_abs_x(x)

    def move_y_to(self, y):
        """
        将加载器移动到指定的(y)坐标。
        """
        self.loader.set_delivery_abs_y(y)

    def move_2_microscope_give_location(self):
        """
        将加载器移动到显微镜的指定位置。

        该函数不接受参数，并且没有返回值。
        它通过调用self.loader的set_delivery_abs_point方法，设置加载器到显微镜的绝对交付点。
        """
        self.move_x_to(self.x_end)
        self.move_z_to(self.z_end)

    def move_2_microscope_get_location(self):
        """
        将加载器移动到显微镜的指定位置。

        该函数不接受参数，并且没有返回值。
        它通过调用self.loader的set_delivery_abs_point方法，设置加载器到显微镜的绝对交付点。
        """
        self.move_x_to(self.x_end)
        self.move_z_to(self.z_end + self.z_microscope_lift)

    def get_slide_from_box(self, current_z):
        """
        从盒子中获取滑块的函数。
        此函数不接受参数，并且没有返回值。
        函数执行过程：
        1. 通过执行机构伸出，将loader设置到初始的y位置。
        2. 调整loader的高度，使其向上移动。
        3. 收回执行机构，将loader移回初始位置。
        """
        self.move_y_to(self.slide_push)
        self.move_z_to(current_z - self.boxzgap)
        self.move_y_to(self.slide_return)

    def give_slide_to_box(self, current_z):
        """
        将滑块送入盒子中的函数。
        此函数不接受参数，并且没有返回值。
        函数执行过程：
        1. 使执行机构伸出到指定的y位置。
        2. 调整执行机构，使其向下移动到指定的z位置。
        3. 恢复执行机构的原始位置。
        """
        self.move_y_to(self.slide_push)
        self.move_z_to(current_z + self.boxzgap)
        self.move_y_to(self.slide_return)

    def give_slide_to_microscope(self):
        """
        将滑块送入显微镜中的函数。
        此函数不接受参数，并且没有返回值。
        函数执行过程：
        1. 使执行机构伸出到指定的y位置。
        2. 调整执行机构，使其向下移动到指定的z位置。
        3. 恢复执行机构的原始位置。
        """
        self.move_y_to(self.slide_push + 3)
        self.move_z_to(self.z_end + self.z_microscope_lift)
        self.move_y_to(self.slide_return)

    def get_slide_from_microscope(self):
        """
        从显微镜中获取滑块的函数。
        此函数不接受参数，并且没有返回值。
        函数执行过程：
        1. 使执行机构伸出到指定的y位置。
        2. 调整执行机构，使其向下移动到指定的z位置。
        3. 恢复执行机构的原始位置。
        """
        self.move_y_to(self.slide_push)
        self.move_z_to(self.z_end)
        self.move_y_to(self.slide_return)

    def last_slide_process(self, current_z):
        self.move_z_to(current_z)
        self.move_y_to(self.slide_push)
        self.move_y_to(self.slide_return)

    def set_led(self, num, color):
        self.loader.led[num] = color  # 设置灯颜色
        self.loader.set_led_color(self.loader.led[0:4])

    def get_key(self):
        box_key = []
        box_list = []
        for key in self.loader.key:
            if key == self.key.none:
                box_key.append(0)
            elif key == self.key.pressed:
                box_key.append(1)
            elif key == self.key.released:
                box_key.append(2)
        for i in range(len(box_key)):
            if box_key[i] == 1:
                box_list.append(i + 1)
        return box_list

    def loader_reset(self):
        """
        重置加载器。
        """
        self.loader.reset_xyz()

    def loader_move_xyz_0(self):
        self.move_y_to(-1)
        self.move_z_to(0)
        self.move_x_to(0)

    def disenble_motor(self):
        # 失能
        self.loader.scan_disenble_motor()

    def loader_avoid(self):
        """
        避免加载器。
        """
        self.move_x_to(self.x_avoid)

    def pump(self):
        self.loader.user_pump_test()

    def loader_move2_camera(self):
        self.move_z_to(self.z_camera)

    def open_camera(self):
        # 尝试打开索引 0 到 9 的摄像头
        self.cap = None
        for i in range(10):
            try:
                print('f"打开索引 {i} 的摄像头"')
                self.cap = cv2.VideoCapture(i)

                # 检查摄像头是否成功打开
                if self.cap.isOpened():
                    print(f"成功打开索引 {i} 的摄像头")
                    self.cap.set(cv2.CAP_PROP_EXPOSURE, self.cameraexposure)
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)  # 宽度为2592像素
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  # 高度为1944像素
                    break
                else:
                    print(f"索引 {i} 打开摄像头失败")
            except Exception as e:
                print(str(e))

        # 检查摄像头是否成功打开
        if not self.cap.isOpened():
            return False
        else:
            return True

    def capture_image(self):
        # 检查摄像头是否已打开
        if self.cap is None or not self.cap.isOpened():
            return None

        # 捕获单张图像
        ret, frame = self.cap.read()
        for i in range(5):
            ret, frame = self.cap.read()

        # 检查图像是否成功捕获
        if not ret:
            print("Failed to capture image")
            return None

        return frame

    def release_camera(self):
        # 释放摄像头资源
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
            return True
        else:
            return False
