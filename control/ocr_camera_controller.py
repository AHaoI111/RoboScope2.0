import cv2


class ocr_camera:
    def __init__(self, angle):
        self.cap = None
        self.angle = angle

    def check_ocr_camera(self):
        for i in range(10):  # 假设最多有5个相机
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                print(f"相机 {i} 已连接")
                cap.release()
                return True
        return False

    def open(self, cameraexposure, width, height):

        for i in range(10):  # 假设最多有5个相机
            self.cap = cv2.VideoCapture(i)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_EXPOSURE, cameraexposure)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)  # 宽度为2592像素
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)  # 高度为1944像素
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                flag = self.cap.grab()
                ret, frame = self.cap.retrieve()
                return

    def read_image(self):
        for i in range(2):
            flag = self.cap.grab()
        ret, frame = self.cap.retrieve()
        # 如果成功获取到图像
        if ret:
            # 裁剪图片，假设裁剪区域是 (x_start, y_start, x_end, y_end)
            x_start, y_start, x_end, y_end = 236, 195, 2560, 991
            cropped_image = frame[y_start:y_end, x_start:x_end]

            # 逆时针旋转90度
            if self.angle == 90:
                cropped_image = cv2.rotate(cropped_image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            elif self.angle == 180:
                cropped_image = cv2.rotate(cropped_image, cv2.ROTATE_180)
            elif self.angle == 270:
                cropped_image = cv2.rotate(cropped_image, cv2.ROTATE_90_CLOCKWISE)
            return cropped_image
        else:
            return None

    def close(self):
        self.cap.release()
