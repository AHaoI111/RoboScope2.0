import json
import logging
import os
import shutil
import time
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import threading

import numpy as np
import cv2
from PIL import Image
import yaml
import crcmod
import serial
import serial.tools.list_ports
from PySide6.QtCore import Signal, Slot, QTime, QTimer, QDate, QThread, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QPixmap, QBrush, QImage
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, \
    QMessageBox, QLineEdit, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy, QWidget, QLabel
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from uvicorn import Server, Config
from pydantic import BaseModel
import requests

# 自定义模块
import utils.read_config as read_config
from control import DeviceConnect
from gui import Ui_MainWindow
from main_plan_ui import MyDialog
from utils import serve
from utils import requester
from utils import config


def custom_question(parent, title, text):
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    # msg_box.setIcon(QMessageBox.Question)

    # 移除默认按钮
    msg_box.setStandardButtons(QMessageBox.NoButton)

    # 创建自定义按钮
    yes_button = msg_box.addButton("是", QMessageBox.YesRole)
    no_button = msg_box.addButton("否", QMessageBox.NoRole)

    # 设置按钮样式
    button_style = """
        QLabel {
                font-size: 14pt;
                padding: 15px;
            }
        QPushButton {
            min-width: 120px;
            min-height: 45px;
            font-size: 15px;
            font-weight: bold;
            padding: 10px;
            border-radius: 6px;
            margin: 10px;
        }
        QPushButton#yes {
            background-color: #4CAF50;
            color: white;
        }
        QPushButton#yes:hover {
            background-color: #45a049;
        }
        QPushButton#no {
            background-color: #f44336;
            color: white;
        }
        QPushButton#no:hover {
            background-color: #d32f2f;
        }
    """

    # 设置按钮对象名用于样式表
    yes_button.setObjectName("yes")
    no_button.setObjectName("no")
    msg_box.setStyleSheet(button_style)

    # 调整按钮布局
    layout = msg_box.layout()
    if layout is not None:
        # 创建水平布局容器
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(yes_button)
        button_layout.addWidget(no_button)
        button_layout.addStretch(1)

        # 替换原始按钮区域
        layout.addLayout(button_layout, 1, 1)
    msg_box.exec()
    clicked_button = msg_box.clickedButton()
    if clicked_button.objectName() == 'yes':
        return QMessageBox.Yes
    else:
        return QMessageBox.No


def scan_json_files(directory):
    json_files = []

    # 遍历目录中的文件
    for filename in os.listdir(directory):
        # 如果文件是 .json 文件，则加入列表
        if filename.endswith('.json'):
            name_without_extension = os.path.splitext(filename)[0]
            json_files.append(name_without_extension)

    return json_files


def create_qimage_from_cvimg(cvimg, format_):
    """
    Convert an OpenCV image (cvimg) to a QImage object.

    Parameters:
    cvimg: np.ndarray
        The OpenCV image, typically in BGR format.
    format_: QtGui.QImage.Format
        The format of the QImage to be created.

    Returns:
    QtGui.QImage
        The converted QImage object.
    """
    # Get the height and width of the OpenCV image
    height, width = cvimg.shape[:2]
    # Calculate the bytes per line of the image, considering whether it is a color image (more than 2 dimensions)
    bytes_per_line = width * cvimg.shape[2] if len(cvimg.shape) > 2 else width
    # Create a QImage object using the data of the OpenCV image, specifying the width, height, bytes per line,
    # and format
    return QImage(
        bytes(cvimg.data), width, height, bytes_per_line,
        format_
    )


def start_log():
    # 创建log文件夹，如果不存在的话
    log_dir = './log'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 获取当前日期，格式化为 yyyy-mm-dd
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_filename = os.path.join(log_dir, f"{current_date}_app.log")  # 生成基于日期的日志文件路径

    # 配置日志记录
    logger = logging.getLogger(__name__)  # 创建一个日志记录器
    logger.setLevel(logging.INFO)

    # 创建日志文件处理器（按天切割日志）
    file_handler = TimedRotatingFileHandler(
        log_filename, when="midnight", interval=1, backupCount=7, encoding='utf-8'  # 每天切割，保留7天的日志文件
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


class MyMainWindow(QMainWindow):
    menu_button_change = Signal(int)
    device_LED_signal = Signal(int)
    button_state_signal = Signal(int)
    open_display_message = Signal(str, str, int)  # 0显示ok按钮，1不显示
    close_display_message = Signal()
    updata_login_status = Signal()
    updata_serial_number_signal = Signal(str)

    updata_background_box = Signal()

    def __init__(self):
        super().__init__()
        self.t_stop = None
        self.t = None
        self.username = None
        self.user_id = None
        self.ui = Ui_MainWindow()  # 创建 UI 类的实例
        self.ui.setupUi(self)  # 设置界面
        self.set_ui()
        self.logger = start_log()
        #
        # config = read_config.ConfigReader(config_file='config.yaml', logger=self.logger)
        # my_devices_info = config.get_config_info()

        self.button_connect()
        self.button_state_number = 3
        self.button_state_signal.emit(self.button_state_number)

        self.plan = None
        self.plan_id = None
        local_config = config.Configuration()

        self.requester = requester.requester(self.logger, local_config)
        time.sleep(1)
        my_devices_info = self.requester.get_device_info()
        self.logger.info(str(my_devices_info))
        self.DeviceConnect = DeviceConnect.device_connect(self.logger, my_devices_info, self.requester)

        self.Server = serve.roboscope_server(local_config.local_host, local_config.local_port, self.DeviceConnect,
                                             self.logger, my_devices_info)
        self.Server.start()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)  # 将信号连接到槽
        self.timer.start(1000)
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_home)
        self.login_status = False
        self.updata_login_status.emit()

    def set_ui(self):
        # 设置 QLabel 背景图片
        self.pixmap_background = QPixmap('./icon/box.png')  # 加载图片
        self.ui.label_box.setPixmap(self.pixmap_background)
        # 创建 QGraphicsView 和 QGraphicsScene
        self.scene = QGraphicsScene()
        self.ui.graphicsView.setScene(self.scene)

        #
        self.ui.progressBar.setValue(0)
        self.ui.lineEdit_info.setText('当前未开始扫描')
        scanned_count = 0  # 例如扫描了10片
        self.ui.label_LED_ok_info.setText(f'已完成扫描{scanned_count}片')
        self.ui.label_LED_notok_info.setText(f'扫描失败{scanned_count}片')
        self.ui.label_LED_run_info.setText('当前未扫描')
        self.ui.label_LED_notrun_info.setText(f'等待扫描{scanned_count}片')
        #
        self.ui.label_device_info.setText('设备已就绪')

        self.ui.label_display_usename.setText('当前用户：未登录')
        self.ui.lineEdit_password.setEchoMode(QLineEdit.Password)

    def button_connect(self):
        self.ui.pushButton_login.clicked.connect(self.login)
        self.ui.pushButton_log_off.clicked.connect(self.logoff)
        self.ui.pushButton_login_cancel.clicked.connect(self.login_cancel)
        self.device_LED_signal.connect(self.device_LED_change)
        self.button_state_signal.connect(self.button_state)

        self.ui.pushButton_start_scan.clicked.connect(self.start_scan)
        self.ui.pushButton_pause_scan.clicked.connect(self.pause_run)
        self.ui.pushButton_continue_scan.clicked.connect(self.recover_run)
        self.ui.pushButton_stop_scan.clicked.connect(self.stop_scan)

        self.ui.pushButton_menu.clicked.connect(self.open_plan_ui)
        self.open_display_message.connect(self.display_message)
        self.close_display_message.connect(self.close_message)
        self.updata_login_status.connect(self.update_login_state)
        self.updata_serial_number_signal.connect(self.updata_serial_task_number)
        self.updata_background_box.connect(self.box_background)
        self.updata_serial_number_signal.emit('')

    def login(self):
        username = self.ui.lineEdit_usename.text()
        password = self.ui.lineEdit_password.text()
        login_flag, login_data = self.requester.login(username, password)
        if login_flag:
            self.user_id = login_data['user_id']
            self.username = login_data['username']
            self.login_status = True
            self.updata_login_status.emit()
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_home)
            if self.DeviceConnect.connected_state:
                self.button_state_signal.emit(self.button_state_number)
            else:
                self.button_state_number = 0
                self.button_state_signal.emit(self.button_state_number)
        else:
            self.open_display_message.emit("登录失败", "请检查用户名密码", 0)

    def logoff(self):
        if self.login_status:
            self.login_status = False
            self.user_id = None
            self.updata_login_status.emit()
            self.button_state_signal.emit(3)
        else:
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_log_in)

    def login_cancel(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_home)

    def start_scan(self):
        # 获取上一次保存的片
        task_id = None
        SlideStorage = DeviceConnect.SlideStorage(file_path='./slides.npy')
        slides = SlideStorage.load()
        count_ones = slides.count(1)
        count_threes = slides.count(3)
        total_count = count_ones + count_threes
        if total_count > 0:
            # 创建一个确认退出的弹窗
            # reply = QMessageBox.question(self, '提示', '检测到上一次扫描中途退出，是否恢复扫描？',
            #                              QMessageBox.Yes | QMessageBox.No,
            #                              QMessageBox.No)
            reply = custom_question(
                self,
                '提示',
                '检测到上一次扫描中途退出，是否恢复扫描？'
            )

            if reply == QMessageBox.Yes:
                task_id = DeviceConnect.load_uuid()
            else:
                slides = [0] * 24
        else:
            slides = [0] * 24
        self.t = None
        self.t = threading.Thread(target=self.start, args=(slides, task_id))
        self.t.start()

    def start(self, slides, task_id):
        self.updata_background_box.emit()
        if self.user_id is None:
            self.open_display_message.emit("未登录", "请登录后执行", 0)
            return
        # 获取方案详情
        if task_id is None:
            plan_data = self.requester.get_plan_info(self.plan_id)
            storage_data = self.requester.get_storage()
        else:
            # 根据task_id申请上一次的plan_id
            data_plan_all = self.requester.get_plan_info_from_task_id(task_id)
            if data_plan_all is None:
                self.open_display_message.emit("失效的任务", "续扫失败", 0)
                return
            self.plan_id = data_plan_all['plan_id']
            plan_data = self.requester.get_plan_info(self.plan_id)
            serial_number = data_plan_all['serial_number']
            storage_id = data_plan_all['storage_id']
            storage_data = self.requester.get_storage_from_storageid(storage_id)
        if self.plan_id is None:
            self.open_display_message.emit("未选择方案", "请选择方案后执行", 0)
            return
        # 检测存储
        
        disk_usage = shutil.disk_usage(storage_data['storage_path'])
        used = disk_usage.used // (2 ** 30)
        self.logger.info(f"存储空间使用情况：{used}G")
        self.logger.info(f"存储空间剩余：{storage_data['quota_space'] - used}G")

        plan_data['storage_id'] = storage_data['id']
        plan_data['storage_path'] = storage_data['storage_path']
        if storage_data['quota_space'] - used < 50:
            self.open_display_message.emit("存储空间不足50G", "请清理存储空间", 0)
            self.logger.info("存储空间不足50G")
            # 申请任务id
            if task_id is None:
                task_id, serial_number = self.requester.create_task_id(plan_data['id'], storage_data['id'],
                                                                       self.user_id)

            self.logger.info(f"方案详情：{plan_data}")
            self.logger.info(f"任务id：{task_id}")
            if task_id is None and serial_number is None:
                self.open_display_message.emit("任务申请失败", "请检查任务申请参数", 0)
                return
            self.updata_serial_number_signal.emit(str(serial_number))
            self.plan_id = None
            self.start_run(plan_data, task_id, slides)
        elif storage_data['quota_space'] - used < 20:
            self.open_display_message.emit("存储空间不足20G", "本次扫描退出，请清理磁盘后进行", 0)
            self.logger.info("存储空间不足20G")
        else:
            # 申请任务id
            if task_id is None:
                task_id, serial_number = self.requester.create_task_id(plan_data['id'], storage_data['id'],
                                                                       self.user_id)

            self.logger.info(f"方案详情：{plan_data}")
            self.logger.info(f"任务id：{task_id}")

            if task_id is None and serial_number is None:
                self.open_display_message.emit("任务申请失败", "请检查任务申请参数", 0)
                return
            self.updata_serial_number_signal.emit(str(serial_number))
            self.plan_id = None
            self.start_run(plan_data, task_id, slides)

    def start_run(self, plan_data, task_id, slides):
        if self.DeviceConnect.connected_state:
            if self.DeviceConnect.Slide_worker.t is not None:
                self.open_display_message.emit("正在运行中", "请勿重复运行", 0)
                return {"status": "error", "message": "该设备扫描正在运行，请勿重复"}
            self.open_display_message.emit("正在准备运行", "请稍等", 0)
            return {"status": "error", "message": "该设备扫描已处于连接状态"}
        else:
            self.open_display_message.emit("正在连接设备", "正在连接设备,请稍等", 1)
            flag, msg = self.DeviceConnect.connect()
            if not flag:
                self.close_display_message.emit()
                self.open_display_message.emit("设备连接失败", msg, 0)
                self.device_LED_signal.emit(3)
                return {"status": "error", "message": msg}
            self.device_LED_signal.emit(1)
            self.button_state_signal.emit(1)
            self.button_state_number = 1
            self.close_display_message.emit()

            self.DeviceConnect.Slide_worker.worker_Progress.connect(self.draw)
            self.DeviceConnect.Slide_worker.worker_info.connect(self.updata_worker_info)
            self.DeviceConnect.Slide_worker.ScanManager.scan_img.connect(self.display)
            self.DeviceConnect.Slide_worker.ScanManager.scan_info.connect(self.scan_info)
            self.DeviceConnect.Slide_worker.ScanManager.progress_signal.connect(self.updata_progress)
            self.DeviceConnect.Slide_worker.finished.connect(self.finfsh)
            self.DeviceConnect.Slide_worker.display_slide_image.connect(self.display_slide)

            self.DeviceConnect.Slide_worker.run(plan_data, task_id, slides, self.user_id)

            return {"status": "success", "message": "开始扫描"}

    def pause_run(self):
        if self.DeviceConnect.connected_state:
            self.DeviceConnect.Slide_worker.pause_work()
            self.device_LED_signal.emit(2)
            self.button_state_signal.emit(2)
            self.button_state_number = 2
            return {"status": "success", "message": "扫描已暂停"}
        else:
            return {"status": "error", "message": "设备未处于连接状态"}

    def recover_run(self):
        if self.DeviceConnect.connected_state:
            self.DeviceConnect.Slide_worker.recover_work()
            self.device_LED_signal.emit(1)
            self.button_state_signal.emit(1)
            self.button_state_number = 1
            return {"status": "success", "message": "扫描已恢复"}
        else:
            return {"status": "error", "message": "设备未处于连接状态"}

    def stop_scan(self):
        self.t_stop = None
        self.t_stop = threading.Thread(target=self.stop_run, )
        self.t_stop.start()

    def stop_run(self):
        if self.DeviceConnect.connected_state:
            self.open_display_message.emit("正在停止", "正在停止设备并退出玻片仓,请稍等", 1)
            self.DeviceConnect.Slide_worker.stop_work()
            if self.t is not None:
                self.t.join()
                self.t = None
            self.device_LED_signal.emit(0)
            self.button_state_signal.emit(0)
            self.close_display_message.emit()
            # self.DeviceConnect.disconnect()
            return {"status": "success", "message": "扫描已停止"}
        else:
            return {"status": "error", "message": "设备未处于连接状态"}

    def open_plan_ui(self):
        if self.login_status:
            self.MyDialog = MyDialog()
            self.plans_list = self.requester.get_plan_list()
            name_list = []
            for plan in self.plans_list:
                name_list.append(plan['name'])
            self.MyDialog.ui.listWidget.addItems(name_list)
            self.MyDialog.button_signal.connect(self.close_plan_ui)
            self.MyDialog.showFullScreen()
            self.MyDialog.show()
        else:
            self.open_display_message.emit("未登录", "请先登录", 0)

    @Slot()  # 显式声明为槽
    def update_login_state(self):
        if self.login_status:
            self.ui.pushButton_log_off.setText("退出登录")
            self.ui.label_display_usename.setText('当前用户：' + self.username)
            self.ui.lineEdit_usename.setText('')
            self.ui.lineEdit_password.setText('')
        else:
            self.ui.pushButton_log_off.setText("登录")
            self.ui.label_display_usename.setText('当前用户：未登录')
            self.ui.lineEdit_usename.setText('')
            self.ui.lineEdit_password.setText('')

    @Slot()  # 显式声明为槽
    def update_time(self):
        # 获取当前时间和日期，并更新 QLabel 上的显示
        current_date = QDate.currentDate().toString("yyyy-MM-dd")
        current_time = QTime.currentTime().toString("HH:mm:ss")
        self.ui.label_time.setText(f"{current_date} {current_time}")

    @Slot(str, str, int)
    def \
            display_message(self, title, text, select_number):
        # 创建没有按钮的 QMessageBox
        self.display_message_window = QMessageBox(self)
        # self.display_message_window.setWindowTitle(title)
        self.display_message_window.setWindowFlags(Qt.FramelessWindowHint)
        self.display_message_window.setText(text)
        if select_number == 0:
            self.display_message_window.setStandardButtons(QMessageBox.StandardButton.Ok)
        elif select_number == 1:
            self.display_message_window.setStandardButtons(QMessageBox.StandardButton.Close)
        self.display_message_window.setStyleSheet("""
        /* 设置整个消息框的背景颜色 */
        QMessageBox {
            background-color: #333;  /* 深灰色背景 */
            border: 2px solid #555;  /* 可选：添加边框 */
            border-radius: 10px;     /* 可选：圆角 */
        }
        
        /* 设置文本标签样式 */
        QMessageBox > QLabel#qt_msgbox_label {
            color: white;            /* 白色文字 */
            font-size: 16px;         /* 字体大小 */
            min-width: 300px;        /* 最小宽度 */
            qproperty-alignment: AlignCenter;  /* 文本居中 */
            padding: 20px;           /* 内边距 */
        }
        
        /* 设置按钮样式（如果有按钮） */
        QMessageBox > QPushButton {
            background-color: #555;   /* 按钮背景色 */
            color: white;             /* 按钮文字颜色 */
            min-width: 80px;          /* 按钮最小宽度 */
            min-height: 30px;         /* 按钮最小高度 */
            border-radius: 5px;       /* 按钮圆角 */
        }
        
        /* 按钮悬停效果 */
        QMessageBox > QPushButton:hover {
            background-color: #666;   /* 悬停时的背景色 */
        }
    """)
        # 显示对话框
        self.display_message_window.show()

    @Slot()
    def close_message(self):
        # 关闭已存在的消息窗口（如果存在）
        if hasattr(self, 'display_message_window') and self.display_message_window:
            self.display_message_window.close()
            self.display_message_window = None

    @Slot(str)
    def close_plan_ui(self, text):
        if text == '':
            self.plan_name = None
            self.plan_id = None
        else:
            for plan in self.plans_list:
                if plan['name'] == text:
                    self.plan_name = plan
                    self.plan_id = plan['id']
                    break
                else:
                    self.plan_name = None
                    self.plan_id = None
        self.MyDialog.close()

    @Slot(str)
    def scan_info(self, text):
        self.ui.lineEdit_info.setText(text)

    @Slot(str)
    def updata_serial_task_number(self, text):
        self.ui.label_display_box_task.setText(text)

    @Slot(int)
    def device_LED_change(self, LED_id):
        if LED_id == 0:
            self.ui.label_device_info.setText('设备已就绪')
            self.ui.label_LED_device.setStyleSheet("QLabel {width: 30px; height: 30px;"
                                                   "border-radius: 15px;background-color: green;"
                                                   "border: 2px solid black; }")
        elif LED_id == 1:
            self.ui.label_device_info.setText('设备正在扫描')
            self.ui.label_LED_device.setStyleSheet("QLabel {width: 30px; height: 30px;"
                                                   "border-radius: 15px;background-color: yellow;"
                                                   "border: 2px solid black; }")
        elif LED_id == 2:
            self.ui.label_device_info.setText('设备已暂停')
            self.ui.label_LED_device.setStyleSheet("QLabel {width: 30px; height: 30px;"
                                                   "border-radius: 15px;background-color: yellow;"
                                                   "border: 2px solid black; }")
        elif LED_id == 3:
            self.ui.label_device_info.setText('设备通信故障，请检查')
            self.ui.label_LED_device.setStyleSheet("QLabel {width: 30px; height: 30px;"
                                                   "border-radius: 15px;background-color: red;"
                                                   "border: 2px solid black; }")

    @Slot(list)  # 将此函数声明为槽函数
    def draw(self, slide_list):
        pixmap = self.pixmap_background
        # 检查是否成功获取了 QPixmap
        if not pixmap.isNull():
            # 创建 QPainter 对象
            painter = QPainter(pixmap)
            xstart = 34
            ystart = 59
            w = 110
            h = 11
            for index, slide in enumerate(slide_list):
                if slide == 0:
                    pass
                elif slide == 1:
                    painter.setPen(QPen(QColor(128, 128, 128), 1))  # 灰色矩形边框
                    painter.setBrush(QBrush(QColor(128, 128, 128, 128)))  # 灰色半透明填充
                    painter.drawRect(xstart, int(ystart + 20.1 * index), w, h)
                elif slide == 2:
                    painter.setPen(QPen(QColor(0, 255, 0), 1))  # 绿色矩形边框
                    painter.setBrush(QBrush(QColor(0, 255, 0, 128)))
                    painter.drawRect(xstart, int(ystart + 20.1 * index), w, h)
                elif slide == 3:
                    painter.setPen(QPen(QColor(255, 0, 0), 1))  # 蓝色矩形边框
                    painter.setBrush(QBrush(QColor(255, 0, 0, 128)))
                    painter.drawRect(xstart, int(ystart + 20.1 * index), w, h)
                elif slide == 4:
                    painter.setPen(QPen(QColor(255, 255, 0), 1))
                    painter.setBrush(QBrush(QColor(255, 255, 0, 128)))
                    painter.drawRect(xstart, int(ystart + 20.1 * index), w, h)
            # 完成绘制
            painter.end()
            # 更新 QLabel 中的显示图像
            self.ui.label_box.setPixmap(pixmap)

    @Slot(list)  # 将此函数声明为槽函数
    def updata_worker_info(self, slide_list):
        count_one = slide_list.count(1)
        count_two = slide_list.count(2)
        count_three = slide_list.count(3)
        count_four = slide_list.count(4)
        self.ui.label_LED_ok_info.setText(f'已完成扫描{count_two}片')
        self.ui.label_LED_notok_info.setText(f'扫描失败{count_three}片')
        if count_four > 0:
            index_4 = slide_list.index(4)
            self.ui.label_LED_run_info.setText(f'正在扫描第{index_4 + 1}片')
        else:
            self.ui.label_LED_run_info.setText('当前未扫描')
        self.ui.label_LED_notrun_info.setText(f'等待扫描{count_one}片')

    @Slot(np.ndarray, int, list, bool, int, int, int, int)  # 将此函数声明为槽函数
    def display(self, img, a, points, stitch_flag, numberx, numbery, crop_w, crop_h):
        """
        根据控件大小自动缩放图像
        :param img: 输入图像（NumPy 数组格式）
        """
        # 清空场景中的所有项
        height, width = img.shape[:2]
        if height > crop_h and width > crop_w:
            img = img[int((height - crop_h) / 2):crop_h + int((height - crop_h) / 2),
                  int((width - crop_w) / 2):crop_w + int((width - crop_w) / 2)]
        if stitch_flag:
            if a == 1:
                self.scene.clear()
            # 获取控件的尺寸
            view_width = self.ui.graphicsView.width() - 8
            view_height = self.ui.graphicsView.height() - 8
            # view_width = 392
            # view_height = 392
            used_width = view_width / numberx
            used_height = view_height / numbery
            used_min = min(used_width, used_height)
            channel = len(img.shape)
            format_ = QImage.Format_Grayscale8 if channel == 2 else QImage.Format_RGB888
            # Convert the OpenCV image to QImage
            q_img = create_qimage_from_cvimg(img, format_)
            scaled_pixmap = QPixmap.fromImage(q_img).scaled(
                int(used_min),
                int(used_min)
            )
            start_x = int((view_width / 2) - (used_min * numberx) / 2)
            start_y = int((view_height / 2) - (used_min * numbery) / 2)
            pixmap_item = QGraphicsPixmapItem(scaled_pixmap)
            pixmap_item.setPos(points[1] * int(used_min) + start_x,
                               points[0] * int(used_min) + start_y)
            # Center the graphics view on the pixmap
            # self.ui.graphicsView.centerOn(points[1] * int(used_width) + int(used_width / 2),
            #                               points[0] * int(used_height) + int(used_height / 2))
            # Add the pixmap item to the scene
            self.scene.addItem(pixmap_item)

            del format_
            del q_img
            del scaled_pixmap
            del start_x
            del start_y

        else:
            self.scene.clear()

            # 获取控件的尺寸
            view_width = self.ui.graphicsView.width() - 8
            view_height = self.ui.graphicsView.height() - 8
            # view_width = 392
            # view_height = 392

            # 将 NumPy 数组转换为 QImage
            height, width = img.shape[:2]
            qimg = QImage(img.data, width, height, img.strides[0], QImage.Format_RGB888)

            # 将 QImage 转换为 QPixmap
            pixmap = QPixmap.fromImage(qimg)

            # 计算缩放比例
            scale_width = view_width / width
            scale_height = view_height / height
            scale_factor = min(scale_width, scale_height)
            new_width = width * scale_factor
            new_height = height * scale_factor

            offset_x = int((view_width - new_width) / 2)
            offset_y = int((view_height - new_height) / 2)

            # 创建一个 QGraphicsPixmapItem 并设置它的位置和大小
            pixmap_item = QGraphicsPixmapItem(pixmap)
            pixmap_item.setOffset(offset_x, offset_y)  # 设置显示的位置
            pixmap_item.setScale(scale_factor)  # 根据控件大小设置图像缩放

            # 将图像添加到场景中
            self.scene.addItem(pixmap_item)

            del qimg
            del pixmap
            del new_width
            del new_height
            del offset_x
            del offset_y
        del height
        del width
        del crop_w
        del crop_h
        del img

    @Slot(np.ndarray)  # 将此函数声明为槽函数
    def display_slide(self, img):
        """
        根据控件大小自动缩放图像
        :param img: 输入图像（NumPy 数组格式）
        """
        # 清空场景中的所有项
        if img is not None:
            channel = len(img.shape)
            format_ = QImage.Format_Grayscale8 if channel == 2 else QImage.Format_RGB888
            # Convert the OpenCV image to QImage
            q_img = create_qimage_from_cvimg(img, format_)
            pixmap = QPixmap.fromImage(q_img)
            self.ui.label_slide.setPixmap(pixmap)
            self.ui.label_slide.setScaledContents(True)
        del img

    @Slot()
    def button_state(self, state):
        if state == 0:
            self.ui.pushButton_start_scan.setEnabled(True)
            self.ui.pushButton_pause_scan.setEnabled(False)
            self.ui.pushButton_stop_scan.setEnabled(False)
            self.ui.pushButton_continue_scan.setEnabled(False)

        elif state == 1:
            self.ui.pushButton_start_scan.setEnabled(False)
            self.ui.pushButton_pause_scan.setEnabled(True)
            self.ui.pushButton_stop_scan.setEnabled(True)
            self.ui.pushButton_continue_scan.setEnabled(False)
        elif state == 2:
            self.ui.pushButton_start_scan.setEnabled(False)
            self.ui.pushButton_pause_scan.setEnabled(False)
            self.ui.pushButton_stop_scan.setEnabled(True)
            self.ui.pushButton_continue_scan.setEnabled(True)
        elif state == 3:
            self.ui.pushButton_start_scan.setEnabled(False)
            self.ui.pushButton_pause_scan.setEnabled(False)
            self.ui.pushButton_stop_scan.setEnabled(False)
            self.ui.pushButton_continue_scan.setEnabled(False)

    @Slot(int)
    def updata_progress(self, progress: int):
        self.ui.progressBar.setValue(progress)

    @Slot(list, str)
    def finfsh(self, slide_list, task_id):
        self.button_state_signal.emit(0)
        self.device_LED_signal.emit(0)
        self.scene.clear()
        self.ui.lineEdit_info.setText('当前已完成扫描')

        self.ui.progressBar.setValue(0)
        self.DeviceConnect.disconnect()

        SlideStorage = DeviceConnect.SlideStorage(file_path='./slides.npy')
        SlideStorage.save(slide_list)
        DeviceConnect.save_uuid(uuid_obj=task_id)

    @Slot()
    def box_background(self):
        self.pixmap_background = QPixmap('./icon/box.png')  # 加载图片
        self.ui.label_box.setPixmap(self.pixmap_background)

    def closeEvent(self, event):
        # 在窗口关闭事件中触发的函数
        self.close_thing()
        event.accept()

    def close_thing(self):
        self.DeviceConnect.Image_Saver.stop()
        self.Server.stop()


if __name__ == "__main__":
    app = QApplication([])  # 创建应用程序对象
    window = MyMainWindow()  # 创建主窗口实例
    window.showFullScreen()  # 显示全屏窗口
    window.show()
    app.exec()  # 启动应用的事件循环
