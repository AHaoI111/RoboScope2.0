# -*- encoding: utf-8 -*-
"""
@Description:
该文件用于做测试装载器与显微镜运动测试任务
@File    :   taskwork_test_loader.py
@Time    :   2024/07/16
@Author  :   Li QingHao
@Version :   3.0
@Time_END :  最后修改时间：20240905
@Developers_END :  最后修改作者：
"""

import time
import uuid
from datetime import datetime


def get_time_2():
    # 获取当前系统时间
    current_time = datetime.now()
    # 格式化时间显示
    year = current_time.strftime("%Y")
    month = current_time.strftime("%m")
    day = current_time.strftime("%d")
    return year, month, day


class Task:

    def __init__(self, action_loader, action_mircoscope, Scanning):
        super().__init__()

        self.number_next = 0
        self.logger = None
        self.pic_label = None
        self.request = None
        self.slide_task = None

        self.action_loader = action_loader
        self.action_mircoscope = action_mircoscope
        self.Scanning = Scanning
        self.action_mircoscope.flag = True
        self.action_mircoscope.flage_run = True

        self.task_flag = True
        self.task_run_flag = True

    def run(self, Taskinfo, slide_list):
        """
        执行自动送片加扫描的任务流程。
        此方法首先使设备复位，然后按照预设的点位信息进行片子的自动取出、送至显微镜、扫描、再放回装载器的过程。
        该过程中涉及显微镜与装载器的多次协作动作。
        """
        try:
            # 复位
            self.number_next = 0
            self.action_mircoscope.microscope_homezxy()
            self.task_flag = True
            self.task_run_flag = True
            elapsed_time = 0
            # 获取任务的ID
            if Taskinfo['task_id'] is None:
                task_id = str(uuid.uuid4())  # 生成一个 UUID
                Taskinfo['task_id'] = task_id
            else:
                task_id = Taskinfo['task_id']
            # self.action_loader.open_camera()
            if Taskinfo['pre_request_flag']:
                boxes = [1]

            count_box = len(slide_list)
            count_slide = 0
            start_box = 1
            # 遍历盒子
            for slides in slide_list:
                if self.task_run_flag:
                    pass
                else:
                    break
                # 该盒子需要扫描
                if Taskinfo['pre_request_flag']:
                    slide__points = self.action_loader.pre_get_box_points(start_box)
                else:
                    slide__points = self.action_loader.get_box_points(start_box)
                number = list(range(1, len(slide__points) + 1))
                # 确保列表中存在0(0表示需要扫描玻片，1表示不需要扫描)
                if 0 in slides:
                    # 找最后一个0表示任务
                    last_zero_index = len(slides) - 1 - slides[::-1].index(0)
                else:
                    last_zero_index = -1
                for task, point_xz, num in zip(slides, slide__points, number):
                    if self.number_next >= 2:
                        break
                    if task == 0:
                        if self.task_flag:
                            pass
                        else:
                            while not self.task_flag:
                                time.sleep(0.01)
                        if self.task_run_flag:
                            pass
                        else:
                            break
                        start_time = time.time()  # 记录开始时间
                        # 移动到盒子取玻片处
                        self.action_loader.move_x_to(point_xz[0])
                        self.action_loader.move_z_to(point_xz[1])
                        # 取片(动作为y伸出、z上台、y回收)
                        self.action_loader.get_slide_from_box(point_xz[1])
                        if self.action_loader.loader.is_warning:
                            self.task_run_flag = False
                            break
                        # 移动至拍摄
                        self.action_loader.loader_move2_camera()
                        # 相机拍摄玻片图片
                        label_img = self.action_loader.capture_image()
                        self.pic_label = label_img
                        if label_img is None:
                            slide_id = None
                        else:
                            # 发送请求玻片的uuid
                            if Taskinfo['pre_request_flag']:
                                slide_id = str(uuid.uuid4())
                            else:
                                if self.request is None:
                                    slide_id = str(uuid.uuid4())
                                    Taskinfo['flag_create_view'] = False
                                else:
                                    if Taskinfo['name'] == 'default':
                                        slide_id = str(uuid.uuid4())
                                        Taskinfo['flag_create_view'] = False
                                    else:
                                        year, month, day = get_time_2()
                                        slide_id = self.request.create_slide_id(Taskinfo['task_id'],
                                                                                '/' + year + '/' + month + '/' + day + '/' +
                                                                                Taskinfo['task_id'] + '/',
                                                                                label_img)
                                        Taskinfo['flag_create_view'] = True

                        if slide_id is not None:
                            self.action_mircoscope.move_2_loader_get_wait(Taskinfo['Xend'], Taskinfo['Yend'])
                            self.number_next = 0
                            # 移动至显微镜处
                            self.action_loader.move_2_microscope_give_location()
                            # 显微镜移动至交接处(确认)
                            self.action_mircoscope.wait_busy()
                            # 放片到载物台
                            self.action_loader.give_slide_to_microscope()
                            if self.action_loader.loader.is_warning:
                                self.task_run_flag = False
                                break
                            # 避位
                            self.action_loader.loader_avoid()
                            self.action_loader.disenble_motor()
                            # 扫描
                            self.Scanning.start(Taskinfo, slide_id, self.pic_label, use_pump=self.action_loader.pump)
                            # 显微镜移动至交接处
                            self.action_mircoscope.move_2_loader_give(Taskinfo['Xend'], Taskinfo['Yend'])
                            # 移动至显微镜处下方
                            self.action_loader.move_2_microscope_get_location()
                            # 取片
                            self.action_loader.get_slide_from_microscope()
                            if self.action_loader.loader.is_warning:
                                self.task_run_flag = False
                                break
                            # 显微镜复位
                            self.action_mircoscope.microscope_homezxy_wait()
                            # 返回玻片仓位置放片
                            self.action_loader.move_x_to(point_xz[0])
                            self.action_loader.move_z_to(point_xz[1] - self.action_loader.boxzgap)
                            # 放片
                            self.action_loader.give_slide_to_box(point_xz[1] - self.action_loader.boxzgap)
                            if self.action_loader.loader.is_warning:
                                self.task_run_flag = False
                                break
                            self.action_mircoscope.wait_busy()
                            if num == (last_zero_index + 1):
                                # 处理最后一片
                                if Taskinfo['pre_request_flag']:
                                    pass
                                else:
                                    self.action_loader.last_slide_process(point_xz[1] - self.action_loader.boxzgap)
                        else:
                            # 移动回去放
                            self.number_next = self.number_next + 1
                            # 返回玻片仓位置放片
                            self.action_loader.move_x_to(point_xz[0])
                            self.action_loader.move_z_to(point_xz[1] - self.action_loader.boxzgap)
                            # 放片
                            self.action_loader.give_slide_to_box(point_xz[1] - self.action_loader.boxzgap)
                            if self.action_loader.loader.is_warning:
                                self.task_run_flag = False
                                break
                            if num == (last_zero_index + 1):
                                # 处理最后一片
                                if Taskinfo['pre_request_flag']:
                                    pass
                                else:
                                    self.action_loader.last_slide_process(point_xz[1] - self.action_loader.boxzgap)
                        end_time = time.time()  # 记录结束时间
                        elapsed_time = end_time - start_time  # 计算耗时
                    elif task == 1:
                        pass

                    count_slide = count_slide + 1

            if self.task_run_flag:
                if self.request is not None:
                    status, data = self.request.finfish_task(task_id)

                self.action_loader.loader_move_xyz_0()
        except Exception as e:
            print(str(e))
            pass

    def pause(self):
        self.task_flag = False
        self.Scanning.pause()


class Task_microscope():

    def __init__(self, action_mircoscope, Scanning):
        super().__init__()

        self.number_next = 0
        self.logger = None
        self.pic_label = None
        self.request = None
        self.slide_task = None

        self.action_mircoscope = action_mircoscope
        self.Scanning = Scanning
        self.action_mircoscope.flag = True
        self.action_mircoscope.flage_run = True

        self.task_flag = True
        self.task_run_flag = True

    def run(self, Taskinfo):
        """
        执行自动送片加扫描的任务流程。
        此方法首先使设备复位，然后按照预设的点位信息进行片子的自动取出、送至显微镜、扫描、再放回装载器的过程。
        该过程中涉及显微镜与装载器的多次协作动作。
        """
        try:
            # 复位
            self.pic_label = None
            self.number_next = 0
            self.write_log_task.emit(0, "当前扫描配置" + str(Taskinfo))
            self.action_mircoscope.microscope_homezxy()

            self.task_flag = True
            self.task_run_flag = True
            elapsed_time = 0
            # 获取任务的ID
            if Taskinfo['task_id'] is None:
                task_id = str(uuid.uuid4())  # 生成一个 UUID
                Taskinfo['task_id'] = task_id
            else:
                task_id = Taskinfo['task_id']
            start_time = time.time()  # 记录开始时间
            # 发送请求玻片的uuid
            if Taskinfo['pre_request_flag']:
                slide_id = str(uuid.uuid4())
                self.updata_textEdit_log_task.emit("生成预扫玻片id:" + slide_id)
                self.write_log_task.emit(0, "生成预扫玻片id:" + slide_id)
            else:
                if self.request is None:
                    slide_id = str(uuid.uuid4())
                    self.updata_textEdit_log_task.emit("生成玻片id:" + slide_id)
                    self.write_log_task.emit(0, "生成玻片id:" + slide_id)
                    Taskinfo['flag_create_view'] = False
                else:
                    year, month, day = get_time_2()
                    self.updata_textEdit_log_task.emit("发送请求申请slide ID")
                    self.write_log_task.emit(0, "发送请求申请slide ID")
                    slide_id = self.request.create_slide_id(Taskinfo['task_id'],
                                                            '/' + year + '/' + month + '/' + day + '/' +
                                                            Taskinfo['task_id'] + '/',
                                                            self.pic_label)
                    if slide_id is not None:
                        self.updata_textEdit_log_task.emit("生成玻片id:" + slide_id)
                        self.write_log_task.emit(0, "生成玻片id:" + slide_id)
                    else:
                        self.updata_textEdit_log_task.emit("发送请求申请slide ID失败")
                        self.write_log_task.emit(1, "发送请求申请slide ID失败")
                    Taskinfo['flag_create_view'] = True
            if slide_id is not None:
                # 扫描
                self.updata_textEdit_log_task.emit("显微镜正在扫描")
                self.write_log_task.emit(0, "显微镜正在扫描")
                self.Scanning.start(Taskinfo, slide_id, self.pic_label, use_pump=None)
                # 显微镜复位
                self.updata_textEdit_log_task.emit("开始显微镜复位")
                self.write_log_task.emit(0, "开始显微镜复位")
                self.action_mircoscope.microscope_homezxy_wait()
                self.action_mircoscope.wait_busy()
                self.updata_textEdit_log_task.emit("显微镜复位完成确认")
                self.write_log_task.emit(0, "显微镜复位完成确认")
            self.activate_pushbutton.emit()
        except Exception as e:
            self.activate_pushbutton.emit()
            self.write_log_task.emit(0, "当前扫描失败:" + str(e))
            self.updata_textEdit_log_task.emit("当前扫描失败:" + str(e) + '\n')

    def pause(self):
        self.task_flag = False
        self.Scanning.pause()
        self.updata_textEdit_log_task.emit("正在暂停扫描..." + '\n')
        self.write_log_task.emit(0, "正在暂停扫描")

    # 发送预扫描标签
