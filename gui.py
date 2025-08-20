# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QGraphicsView, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMenuBar,
    QProgressBar, QPushButton, QScrollArea, QSizePolicy,
    QSpacerItem, QStackedWidget, QStatusBar, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1024, 768)
        MainWindow.setMinimumSize(QSize(1024, 768))
        MainWindow.setMaximumSize(QSize(1024, 768))
        MainWindow.setStyleSheet(u"background-color: #282c34;")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.stackedWidget.setGeometry(QRect(6, 6, 1024, 768))
        self.stackedWidget.setMinimumSize(QSize(1024, 768))
        self.stackedWidget.setMaximumSize(QSize(1024, 768))
        self.page_home = QWidget()
        self.page_home.setObjectName(u"page_home")
        self.verticalLayout_9 = QVBoxLayout(self.page_home)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(-1, -1, -1, 40)
        self.frame = QFrame(self.page_home)
        self.frame.setObjectName(u"frame")
        self.frame.setMinimumSize(QSize(0, 25))
        self.frame.setMaximumSize(QSize(16777215, 25))
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_9 = QHBoxLayout(self.frame)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.label_time = QLabel(self.frame)
        self.label_time.setObjectName(u"label_time")
        self.label_time.setMinimumSize(QSize(371, 21))
        self.label_time.setMaximumSize(QSize(16777215, 21))
        self.label_time.setStyleSheet(u"color: white;")

        self.horizontalLayout_9.addWidget(self.label_time)

        self.label_display_usename = QLabel(self.frame)
        self.label_display_usename.setObjectName(u"label_display_usename")
        self.label_display_usename.setMinimumSize(QSize(161, 21))
        self.label_display_usename.setMaximumSize(QSize(161, 21))
        self.label_display_usename.setStyleSheet(u"color: white;")

        self.horizontalLayout_9.addWidget(self.label_display_usename)

        self.pushButton_log_off = QPushButton(self.frame)
        self.pushButton_log_off.setObjectName(u"pushButton_log_off")
        self.pushButton_log_off.setMinimumSize(QSize(101, 21))
        self.pushButton_log_off.setMaximumSize(QSize(101, 21))
        self.pushButton_log_off.setStyleSheet(u"color: white;")

        self.horizontalLayout_9.addWidget(self.pushButton_log_off)


        self.verticalLayout_9.addWidget(self.frame)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.scrollArea_2 = QScrollArea(self.page_home)
        self.scrollArea_2.setObjectName(u"scrollArea_2")
        self.scrollArea_2.setMinimumSize(QSize(400, 470))
        self.scrollArea_2.setStyleSheet(u"    QScrollArea {\n"
"        border: 2px solid black;      /* \u9ed1\u8272\u8fb9\u6846\uff0c\u5bbd\u5ea6\u4e3a2px */\n"
"        border-radius: 10px;          /* \u8fb9\u89d2\u5706\u6da6\uff0c\u534a\u5f84\u4e3a10px */\n"
"        padding: 5px;                 /* \u5185\u8fb9\u8ddd */\n"
"    }")
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollAreaWidgetContents_2 = QWidget()
        self.scrollAreaWidgetContents_2.setObjectName(u"scrollAreaWidgetContents_2")
        self.scrollAreaWidgetContents_2.setGeometry(QRect(0, 0, 571, 607))
        self.verticalLayout_4 = QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_LED_device = QLabel(self.scrollAreaWidgetContents_2)
        self.label_LED_device.setObjectName(u"label_LED_device")
        self.label_LED_device.setMinimumSize(QSize(30, 30))
        self.label_LED_device.setMaximumSize(QSize(30, 30))
        self.label_LED_device.setStyleSheet(u"    QLabel {\n"
"        width: 30px;\n"
"        height: 30px;\n"
"        border-radius: 15px;\n"
"        background-color: green;\n"
"        border: 2px solid black;\n"
"    }")

        self.horizontalLayout_8.addWidget(self.label_LED_device)

        self.label_device_info = QLabel(self.scrollAreaWidgetContents_2)
        self.label_device_info.setObjectName(u"label_device_info")
        self.label_device_info.setMinimumSize(QSize(370, 30))
        self.label_device_info.setMaximumSize(QSize(370, 30))
        self.label_device_info.setStyleSheet(u"color: white;")

        self.horizontalLayout_8.addWidget(self.label_device_info)


        self.verticalLayout_4.addLayout(self.horizontalLayout_8)

        self.pushButton_menu = QPushButton(self.scrollAreaWidgetContents_2)
        self.pushButton_menu.setObjectName(u"pushButton_menu")
        self.pushButton_menu.setMinimumSize(QSize(530, 51))
        self.pushButton_menu.setMaximumSize(QSize(530, 51))
        font = QFont()
        font.setPointSize(26)
        self.pushButton_menu.setFont(font)
        self.pushButton_menu.setStyleSheet(u"   background-color: rgb(128,128,128);   /* \u80cc\u666f\u900f\u660e */")
        icon = QIcon()
        icon.addFile(u"icon/menu.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_menu.setIcon(icon)
        self.pushButton_menu.setIconSize(QSize(50, 50))

        self.verticalLayout_4.addWidget(self.pushButton_menu)

        self.graphicsView = QGraphicsView(self.scrollAreaWidgetContents_2)
        self.graphicsView.setObjectName(u"graphicsView")
        self.graphicsView.setMinimumSize(QSize(530, 400))
        self.graphicsView.setMaximumSize(QSize(530, 400))
        self.graphicsView.setStyleSheet(u"    QGraphicsView {\n"
"        border: 3px solid black;\n"
"    }")

        self.verticalLayout_4.addWidget(self.graphicsView)

        self.progressBar = QProgressBar(self.scrollAreaWidgetContents_2)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setMinimumSize(QSize(530, 25))
        self.progressBar.setMaximumSize(QSize(530, 25))
        self.progressBar.setValue(24)

        self.verticalLayout_4.addWidget(self.progressBar)

        self.lineEdit_info = QLineEdit(self.scrollAreaWidgetContents_2)
        self.lineEdit_info.setObjectName(u"lineEdit_info")
        self.lineEdit_info.setMinimumSize(QSize(530, 0))
        self.lineEdit_info.setMaximumSize(QSize(530, 16777215))
        self.lineEdit_info.setStyleSheet(u"color: white;\n"
"border: 2px solid gray")

        self.verticalLayout_4.addWidget(self.lineEdit_info)

        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_2)

        self.horizontalLayout_11.addWidget(self.scrollArea_2)

        self.scrollArea = QScrollArea(self.page_home)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setMinimumSize(QSize(240, 600))
        self.scrollArea.setMaximumSize(QSize(240, 9999))
        self.scrollArea.setStyleSheet(u"    QScrollArea {\n"
"        border: 2px solid black;      /* \u9ed1\u8272\u8fb9\u6846\uff0c\u5bbd\u5ea6\u4e3a2px */\n"
"        border-radius: 10px;          /* \u8fb9\u89d2\u5706\u6da6\uff0c\u534a\u5f84\u4e3a10px */\n"
"        padding: 5px;                 /* \u5185\u8fb9\u8ddd */\n"
"    }")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 226, 607))
        self.verticalLayout_3 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer)

        self.label_slide = QLabel(self.scrollAreaWidgetContents)
        self.label_slide.setObjectName(u"label_slide")
        self.label_slide.setMinimumSize(QSize(143, 420))
        self.label_slide.setMaximumSize(QSize(143, 420))
        self.label_slide.setStyleSheet(u"background-color: gray;\n"
"border: 3px solid black;")

        self.horizontalLayout_7.addWidget(self.label_slide)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_2)


        self.verticalLayout_3.addLayout(self.horizontalLayout_7)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_LED_ok = QLabel(self.scrollAreaWidgetContents)
        self.label_LED_ok.setObjectName(u"label_LED_ok")
        self.label_LED_ok.setMinimumSize(QSize(30, 30))
        self.label_LED_ok.setMaximumSize(QSize(30, 30))
        self.label_LED_ok.setStyleSheet(u"    QLabel {\n"
"        width: 30px;\n"
"        height: 30px;\n"
"        border-radius: 15px;\n"
"        background-color: green;\n"
"        border: 2px solid black;\n"
"    }")

        self.horizontalLayout_3.addWidget(self.label_LED_ok)

        self.label_LED_ok_info = QLabel(self.scrollAreaWidgetContents)
        self.label_LED_ok_info.setObjectName(u"label_LED_ok_info")
        self.label_LED_ok_info.setMinimumSize(QSize(141, 30))
        self.label_LED_ok_info.setMaximumSize(QSize(141, 30))
        self.label_LED_ok_info.setStyleSheet(u"color: white;")

        self.horizontalLayout_3.addWidget(self.label_LED_ok_info)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_LED_notok = QLabel(self.scrollAreaWidgetContents)
        self.label_LED_notok.setObjectName(u"label_LED_notok")
        self.label_LED_notok.setMinimumSize(QSize(30, 30))
        self.label_LED_notok.setMaximumSize(QSize(30, 30))
        self.label_LED_notok.setStyleSheet(u"    QLabel {\n"
"        width: 30px;\n"
"        height: 30px;\n"
"        border-radius: 15px;\n"
"        background-color: red;\n"
"        border: 2px solid black;\n"
"    }")

        self.horizontalLayout_4.addWidget(self.label_LED_notok)

        self.label_LED_notok_info = QLabel(self.scrollAreaWidgetContents)
        self.label_LED_notok_info.setObjectName(u"label_LED_notok_info")
        self.label_LED_notok_info.setMinimumSize(QSize(141, 30))
        self.label_LED_notok_info.setMaximumSize(QSize(141, 30))
        self.label_LED_notok_info.setStyleSheet(u"color: white;")

        self.horizontalLayout_4.addWidget(self.label_LED_notok_info)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_LED_run = QLabel(self.scrollAreaWidgetContents)
        self.label_LED_run.setObjectName(u"label_LED_run")
        self.label_LED_run.setMinimumSize(QSize(30, 30))
        self.label_LED_run.setMaximumSize(QSize(30, 30))
        self.label_LED_run.setStyleSheet(u"    QLabel {\n"
"        width: 30px;\n"
"        height: 30px;\n"
"        border-radius: 15px;\n"
"        background-color: yellow;\n"
"        border: 2px solid black;\n"
"    }")

        self.horizontalLayout_5.addWidget(self.label_LED_run)

        self.label_LED_run_info = QLabel(self.scrollAreaWidgetContents)
        self.label_LED_run_info.setObjectName(u"label_LED_run_info")
        self.label_LED_run_info.setMinimumSize(QSize(141, 30))
        self.label_LED_run_info.setMaximumSize(QSize(141, 30))
        self.label_LED_run_info.setStyleSheet(u"color: white;")

        self.horizontalLayout_5.addWidget(self.label_LED_run_info)


        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_LED_notrun = QLabel(self.scrollAreaWidgetContents)
        self.label_LED_notrun.setObjectName(u"label_LED_notrun")
        self.label_LED_notrun.setMinimumSize(QSize(30, 30))
        self.label_LED_notrun.setMaximumSize(QSize(30, 30))
        self.label_LED_notrun.setStyleSheet(u"    QLabel {\n"
"        width: 30px;\n"
"        height: 30px;\n"
"        border-radius: 15px;\n"
"        background-color: gray;\n"
"        border: 2px solid black;\n"
"    }")

        self.horizontalLayout_6.addWidget(self.label_LED_notrun)

        self.label_LED_notrun_info = QLabel(self.scrollAreaWidgetContents)
        self.label_LED_notrun_info.setObjectName(u"label_LED_notrun_info")
        self.label_LED_notrun_info.setMinimumSize(QSize(141, 30))
        self.label_LED_notrun_info.setMaximumSize(QSize(141, 30))
        self.label_LED_notrun_info.setStyleSheet(u"color: white;")

        self.horizontalLayout_6.addWidget(self.label_LED_notrun_info)


        self.verticalLayout_2.addLayout(self.horizontalLayout_6)


        self.verticalLayout_3.addLayout(self.verticalLayout_2)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.horizontalLayout_11.addWidget(self.scrollArea)

        self.label_box = QLabel(self.page_home)
        self.label_box.setObjectName(u"label_box")
        self.label_box.setMinimumSize(QSize(177, 631))
        self.label_box.setMaximumSize(QSize(177, 631))
        self.label_box.setStyleSheet(u"background-image: url(./icon/box.png);")

        self.horizontalLayout_11.addWidget(self.label_box)


        self.verticalLayout_9.addLayout(self.horizontalLayout_11)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.frame_2 = QFrame(self.page_home)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setMaximumSize(QSize(830, 16777215))
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pushButton_start_scan = QPushButton(self.frame_2)
        self.pushButton_start_scan.setObjectName(u"pushButton_start_scan")
        self.pushButton_start_scan.setMinimumSize(QSize(200, 50))
        self.pushButton_start_scan.setMaximumSize(QSize(200, 50))
        self.pushButton_start_scan.setFont(font)
        self.pushButton_start_scan.setStyleSheet(u"    QPushButton:enabled {\n"
"        background-color: rgb(0, 88, 0);  /* \u542f\u7528\u65f6\u7684\u80cc\u666f\u989c\u8272 (\u84dd\u8272) */\n"
"        color: white;                        /* \u6587\u5b57\u989c\u8272 */\n"
"    }\n"
"    QPushButton:disabled {\n"
"        background-color: rgb(169, 169, 169);  /* \u7981\u7528\u65f6\u7684\u80cc\u666f\u989c\u8272 (\u7070\u8272) */\n"
"        color: gray;                           /* \u6587\u5b57\u989c\u8272 */\n"
"    }")
        icon1 = QIcon()
        icon1.addFile(u"icon/start.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_start_scan.setIcon(icon1)
        self.pushButton_start_scan.setIconSize(QSize(50, 50))

        self.horizontalLayout_2.addWidget(self.pushButton_start_scan)

        self.pushButton_pause_scan = QPushButton(self.frame_2)
        self.pushButton_pause_scan.setObjectName(u"pushButton_pause_scan")
        self.pushButton_pause_scan.setMinimumSize(QSize(200, 50))
        self.pushButton_pause_scan.setMaximumSize(QSize(200, 50))
        self.pushButton_pause_scan.setFont(font)
        self.pushButton_pause_scan.setStyleSheet(u"    QPushButton:enabled {\n"
"        background-color: rgb(0, 88, 0);  /* \u542f\u7528\u65f6\u7684\u80cc\u666f\u989c\u8272 (\u84dd\u8272) */\n"
"        color: white;                        /* \u6587\u5b57\u989c\u8272 */\n"
"    }\n"
"    QPushButton:disabled {\n"
"        background-color: rgb(169, 169, 169);  /* \u7981\u7528\u65f6\u7684\u80cc\u666f\u989c\u8272 (\u7070\u8272) */\n"
"        color: gray;                           /* \u6587\u5b57\u989c\u8272 */\n"
"    }")
        icon2 = QIcon()
        icon2.addFile(u"icon/pause.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_pause_scan.setIcon(icon2)
        self.pushButton_pause_scan.setIconSize(QSize(50, 50))

        self.horizontalLayout_2.addWidget(self.pushButton_pause_scan)

        self.pushButton_continue_scan = QPushButton(self.frame_2)
        self.pushButton_continue_scan.setObjectName(u"pushButton_continue_scan")
        self.pushButton_continue_scan.setMinimumSize(QSize(200, 50))
        self.pushButton_continue_scan.setMaximumSize(QSize(200, 50))
        self.pushButton_continue_scan.setFont(font)
        self.pushButton_continue_scan.setStyleSheet(u"    QPushButton:enabled {\n"
"        background-color: rgb(0, 88, 0);  /* \u542f\u7528\u65f6\u7684\u80cc\u666f\u989c\u8272 (\u84dd\u8272) */\n"
"        color: white;                        /* \u6587\u5b57\u989c\u8272 */\n"
"    }\n"
"    QPushButton:disabled {\n"
"        background-color: rgb(169, 169, 169);  /* \u7981\u7528\u65f6\u7684\u80cc\u666f\u989c\u8272 (\u7070\u8272) */\n"
"        color: gray;                           /* \u6587\u5b57\u989c\u8272 */\n"
"    }")
        icon3 = QIcon()
        icon3.addFile(u"icon/continue.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_continue_scan.setIcon(icon3)
        self.pushButton_continue_scan.setIconSize(QSize(50, 50))

        self.horizontalLayout_2.addWidget(self.pushButton_continue_scan)

        self.pushButton_stop_scan = QPushButton(self.frame_2)
        self.pushButton_stop_scan.setObjectName(u"pushButton_stop_scan")
        self.pushButton_stop_scan.setMinimumSize(QSize(200, 50))
        self.pushButton_stop_scan.setMaximumSize(QSize(200, 50))
        self.pushButton_stop_scan.setFont(font)
        self.pushButton_stop_scan.setStyleSheet(u"    QPushButton:enabled {\n"
"        background-color: rgb(0, 88, 0);  /* \u542f\u7528\u65f6\u7684\u80cc\u666f\u989c\u8272 (\u84dd\u8272) */\n"
"        color: white;                        /* \u6587\u5b57\u989c\u8272 */\n"
"    }\n"
"    QPushButton:disabled {\n"
"        background-color: rgb(169, 169, 169);  /* \u7981\u7528\u65f6\u7684\u80cc\u666f\u989c\u8272 (\u7070\u8272) */\n"
"        color: gray;                           /* \u6587\u5b57\u989c\u8272 */\n"
"    }")
        icon4 = QIcon()
        icon4.addFile(u"icon/stop.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_stop_scan.setIcon(icon4)
        self.pushButton_stop_scan.setIconSize(QSize(50, 50))

        self.horizontalLayout_2.addWidget(self.pushButton_stop_scan)


        self.horizontalLayout_10.addWidget(self.frame_2)

        self.label_display_box_task = QLabel(self.page_home)
        self.label_display_box_task.setObjectName(u"label_display_box_task")
        self.label_display_box_task.setMinimumSize(QSize(168, 21))
        self.label_display_box_task.setMaximumSize(QSize(168, 21))
        self.label_display_box_task.setLayoutDirection(Qt.LeftToRight)
        self.label_display_box_task.setStyleSheet(u"color: white;\n"
"")
        self.label_display_box_task.setTextFormat(Qt.AutoText)
        self.label_display_box_task.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_10.addWidget(self.label_display_box_task)


        self.verticalLayout_9.addLayout(self.horizontalLayout_10)

        self.stackedWidget.addWidget(self.page_home)
        self.page_log_in = QWidget()
        self.page_log_in.setObjectName(u"page_log_in")
        self.verticalLayout_6 = QVBoxLayout(self.page_log_in)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(-1, -1, -1, 300)
        self.verticalSpacer = QSpacerItem(1007, 14, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_14.addItem(self.horizontalSpacer_3)

        self.label = QLabel(self.page_log_in)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(371, 300))
        self.label.setMaximumSize(QSize(371, 300))
        self.label.setStyleSheet(u"background-image: url(./icon/huaxi.png);")

        self.horizontalLayout_14.addWidget(self.label)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_14.addItem(self.horizontalSpacer_4)


        self.verticalLayout_5.addLayout(self.horizontalLayout_14)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_7)

        self.label_usename = QLabel(self.page_log_in)
        self.label_usename.setObjectName(u"label_usename")
        self.label_usename.setMinimumSize(QSize(81, 31))
        self.label_usename.setMaximumSize(QSize(81, 31))
        self.label_usename.setStyleSheet(u"color: white;")

        self.horizontalLayout.addWidget(self.label_usename)

        self.lineEdit_usename = QLineEdit(self.page_log_in)
        self.lineEdit_usename.setObjectName(u"lineEdit_usename")
        self.lineEdit_usename.setMinimumSize(QSize(201, 31))
        self.lineEdit_usename.setMaximumSize(QSize(201, 31))
        self.lineEdit_usename.setStyleSheet(u"color: white;")

        self.horizontalLayout.addWidget(self.lineEdit_usename)

        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_10)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_8)

        self.label_password = QLabel(self.page_log_in)
        self.label_password.setObjectName(u"label_password")
        self.label_password.setMinimumSize(QSize(81, 31))
        self.label_password.setMaximumSize(QSize(81, 31))
        self.label_password.setStyleSheet(u"color: white;")

        self.horizontalLayout_12.addWidget(self.label_password)

        self.lineEdit_password = QLineEdit(self.page_log_in)
        self.lineEdit_password.setObjectName(u"lineEdit_password")
        self.lineEdit_password.setMinimumSize(QSize(201, 31))
        self.lineEdit_password.setMaximumSize(QSize(201, 31))
        self.lineEdit_password.setStyleSheet(u"color: white;")

        self.horizontalLayout_12.addWidget(self.lineEdit_password)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_9)


        self.verticalLayout.addLayout(self.horizontalLayout_12)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_5)

        self.pushButton_login = QPushButton(self.page_log_in)
        self.pushButton_login.setObjectName(u"pushButton_login")
        self.pushButton_login.setMinimumSize(QSize(151, 51))
        self.pushButton_login.setMaximumSize(QSize(16777215, 51))
        self.pushButton_login.setStyleSheet(u"    QPushButton:enabled {\n"
"        background-color: rgb(0, 88, 0);  /* \u542f\u7528\u65f6\u7684\u80cc\u666f\u989c\u8272 (\u84dd\u8272) */\n"
"        color: white;                        /* \u6587\u5b57\u989c\u8272 */\n"
"    }\n"
"    QPushButton:disabled {\n"
"        background-color: rgb(169, 169, 169);  /* \u7981\u7528\u65f6\u7684\u80cc\u666f\u989c\u8272 (\u7070\u8272) */\n"
"        color: gray;                           /* \u6587\u5b57\u989c\u8272 */\n"
"    }")

        self.horizontalLayout_13.addWidget(self.pushButton_login)

        self.pushButton_login_cancel = QPushButton(self.page_log_in)
        self.pushButton_login_cancel.setObjectName(u"pushButton_login_cancel")
        self.pushButton_login_cancel.setMinimumSize(QSize(151, 51))
        self.pushButton_login_cancel.setMaximumSize(QSize(16777215, 51))
        self.pushButton_login_cancel.setStyleSheet(u"    QPushButton:enabled {\n"
"        background-color: rgb(0, 88, 0);  /* \u542f\u7528\u65f6\u7684\u80cc\u666f\u989c\u8272 (\u84dd\u8272) */\n"
"        color: white;                        /* \u6587\u5b57\u989c\u8272 */\n"
"    }\n"
"    QPushButton:disabled {\n"
"        background-color: rgb(169, 169, 169);  /* \u7981\u7528\u65f6\u7684\u80cc\u666f\u989c\u8272 (\u7070\u8272) */\n"
"        color: gray;                           /* \u6587\u5b57\u989c\u8272 */\n"
"    }")

        self.horizontalLayout_13.addWidget(self.pushButton_login_cancel)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_6)


        self.verticalLayout.addLayout(self.horizontalLayout_13)


        self.verticalLayout_5.addLayout(self.verticalLayout)


        self.verticalLayout_6.addLayout(self.verticalLayout_5)

        self.verticalSpacer_2 = QSpacerItem(1007, 142, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer_2)

        self.stackedWidget.addWidget(self.page_log_in)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1024, 17))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label_time.setText("")
        self.label_display_usename.setText(QCoreApplication.translate("MainWindow", u"\u5f53\u524d\u7528\u6237\uff1a111", None))
        self.pushButton_log_off.setText(QCoreApplication.translate("MainWindow", u"\u9000\u51fa\u767b\u5f55", None))
        self.label_LED_device.setText("")
        self.label_device_info.setText(QCoreApplication.translate("MainWindow", u"\u8bbe\u5907\u6b63\u5728\u8fd0\u884c", None))
        self.pushButton_menu.setText(QCoreApplication.translate("MainWindow", u"\u626b\u63cf\u65b9\u6848", None))
        self.lineEdit_info.setText(QCoreApplication.translate("MainWindow", u"\u5f53\u524d\u6b63\u5728\u4f4e\u500d5X\u626b\u63cf", None))
        self.label_slide.setText("")
        self.label_LED_ok.setText("")
        self.label_LED_ok_info.setText(QCoreApplication.translate("MainWindow", u"\u5df2\u5b8c\u6210\u73bb\u7247\u626b\u63cf\uff1a10\u7247", None))
        self.label_LED_notok.setText("")
        self.label_LED_notok_info.setText(QCoreApplication.translate("MainWindow", u"\u73bb\u7247\u626b\u63cf\u5931\u8d25\uff1a 0\u7247", None))
        self.label_LED_run.setText("")
        self.label_LED_run_info.setText(QCoreApplication.translate("MainWindow", u"\u5f53\u524d\u6b63\u5728\u626b\u63cf\u7b2c11\u7247", None))
        self.label_LED_notrun.setText("")
        self.label_LED_notrun_info.setText(QCoreApplication.translate("MainWindow", u"\u7b49\u5f85\u626b\u63cf\uff1a13\u7247", None))
        self.label_box.setText("")
        self.pushButton_start_scan.setText(QCoreApplication.translate("MainWindow", u"\u5f00\u59cb\u626b\u63cf", None))
        self.pushButton_pause_scan.setText(QCoreApplication.translate("MainWindow", u"\u6682\u505c\u626b\u63cf", None))
        self.pushButton_continue_scan.setText(QCoreApplication.translate("MainWindow", u"\u7ee7\u7eed\u626b\u63cf", None))
        self.pushButton_stop_scan.setText(QCoreApplication.translate("MainWindow", u"\u505c\u6b62\u626b\u63cf", None))
        self.label_display_box_task.setText(QCoreApplication.translate("MainWindow", u"\u4eca\u65e5\u626b\u63cf\u7b2c1\u76d2", None))
        self.label.setText("")
        self.label_usename.setText(QCoreApplication.translate("MainWindow", u"\u7528\u6237\u540d", None))
        self.label_password.setText(QCoreApplication.translate("MainWindow", u"\u5bc6\u7801", None))
        self.pushButton_login.setText(QCoreApplication.translate("MainWindow", u"\u767b\u5f55", None))
        self.pushButton_login_cancel.setText(QCoreApplication.translate("MainWindow", u"\u53d6\u6d88", None))
    # retranslateUi

