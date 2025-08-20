# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plan.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(1024, 768)
        Dialog.setMinimumSize(QSize(1024, 768))
        Dialog.setMaximumSize(QSize(1024, 768))
        Dialog.setStyleSheet(u"background-color: #282c34;")
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.listWidget = QListWidget(Dialog)
        self.listWidget.setObjectName(u"listWidget")
        font = QFont()
        font.setPointSize(26)
        self.listWidget.setFont(font)
        self.listWidget.setStyleSheet(u"    QListWidget {\n"
"        spacing: 5px;  /* \u8bbe\u7f6e\u884c\u95f4\u8ddd */\n"
"color: white;\n"
"    }\n"
"    QListWidget::item {\n"
"        padding: 10px;  /* \u8bbe\u7f6e\u6bcf\u4e2a\u9879\u76ee\u7684\u5185\u8fb9\u8ddd\uff0c\u589e\u52a0\u95f4\u9694 */\n"
"color: white;\n"
"    }\n"
"    QListWidget::item:selected {\n"
"        background-color: rgb(0, 255, 0);  /* \u9009\u4e2d\u9879\u80cc\u666f\u989c\u8272\u4e3a\u7eff\u8272 */\n"
"        color: white;  /* \u9009\u4e2d\u9879\u6587\u5b57\u989c\u8272\u4e3a\u767d\u8272 */\n"
"    }")

        self.verticalLayout.addWidget(self.listWidget)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_ok = QPushButton(Dialog)
        self.pushButton_ok.setObjectName(u"pushButton_ok")
        self.pushButton_ok.setMinimumSize(QSize(200, 50))
        self.pushButton_ok.setMaximumSize(QSize(200, 50))
        self.pushButton_ok.setFont(font)
        self.pushButton_ok.setStyleSheet(u"    QPushButton:enabled {\n"
"        background-color: rgb(0, 88, 0);  /* \u542f\u7528\u65f6\u7684\u80cc\u666f\u989c\u8272 (\u84dd\u8272) */\n"
"        color: white;                        /* \u6587\u5b57\u989c\u8272 */\n"
"    }\n"
"    QPushButton:disabled {\n"
"        background-color: rgb(169, 169, 169);  /* \u7981\u7528\u65f6\u7684\u80cc\u666f\u989c\u8272 (\u7070\u8272) */\n"
"        color: gray;                           /* \u6587\u5b57\u989c\u8272 */\n"
"    }")

        self.horizontalLayout.addWidget(self.pushButton_ok)

        self.pushButton_cancel = QPushButton(Dialog)
        self.pushButton_cancel.setObjectName(u"pushButton_cancel")
        self.pushButton_cancel.setMinimumSize(QSize(200, 50))
        self.pushButton_cancel.setMaximumSize(QSize(200, 50))
        self.pushButton_cancel.setFont(font)
        self.pushButton_cancel.setStyleSheet(u"    QPushButton:enabled {\n"
"        background-color: rgb(0, 88, 0);  /* \u542f\u7528\u65f6\u7684\u80cc\u666f\u989c\u8272 (\u84dd\u8272) */\n"
"        color: white;                        /* \u6587\u5b57\u989c\u8272 */\n"
"    }\n"
"    QPushButton:disabled {\n"
"        background-color: rgb(169, 169, 169);  /* \u7981\u7528\u65f6\u7684\u80cc\u666f\u989c\u8272 (\u7070\u8272) */\n"
"        color: gray;                           /* \u6587\u5b57\u989c\u8272 */\n"
"    }")

        self.horizontalLayout.addWidget(self.pushButton_cancel)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.pushButton_ok.setText(QCoreApplication.translate("Dialog", u"\u786e\u5b9a", None))
        self.pushButton_cancel.setText(QCoreApplication.translate("Dialog", u"\u53d6\u6d88", None))
    # retranslateUi

