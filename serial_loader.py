###玻片装载器设备自检测试
from Drives.loadercontroller import LoaderController


class SerialLoader:
    def __init__(self, COM, COMoil, oil_flag):
        self.COM = COM
        self.COMoil = COMoil
        self.oil_flag = oil_flag

    def open(self):
        self.Loader = LoaderController(self.COM, self.COMoil, self.oil_flag)
        self.Loader.reset_xyz()

    def close(self):
        self.Loader.ser_close()
