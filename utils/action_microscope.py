# -*- encoding: utf-8 -*-
"""
@Description:
用于控制显微镜的封装类
@File    :   action_loader.py
@Time    :   2025/03/06
@Author  :   Li QingHao
@Version :   2.0
@Time_END :  最后修改时间：
@Developers_END :  最后修改作者：
"""
import time

class ActionMicroscope:

    def __init__(self, microscope):
        super().__init__()

        self.microscope = microscope

    def microscope_homezxy(self):
        self.microscope.navigationController.home_z()
        while self.microscope.microcontroller.is_busy():
            time.sleep(0.005)
        self.microscope.navigationController.home_x()
        while self.microscope.microcontroller.is_busy():
            time.sleep(0.005)
        self.microscope.navigationController.home_y()
        while self.microscope.microcontroller.is_busy():
            time.sleep(0.005)

    def microscope_homezxy_wait(self):
        self.microscope.navigationController.home_z()
        while self.microscope.microcontroller.is_busy():
            time.sleep(0.005)
        self.microscope.navigationController.home_x()
        self.microscope.navigationController.home_y()

    def microscope_home_z(self):
        self.microscope.navigationController.home_z()
        while self.microscope.microcontroller.is_busy():
            time.sleep(0.005)

    def microscope_move_x_to(self, x):
        self.microscope.navigationController.move_x_to(x)
        while self.microscope.microcontroller.is_busy():
            time.sleep(0.005)

    def microscope_move_y_to(self, y):
        self.microscope.navigationController.move_y_to(y)
        while self.microscope.microcontroller.is_busy():
            time.sleep(0.005)

    def microscope_move_z_to(self, z):
        self.microscope.navigationController.move_z_to(z)
        while self.microscope.microcontroller.is_busy():
            time.sleep(0.005)

    def move_2_loader_get(self, Xend, Yend):
        self.microscope.navigationController.move_y_to(Yend)
        # while self.microscope.microcontroller.is_busy():
        #     time.sleep(0.005)
        self.microscope.navigationController.move_x_to(Xend)
        while self.microscope.microcontroller.is_busy():
            time.sleep(0.005)

    def move_2_loader_give(self, Xend, Yend):
        self.microscope.navigationController.move_y_to(Yend - 1)
        # while self.microscope.microcontroller.is_busy():
        #     time.sleep(0.005)
        self.microscope.navigationController.move_x_to(Xend)
        while self.microscope.microcontroller.is_busy():
            time.sleep(0.005)

    def move_2_loader_get_wait(self, Xend, Yend):
        self.microscope.navigationController.move_y_to(Yend)
        self.microscope.navigationController.move_x_to(Xend)

    def wait_busy(self):
        while self.microscope.microcontroller.is_busy():
            time.sleep(0.005)

    # 设置0号灯
    def set_low_light(self):
        self.microscope.set_low_led()

    # 设置1号灯
    def set_high_light(self):
        self.microscope.set_high_led()

    # 打开灯
    def turn_on_light(self):
        self.microscope.microcontroller.turn_on_illumination()

    # 关闭灯
    def turn_off_light(self):
        self.microscope.microcontroller.turn_off_illumination()

    def set_only_light(self):
        self.microscope.set_only_led()

    def get_image_camera_low(self):
        self.turn_on_light()
        self.microscope.camera1.send_trigger()
        image = self.microscope.camera1.read_frame()
        self.turn_off_light()
        return image

    def get_image_camera_high(self):
        self.turn_on_light()
        self.microscope.camera2.send_trigger()
        image = self.microscope.camera2.read_frame()
        self.turn_off_light()
        return image

    def get_image_camera_one(self):
        self.turn_on_light()
        self.microscope.camera.send_trigger()
        image = self.microscope.camera.read_frame()
        self.turn_off_light()
        return image
