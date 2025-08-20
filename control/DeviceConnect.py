import json
import os
import numpy as np
import uuid

import serial
import serial.tools.list_ports

from control import microscope_controller
from control import ocr_camera_controller
from control import scan_camera_controller

from utils import Slide_worker
from utils import ImageSaver


class device_connect:
    def __init__(self, logger, my_devices_info, requester):
        self.microscope = None
        self.scan_camera = None
        self.ocr_camera = None
        self.connected_state = False
        self.Slide_worker = None
        self.requester = requester

        self.my_devices_info = my_devices_info
        self.logger = logger
        self.Image_Saver = ImageSaver.Image_Saver(my_devices_info['image_saver'], self.requester)

    def connect(self):
        try:
            for p in serial.tools.list_ports.comports():
                if p.serial_number == str(self.my_devices_info['microscope']['serial_port']):
                    self.microscope = microscope_controller.scannercontroller(p.device)
                    # self.microscope.enable_motor()
            if self.microscope is None:
                self.connected_state = False
                self.logger.error('显微镜串口连接失败,串口未查询到')
                return False, '显微镜串口连接失败,串口未查询到'
        except Exception as e:
            self.connected_state = False
            self.logger.error('显微镜串口连接失败')
            self.logger.error(str(e))
            return False, str(e)
        try:
            if self.scan_camera is None:
                self.scan_camera = scan_camera_controller.Camera()
                self.scan_camera.open()
                offset_x = (512 // 8) * 8
                offset_y = (18 // 8) * 8
                self.scan_camera.set_ROI(offset_x, offset_y, self.my_devices_info['image_saver']['widthMax'],
                                         self.my_devices_info['image_saver']['heightMax'])
                # 设置曝光时间和增益
                # self.scan_camera.set_exposure_time(my_devices_info['ScanCamera']['ExposureTime'])
                # 启用软件触发拍摄
                self.scan_camera.set_software_triggered_acquisition()
                self.scan_camera.start_streaming()
                # self.scan_camera.send_trigger()
                # img = self.scan_camera.read_frame()
                # print(img)
        except Exception as e:
            self.connected_state = False
            self.logger.error('扫描相机连接失败')
            self.logger.error(str(e))
            return False, str(e)
        try:
            if self.ocr_camera is None:
                self.ocr_camera = ocr_camera_controller.ocr_camera(self.my_devices_info['ocr_camera']['angle'])
                flag = self.ocr_camera.check_ocr_camera()
                if not flag:
                    self.connected_state = False
                    self.logger.error('OCR相机连接失败')
                    return False, 'OCR相机连接失败'
                self.ocr_camera.open(self.my_devices_info['ocr_camera']['ExposureTime'],
                                     self.my_devices_info['ocr_camera']['width'],
                                     self.my_devices_info['ocr_camera']['height'])
                self.connected_state = True
        except Exception as e:
            self.connected_state = False
            self.logger.error('OCR相机连接失败')
            self.logger.error(str(e))
            return False, str(e)
        self.connected_state = True
        self.microscope.motor_reset("z")
        self.microscope.motor_reset("w")
        self.microscope.motor_reset("y")
        self.microscope.motor_reset("ly")
        self.microscope.set_delivery_abs_ly(float(self.my_devices_info['loader']['slidepullly_offset']))
        self.microscope.motor_reset("x")
        self.microscope.motor_reset("lz")
        self.logger.info('设备连接成功')
        self.Slide_worker = Slide_worker.worker(self.microscope, self.scan_camera, self.ocr_camera, self.logger,
                                                self.my_devices_info, self.disconnect, self.requester)
        self.Slide_worker.ScanManager.Image_Saver = self.Image_Saver
        self.Slide_worker.ScanManager.Image_Saver.high_points_signal.connect(
            self.Slide_worker.ScanManager.updata_high_points)
        del offset_x
        del offset_y

        return self.connected_state, ''

    def disconnect(self):
        try:
            if self.microscope is not None:
                self.microscope.ser_close()
            if self.scan_camera is not None:
                self.scan_camera.close()
            if self.ocr_camera is not None:
                self.ocr_camera.close()
            # self.Image_Saver.stop()
            self.connected_state = False
            self.Slide_worker = None
            self.microscope = None
            self.scan_camera = None
            self.ocr_camera = None
            self.logger.error('设备连接断开')
            return True, ''
        except Exception as e:
            print(str(e))
            self.logger.error('设备连接断开失败')
            self.logger.error(str(e))
            return False, str(e)


class SlideStorage:
    def __init__(self, file_path, default_length=24):
        """
        初始化幻灯片存储类
        :param file_path: .npy文件路径
        :param default_length: 默认列表长度（默认为24）
        """
        self.file_path = file_path
        self.default_length = default_length
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 如果文件不存在，创建默认列表
        if not os.path.exists(file_path):
            self.save([0] * default_length)

    def save(self, slides):
        """
        保存幻灯片列表到.npy文件
        :param slides: 要保存的幻灯片列表
        """
        # 确保列表长度正确
        if len(slides) != self.default_length:
            raise ValueError(f"列表长度必须为 {self.default_length}")

        # 将列表转换为NumPy数组并保存
        np.save(self.file_path, np.array(slides))
        print(f"幻灯片列表已保存至: {self.file_path}")

    def load(self):
        """
        从.npy文件加载幻灯片列表
        :return: 加载的幻灯片列表
        """
        try:
            # 加载NumPy数组并转换为Python列表
            loaded_array = np.load(self.file_path, allow_pickle=True)
            slides = loaded_array.tolist()

            # 确保加载的列表长度正确
            if len(slides) != self.default_length:
                print(f"警告: 文件中的列表长度({len(slides)})与预期长度({self.default_length})不符，已重置为默认值")
                slides = [0] * self.default_length
                self.save(slides)

            return slides
        except Exception as e:
            print(f"加载文件时出错: {str(e)}，已创建新列表")
            slides = [0] * self.default_length
            self.save(slides)
            return slides

    def update_slide(self, index, value):
        """
        更新单个幻灯片的值
        :param index: 幻灯片索引(0-23)
        :param value: 新值
        """
        slides = self.load()
        if 0 <= index < len(slides):
            slides[index] = value
            self.save(slides)
        else:
            raise IndexError(f"索引 {index} 超出范围(0-{len(slides) - 1})")

    def get_slide(self, index):
        """
        获取单个幻灯片的值
        :param index: 幻灯片索引(0-23)
        :return: 幻灯片的值
        """
        slides = self.load()
        if 0 <= index < len(slides):
            return slides[index]
        raise IndexError(f"索引 {index} 超出范围(0-{len(slides) - 1})")


# 保存UUID
def save_uuid(uuid_obj):
    if not os.path.exists('uuid.json'):
        data = {"uuid": None}
    else:
        with open('uuid.json', 'r') as f:
            data = json.load(f)

    data["uuid"] = str(uuid_obj)

    with open('uuid.json', 'w') as f:
        json.dump(data, f, indent=2)


# 读取UUID
def load_uuid():
    if not os.path.exists('uuid.json'):
        return None

    with open('uuid.json', 'r') as f:
        data = json.load(f)

    return data.get("uuid", None)
