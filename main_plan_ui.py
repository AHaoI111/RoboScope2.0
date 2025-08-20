from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Slot, Signal

from gui_plan import Ui_Dialog


class MyDialog(QDialog):
    button_signal = Signal(str)

    def __init__(self):
        super().__init__()

        # 初始化 Ui_Dialog 类并设置界面
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.pushButton_ok.clicked.connect(self.sure)
        self.ui.pushButton_cancel.clicked.connect(self.cancel)

    def sure(self):
        selected_items = self.ui.listWidget.selectedItems()
        # 检查是否有选中项
        if selected_items:
            # 获取第一个选中项的文本
            selected_text = selected_items[0].text()
            self.button_signal.emit(str(selected_text))
        else:
            self.button_signal.emit('')

    def cancel(self):
        self.button_signal.emit('')
