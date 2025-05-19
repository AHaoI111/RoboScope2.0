import re

from Drives import camera
from Drives.microcontroller_V2 import Microcontroller
import control.core_V2 as core
from Drives._def_V2 import *
import time


class SerialMicroscope:
    def __init__(self, config_info):
        self.config_info = config_info

    def open(self):
        try:
            self.configurationManager = core.ConfigurationManager('./channel_configurations.xml')
            self.microcontroller = Microcontroller(COM=self.config_info['Microscope']['sys']['串口'])
            self.microcontroller.reset()
            self.microcontroller.initialize_drivers()
            self.microcontroller.configure_actuators()
            self.navigationController = core.NavigationController(self.microcontroller)
            self.initialization()
            self.set_pid()
            self.set_limit()
            self.open_camera()
            return True
        except Exception as e:
            print(e)
            return False

    def close(self):
        self.microcontroller.close()
        if self.config_info['Device']['cameranumber'] == 1:
            self.camera.close()
        elif self.config_info['Device']['cameranumber'] == 2:
            self.camera1.close()
            self.camera2.close()

    def open_camera(self):
        try:
            if self.config_info['Device']['cameranumber'] == 1:
                # 单相机配置
                self.camera = camera.Camera(
                    rotate_image_angle=self.config_info['Camera']['single']['RotateImageAngleonly'])
                # 打开相机
                self.camera.open()
                configuration = self.configurationManager.configurations[0]
                # 根据相机型号配置参数
                # 设置相机参数
                letters_only = re.sub(r'\d+', '', configuration.camera_sn)
                if letters_only == 'FCU':
                    # 自动白平衡
                    if len(self.config_info['Camera']['single']['wbone']) != 3:
                        self.camera.camera.BalanceWhiteAuto.set(2)
                    else:
                        self.camera.set_wb_ratios(self.config_info['Camera']['single']['wbone']['R'],
                                                  self.config_info['Camera']['single']['wbone']['G'],
                                                  self.config_info['Camera']['single']['wbone']['B'])
                # 设置拍摄区域
                offset_x = (732 // 8) * 8
                offset_y = (238 // 8) * 8
                self.camera.set_ROI(offset_x, offset_y, 2560, 2560)
                # 设置曝光时间和增益
                self.camera.set_exposure_time(configuration.exposure_time)
                self.camera.set_analog_gain(configuration.analog_gain)
                # 启用软件触发拍摄
                self.camera.set_software_triggered_acquisition()
                self.camera.start_streaming()

                self.set_only_led()
                self.microcontroller.turn_on_illumination()
                self.camera.send_trigger()
                # 检查相机是否成功获取图像
                img = self.camera.read_frame()
                self.microcontroller.turn_off_illumination()
                print(img)
                if img is not None:
                    return True

            elif self.config_info['Device']['cameranumber'] == 2:
                # 双相机配置
                configuration1 = self.configurationManager.configurations[0]
                configuration2 = self.configurationManager.configurations[1]
                self.camera1 = camera.Camera(sn=configuration1.camera_sn,
                                             rotate_image_angle=self.config_info['Camera']['low'][
                                                 'RotateImageAnglelow'])
                self.camera2 = camera.Camera(sn=configuration2.camera_sn,
                                             rotate_image_angle=self.config_info['Camera']['high'][
                                                 'RotateImageAnglehigh'])
                # 打开相机
                self.camera1.open()
                self.camera2.open()
                configuration1 = self.configurationManager.configurations[0]
                configuration2 = self.configurationManager.configurations[1]

                letters_only = re.sub(r'\d+', '', configuration1.camera_sn)
                if letters_only == 'FCU':
                    # 自动白平衡
                    if len(self.config_info['Camera']['low']['wblow']) != 3:
                        self.camera1.camera.BalanceWhiteAuto.set(2)
                    else:
                        self.camera1.set_wb_ratios(self.config_info['Camera']['low']['wblow']['R'],
                                                   self.config_info['Camera']['low']['wblow']['G'],
                                                   self.config_info['Camera']['low']['wblow']['B'])
                # 设置拍摄区域
                offset_x = (732 // 8) * 8
                offset_y = (238 // 8) * 8
                self.camera1.set_ROI(offset_x, offset_y, 2560, 2560)
                # 设置曝光时间和增益
                self.camera1.set_exposure_time(configuration1.exposure_time)
                self.camera1.set_analog_gain(configuration1.analog_gain)
                # 启用软件触发拍摄
                self.camera1.set_software_triggered_acquisition()
                self.camera1.start_streaming()

                self.set_low_led()
                # 检查相机是否成功获取图像
                self.microcontroller.turn_on_illumination()
                self.camera1.send_trigger()
                img = self.camera1.read_frame()
                self.microcontroller.turn_off_illumination()

                letters_only = re.sub(r'\d+', '', configuration2.camera_sn)
                if letters_only == 'FCU':
                    if len(self.config_info['Camera']['high']['wbhigh']) != 3:
                        self.camera2.camera.BalanceWhiteAuto.set(2)
                    else:
                        self.camera2.set_wb_ratios(self.config_info['Camera']['high']['wbhigh']['R'],
                                                   self.config_info['Camera']['high']['wbhigh']['G'],
                                                   self.config_info['Camera']['high']['wbhigh']['B'])
                self.camera2.set_ROI(offset_x, offset_y, 2560, 2560)
                self.camera2.set_exposure_time(configuration2.exposure_time)
                self.camera2.set_analog_gain(configuration2.analog_gain)
                self.camera2.set_software_triggered_acquisition()
                self.camera2.start_streaming()

                self.set_high_led()
                self.microcontroller.turn_on_illumination()
                self.camera2.send_trigger()
                # 检查相机是否成功获取图像
                img = self.camera2.read_frame()
                self.microcontroller.turn_off_illumination()
                return True
        except Exception as e:
            print(e)
            return False

    def initialization(self):
        t0 = time.time()
        self.navigationController.home_z()
        while self.microcontroller.is_busy():
            time.sleep(0.005)
            if time.time() - t0 > 8:
                print('Z轴归零超时')
                break
        t0 = time.time()
        self.navigationController.home_x()
        # 等待X轴归零完成
        while self.microcontroller.is_busy():
            time.sleep(0.005)
            if time.time() - t0 > 8:
                print('X轴归零超时')
                break
        t0 = time.time()
        self.navigationController.home_y()
        # 等待Y轴归零完成
        while self.microcontroller.is_busy():
            time.sleep(0.005)
            if time.time() - t0 > 8:
                print('Y轴归零超时')
                break

    def set_pid(self):
        # 根据配置信息，条件性地配置编码器
        if HAS_ENCODER_X == True:
            self.navigationController.set_axis_PID_arguments(0, PID_P_X, PID_I_X, PID_D_X)
            self.navigationController.configure_encoder(0, (SCREW_PITCH_X_MM * 1000) / ENCODER_RESOLUTION_UM_X,
                                                        ENCODER_FLIP_DIR_X)
            self.navigationController.set_pid_control_enable(0, ENABLE_PID_X)
            if HAS_ENCODER_Y == True:
                self.navigationController.set_axis_PID_arguments(1, PID_P_Y, PID_I_Y, PID_D_Y)
                self.navigationController.configure_encoder(1, (SCREW_PITCH_Y_MM * 1000) / ENCODER_RESOLUTION_UM_Y,
                                                            ENCODER_FLIP_DIR_Y)
                self.navigationController.set_pid_control_enable(1, ENABLE_PID_Y)
            if HAS_ENCODER_Z == True:
                self.navigationController.set_axis_PID_arguments(2, PID_P_Z, PID_I_Z, PID_D_Z)
                self.navigationController.configure_encoder(2, (SCREW_PITCH_Z_MM * 1000) / ENCODER_RESOLUTION_UM_Z,
                                                            ENCODER_FLIP_DIR_Z)
                self.navigationController.set_pid_control_enable(2, ENABLE_PID_Z)
        time.sleep(0.5)

    def set_limit(self):
        self.navigationController.set_x_limit_pos_mm(SOFTWARE_POS_LIMIT.X_POSITIVE)
        self.navigationController.set_x_limit_neg_mm(SOFTWARE_POS_LIMIT.X_NEGATIVE)
        self.navigationController.set_y_limit_pos_mm(SOFTWARE_POS_LIMIT.Y_POSITIVE)
        self.navigationController.set_y_limit_neg_mm(SOFTWARE_POS_LIMIT.Y_NEGATIVE)
        self.navigationController.set_z_limit_pos_mm(SOFTWARE_POS_LIMIT.Z_POSITIVE)

    def set_low_led(self):
        self.microcontroller.turn_off_illumination()
        if self.configurationManager.configurations[0].illumination_source < 10:  # LED matrix
            self.microcontroller.set_illumination_led_matrix(
                self.configurationManager.configurations[0].illumination_source,
                r=(self.configurationManager.configurations[0].illumination_intensity / 100) * LED_MATRIX_R_FACTOR,
                g=(self.configurationManager.configurations[0].illumination_intensity / 100) * LED_MATRIX_G_FACTOR,
                b=(self.configurationManager.configurations[0].illumination_intensity / 100) * LED_MATRIX_B_FACTOR)
        else:
            self.microcontroller.set_illumination(self.configurationManager.configurations[0].illumination_source,
                                                  self.configurationManager.configurations[0].illumination_intensity)

    def set_high_led(self):
        self.microcontroller.turn_off_illumination()
        if self.configurationManager.configurations[1].illumination_source < 10:  # LED matrix
            self.microcontroller.set_illumination_led_matrix(
                self.configurationManager.configurations[1].illumination_source,
                r=(self.configurationManager.configurations[1].illumination_intensity / 100) * LED_MATRIX_R_FACTOR,
                g=(self.configurationManager.configurations[1].illumination_intensity / 100) * LED_MATRIX_G_FACTOR,
                b=(self.configurationManager.configurations[1].illumination_intensity / 100) * LED_MATRIX_B_FACTOR)
        else:
            self.microcontroller.set_illumination(self.configurationManager.configurations[1].illumination_source,
                                                  self.configurationManager.configurations[1].illumination_intensity)

    def set_only_led(self):

        self.microcontroller.turn_off_illumination()
        if self.configurationManager.configurations[0].illumination_source < 10:  # LED matrix
            self.microcontroller.set_illumination_led_matrix(
                self.configurationManager.configurations[0].illumination_source,
                r=(self.configurationManager.configurations[0].illumination_intensity / 100) * LED_MATRIX_R_FACTOR,
                g=(self.configurationManager.configurations[0].illumination_intensity / 100) * LED_MATRIX_G_FACTOR,
                b=(self.configurationManager.configurations[0].illumination_intensity / 100) * LED_MATRIX_B_FACTOR)
        else:
            self.microcontroller.set_illumination(self.configurationManager.configurations[0].illumination_source,
                                                  self.configurationManager.configurations[0].illumination_intensity)
