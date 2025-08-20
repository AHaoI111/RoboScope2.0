# -*- encoding: utf-8 -*-
'''
@Description:
1.上位机对应的处理程序
@File    :   scannercontroller.py
@Time    :   2025/07/25 
@Author  :   He qing xin
@Version :   2.0

add:
1.read_slide_nums(self,start_pos,end_pos),增加了开始数片的点位的参数
3.light_ocr_ctrl(self,val):增加OCR灯光参数设定的功能
4.enable_motor(self),增加了使能电机的功能

'''
import threading

import crcmod
import time
import serial
import struct
import numpy as np
from threading import Thread



# 显微镜基本控制类
class scannercontroller():
    def __init__(self, port):
        super().__init__()
        # 硬件基本参数定义
        # 螺距
        self.x_pitch_mm = 2.54
        self.y_pitch_mm = 2.54
        self.z_pitch_mm = 0.3175
        self.w_pitch_mm = 1                
        self.ly_pitch_mm = 2.54
        self.lz_pitch_mm = 2.54
        # 电机细分
        self.x_subdivision = 256
        self.y_subdivision = 256     
        self.z_subdivision = 256
        self.w_subdivision = 64  
        self.ly_subdivision = 256
        self.lz_subdivision = 256  
        # 步距角
        self.x_step_angle = 1.8
        self.y_step_angle = 1.8
        self.z_step_angle = 1.8
        self.w_step_angle = 1.8
        self.ly_step_angle = 1.8
        self.lz_step_angle = 1.8
        # 轴当前实际所处的绝对位置
        self.x_input = 0.0
        self.y_input = 0.0
        self.z_input = 0.0
        self.w_input = 0.0
        self.ly_input = 0.0
        self.lz_input = 0.0        
        # 用户从上位机输入的轴即将运动到的位置
        self.x_abspos = 0.0
        self.y_abspos = 0.0
        self.y_abspos = 0.0
        self.w_abspos = 0.0
        self.ly_abspos = 0.0
        self.lz_abspos = 0.0
        # 轴速度设置
        self.x_speed = 0.0
        self.y_speed = 0.0
        self.z_speed = 0.0
        self.w_speed = 0.0
        self.ly_speed = 0.0
        self.lz_speed = 0.0
        self.is_speed = False
        # 限位开关是否被触发
        self.is_limit_let_tri = False
        self.is_limit_rht_tri = False   
        # 限位开关位置
        self.limit_rht_pos = 0.0        
        self.limit_let_pos = 0.0                 
        # 玻片数量
        self.slide_nums = 0
        # 机械轴是否正在工作
        self.is_busy = True
        # 系统是否有警告
        self.is_warning = False
        # 系统是否复位完成
        self.is_reset=False
        self.zero_val=0
        # 电机失能/强停是否完成
        self.is_disenble=False
        # 其他参数设置成功应答
        self.is_setup_ack=False
        # 风扇转速设置成功应答
        self.is_fans_ack =  False
        # RGB氛围灯设置成功应答
        self.is_rgb_ack =  False
        # 玻片数量获取成功应答
        self.is_slide_ack = False
        # 加速度设置成功应答
        self.is_acc_ack =  False   
        # 速度设置成功应答  
        self.is_vel_ack =  False
        # 电机成功停止应答
        self.is_stop_ack =  False  
        # 零点单独设置成功应答
        self.is_zero_ack=False
        # 温度值
        self.is_temp_ack=False 
        self.temp_val = 0.0   
        # 焦距值
        self.is_focus_ack=False 
        self.focus_val = 0.0     
        self.read_cnt = 0   
        self.is_light_ocr_ack=False    
        self.is_eeror_ack=False  
        self.is_enable_ack = False 
        # 玻片数量列表
        self.slide_num_data = [0]*24       
        # 通信串口基本配置
        self.serial = serial.Serial(port, 115200, timeout=0.001)
        self.crc8 = crcmod.predefined.mkPredefinedCrcFun("crc-8")
        time.sleep(2)   
        self.serial_thread = Thread(target=self.read_msg)
        self.serial_thread.start()
        # 串口是否正在运行
        self.flag_run = True

    ##############################主代码################################

    # 上位机串口发送数据帧功能函数(b"\xB3", struct.pack(">i", y))
    def send_cmd_frame(self, cmd_id, axis,data):
        # AA B3 data CRC8
        tx_data = b"\x00" + b"\xAA" + cmd_id + axis + data
        self.serial.flush()
        # self.serial.write(tx_data + self.crc8(tx_data).to_bytes(1, 'big'))
        self.serial.write(tx_data + b"\xff")

    # 机械轴正在工作函数处理
    def wait_busy(self, local):
        self.is_busy = True
        while self.is_busy:
            time.sleep(0.01)  # 延时100ms
            self.read_cnt = self.read_cnt + 1
            # 以精度0.01mm进行判断是否已经到达指定位置，若是则退出循环
            # x轴和z轴使用该busy函数，用于是否已经到达位置，避免错过busy单脉冲信号
            if (local == "x"):
                self.read_abs_pos("x")
                self.get_busy_judge_x(accuracy=0.005)
            elif (local == "y"):
                self.read_abs_pos("y")
                self.get_busy_judge_y(accuracy=0.005)
            elif (local == "z"):
                self.read_abs_pos("z")
                self.get_busy_judge_z(accuracy=0.005)
            elif (local == "w"):
                self.read_abs_pos("w")                    
                self.get_busy_judge_w(accuracy=0.005)
            elif (local == "ly"):
                self.read_abs_pos("ly")                    
                self.get_busy_judge_ly(accuracy=0.005)
            elif (local == "lz"):
                self.read_abs_pos("lz")                    
                self.get_busy_judge_lz(accuracy=0.005) 
            if self.is_limit_rht_tri == True:
                if  self.read_cnt < 30:
                    self.is_busy = True
                else: 
                    self.is_busy = False    
                self.is_limit_rht_tri = False
            elif self.is_limit_let_tri == True:  
                if  self.read_cnt < 30:
                    self.is_busy = True
                else: 
                    self.is_busy = False        
                self.is_limit_let_tri = False  
        self.read_cnt = 0                                                                 

    # 判断x是否到达预定位置
    def get_busy_judge_x(self, accuracy=0.005) -> int:
        # print("x_input={}\n",format(self.x_input ))
        # print("x_abspos={}\n",format(self.x_abspos ))
        # print("dx={}\n",format(np.abs(self.x_input - self.x_abspos) ))
        if (np.abs(self.x_input - self.x_abspos) <= accuracy):  # 若当前坐标和指定坐标的三轴误差都小于0.01mm，则判断就位
            self.is_busy = False


    # 判断y是否到达预定位置
    def get_busy_judge_y(self, accuracy=0.005) -> int:
        # print("y_input={}\n",format(self.y_input ))
        # print("y_abspos={}\n",format(self.y_abspos ))
        # print("dy={}\n",format(np.abs(self.y_input - self.y_abspos) ))        
        if (np.abs(self.y_input - self.y_abspos) <= accuracy):
            self.is_busy = False

    # 判断z是否到达预定位置
    def get_busy_judge_z(self, accuracy=0.005) -> int:
        # print("z_input={}\n",format(self.z_input ))
        # print("z_abspos={}\n",format(self.z_abspos ))
        # print("dz={}\n",format(np.abs(self.z_input - self.z_abspos) ))           
        if (np.abs(self.z_input - self.z_abspos) <= accuracy):
            # 若当前坐标和指定坐标的三轴误差都小于5mm，则判断就位
            self.is_busy = False

    # 判断w是否到达预定位置
    def get_busy_judge_w(self, accuracy=0.005) -> int:
        # print("w_input={}\n",format(self.w_input ))
        # print("w_abspos={}\n",format(self.w_abspos ))
        # print("dw={}\n",format(np.abs(self.w_input - self.w_abspos) ))            
        if (np.abs(self.w_input - self.w_abspos) <= accuracy):
            # 若当前坐标和指定坐标的三轴误差都小于5mm，则判断就位
            self.is_busy = False

    # 判断lz是否到达预定位置
    def get_busy_judge_ly(self, accuracy=0.005) -> int:
        if (np.abs(self.ly_input - self.ly_abspos) <= accuracy):
            # 若当前坐标和指定坐标的三轴误差都小于5mm，则判断就位
            self.is_busy = False

    # 判断ly是否到达预定位置
    def get_busy_judge_lz(self, accuracy=0.005) -> int:
        if (np.abs(self.lz_input - self.lz_abspos) <= accuracy):
            # 若当前坐标和指定坐标的三轴误差都小于5mm，则判断就位
            self.is_busy = False

    ###################################绝对位置控制############################################
    # 控制x轴移动绝对距离
    def set_delivery_abs_x(self, x):
        self.x_abspos = x
        abspos = int(((self.x_abspos / self.x_pitch_mm) * 360 / (self.x_step_angle/ self.x_subdivision))*(-1))
        self.send_cmd_frame(b"\xB1", b"\x00", struct.pack(">i", abspos))
        self.wait_busy(local="x")

    # 控制y轴移动绝对距离
    def set_delivery_abs_y(self, y):
        self.y_abspos = y
        abspos = int(((self.y_abspos / self.y_pitch_mm) * 360 / (self.y_step_angle/ self.y_subdivision))*(-1))
        self.send_cmd_frame(b"\xB1", b"\x01", struct.pack(">i", abspos))
        self.wait_busy(local="y")

    # 控制z轴移动绝对距离
    def set_delivery_abs_z(self, z):
        self.z_abspos = z
        if self.z_abspos > 6.95:
            self.z_abspos = 6.95
        abspos = int((self.z_abspos / self.z_pitch_mm) * 360 / (self.z_step_angle/ self.z_subdivision))
        self.send_cmd_frame(b"\xB1", b"\x02", struct.pack(">i", abspos))
        # self.read_abs_pos("z") 
        # if self.is_limit_rht_tri or self.is_limit_let_tri:
        #     time.sleep(0.2)
        # self.read_abs_pos("z")
        self.wait_busy(local="z")

    # 控制w轴移动绝对距离
    def set_delivery_abs_w(self, w):
        self.w_abspos = w
        abspos = int((self.w_abspos / self.w_pitch_mm) * 360 / (self.w_step_angle/ self.w_subdivision))
        self.send_cmd_frame(b"\xB1", b"\x03", struct.pack(">i", abspos))
        # self.read_abs_pos("w") 
        # if self.is_limit_rht_tri or self.is_limit_let_tri:
        #     time.sleep(0.2)
        # self.read_abs_pos("w")
        self.wait_busy(local="w")        

    # 选择1号物镜
    def select_objective_num1(self):
        self.set_delivery_abs_w(0.68)

    # 选择2号物镜
    def select_objective_num2(self):
        self.set_delivery_abs_w(1.367)

    # 选择3号物镜
    def select_objective_num3(self):
        self.set_delivery_abs_w(2.052)

    # 选择4号物镜
    def select_objective_num4(self):
        self.set_delivery_abs_w(2.74)

    # 控制ly轴移动绝对距离
    def set_delivery_abs_ly(self, ly):
        self.ly_abspos = ly
        abspos = int(((self.ly_abspos  / self.ly_pitch_mm) * 360 / (self.ly_step_angle/ self.ly_subdivision))*(-1))
        self.send_cmd_frame(b"\xB1", b"\x04", struct.pack(">i", abspos))
        self.wait_busy(local="ly")

    # 控制lz轴移动绝对距离
    def set_delivery_abs_lz(self, lz):
        self.lz_abspos = lz
        abspos = int(((self.lz_abspos / self.lz_pitch_mm) * 360 / (self.lz_step_angle/ self.lz_subdivision))*(-1))
        self.send_cmd_frame(b"\xB1", b"\x05", struct.pack(">i", abspos))
        self.wait_busy(local="lz")


    # 控制xy轴同时运动绝对距离
    def set_delivery_abs_xy(self, x, y):
        self.x_abspos = x
        self.abspos = int((x / self.x_pitch_mm) * 360 / (self.x_step_angle/ self.x_subdivision))
        self.y_abspos = y
        self.abspos = int((y / self.y_pitch_mm) * 360 / (self.y_step_angle/ self.y_subdivision))
        self.send_cmd_frame(b"\xB1", b"\x00", struct.pack(">i", self.abspos))  # x轴
        # time.sleep(0.5)
        self.send_cmd_frame(b"\xB1", b"\x01", struct.pack(">i", self.abspos))  # y轴
        self.wait_busy(local="x")
        self.wait_busy(local="y")           
    ###################################绝对位置控制end############################################

    ###################################相对位置控制############################################
    # 控制x轴移动相对距离
    def set_delivery_rel_x(self, x):
        self.read_abs_pos("x")
        self.x_abspos = x + self.x_input
        self.x_relpos = int((x / self.x_pitch_mm) * 360 / (self.x_step_angle/ self.x_subdivision)*(-1))
        self.send_cmd_frame(b"\xB2", b"\x00", struct.pack(">i", self.x_relpos))
        self.wait_busy(local="x")

    # 控制y轴移动相对距离
    def set_delivery_rel_y(self, y):
        self.read_abs_pos("y")
        self.y_relpos = int(((y / self.y_pitch_mm) * 360 / (self.y_step_angle/ self.y_subdivision))*(-1))
        self.y_abspos = (y + self.y_input)
        self.send_cmd_frame(b"\xB2", b"\x01", struct.pack(">i", self.y_relpos))
        self.wait_busy(local="y")

    # 控制z轴移动相对距离
    def set_delivery_rel_z(self, z):
        self.read_abs_pos("z")        
        self.z_relpos = int((z / self.z_pitch_mm) * 360 / (self.z_step_angle/ self.z_subdivision))
        self.z_abspos = z + self.z_input
        self.send_cmd_frame(b"\xB2", b"\x02", struct.pack(">i", self.z_relpos))
        self.wait_busy(local="z")        

    # 控制w轴移动相对距离
    def set_delivery_rel_w(self, w):
        self.read_abs_pos("w")          
        self.w_relpos = int((w / self.w_pitch_mm) * 360 / (self.w_step_angle/ self.w_subdivision))
        self.w_abspos = w + self.w_input        
        self.send_cmd_frame(b"\xB2", b"\x03", struct.pack(">i", self.w_relpos))
        self.wait_busy(local="w")

    # 控制ly轴移动相对距离
    def set_delivery_rel_ly(self, ly):
        self.read_abs_pos("ly")  
        self.ly_relpos = int((ly / self.ly_pitch_mm) * 360 / (self.ly_step_angle/ self.ly_subdivision)*(-1))
        self.ly_abspos = ly + self.ly_input    
        self.send_cmd_frame(b"\xB2", b"\x04", struct.pack(">i", self.ly_relpos))
        self.wait_busy(local="ly")

    # 控制lz轴移动相对距离
    def set_delivery_rel_lz(self, lz):
        self.read_abs_pos("lz")  
        self.lz_relpos = int((lz / self.lz_pitch_mm) * 360 / (self.lz_step_angle/ self.lz_subdivision)*(-1))
        self.lz_abspos = lz + self.lz_input    
        self.send_cmd_frame(b"\xB2", b"\x05", struct.pack(">i", self.lz_relpos))
        self.wait_busy(local="lz")

    # 控制xy轴同时运动相对距离
    def set_delivery_rel_xy(self, x, y):
        self.read_abs_pos("x")
        self.read_abs_pos("y")
        self.x_relpos = int((x / self.x_pitch_mm) * 360 / (self.x_step_angle/ self.x_subdivision))
        self.y_relpos = int((y / self.y_pitch_mm) * 360 / (self.y_step_angle/ self.y_subdivision))
        self.x_abspos = x + self.x_input
        self.y_abspos = y + self.y_input
        self.send_cmd_frame(b"\xB2", b"\x00", struct.pack(">i", self.x_relpos))  # x轴
        self.send_cmd_frame(b"\xB2", b"\x01", struct.pack(">i", self.y_relpos))  # y轴  
        self.wait_busy(local="x")
        self.wait_busy(local="y")  

    ###################################相对位置控制end############################################

    ###################################速度控制############################################
    # 设置电机最大速度
    def setup_velocity(self,local,velocity:float):
        self.is_vel_ack = False
        self.velocity = int(velocity*1000)
        if (local =="x"):
            self.send_cmd_frame(b"\xB5", b"\x00", struct.pack(">i", self.velocity))
        elif (local =="y"):
            self.send_cmd_frame(b"\xB5", b"\x01", struct.pack(">i", self.velocity))            
        elif (local =="z"):
            self.send_cmd_frame(b"\xB5", b"\x02", struct.pack(">i", self.velocity)) 
        elif (local =="w"):
            self.send_cmd_frame(b"\xB5", b"\x03", struct.pack(">i", self.velocity)) 
        elif (local =="ly"):
            self.send_cmd_frame(b"\xB5", b"\x04", struct.pack(">i", self.velocity)) 
        elif (local =="lz"):
            self.send_cmd_frame(b"\xB5", b"\x05", struct.pack(">i", self.velocity)) 
        # while not self.is_vel_ack :
        #     time.sleep(0.005)

    # 设置电机最大加速度
    def setup_acceleration(self,local,acceleration):
        self.is_acc_ack = False
        self.acceleration = acceleration
        if (local =="x"):
            self.send_cmd_frame(b"\xB6", b"\x00", struct.pack(">i", self.acceleration))
        elif (local =="y"):
            self.send_cmd_frame(b"\xB6", b"\x01", struct.pack(">i", self.acceleration))            
        elif (local =="z"):
            self.send_cmd_frame(b"\xB6", b"\x02", struct.pack(">i", self.acceleration)) 
        elif (local =="w"):
            self.send_cmd_frame(b"\xB6", b"\x03", struct.pack(">i", self.acceleration)) 
        elif (local =="ly"):
            self.send_cmd_frame(b"\xB6", b"\x04", struct.pack(">i", self.acceleration)) 
        elif (local =="lz"):
            self.send_cmd_frame(b"\xB6", b"\x05", struct.pack(">i", self.acceleration)) 
        while not self.is_acc_ack :
            time.sleep(0.005)
    ###################################速度控制end############################################

    ###################################电机复位控制############################################
    # 复位及判断
    def motor_reset(self,local):
        self.is_reset = False
        self.is_eeror_ack = False
        if (local =="x"):
            self.send_cmd_frame(b"\xBB", b"\x00", struct.pack(">i", self.zero_val))
        elif (local =="y"):
            self.send_cmd_frame(b"\xBB", b"\x01", struct.pack(">i", self.zero_val))
        elif (local =="z"):
            self.send_cmd_frame(b"\xBB", b"\x02", struct.pack(">i", self.zero_val))
        elif (local =="w"):
            self.send_cmd_frame(b"\xBB", b"\x03", struct.pack(">i", self.zero_val))
        elif (local =="ly"):
            self.send_cmd_frame(b"\xBB", b"\x04", struct.pack(">i", self.zero_val))
        elif (local =="lz"):
            self.send_cmd_frame(b"\xBB", b"\x05", struct.pack(">i", self.zero_val))                                         
        while not self.is_reset :
            time.sleep(0.005)
        if  (local =="x"):
            self.set_delivery_abs_x(0.5)
            self.set_delivery_abs_x(0)
        elif  (local =="y"):
            self.set_delivery_abs_y(0.5)
            self.set_delivery_abs_y(0)
        elif  (local =="z"):
            self.set_delivery_abs_z(0.5)
            self.set_delivery_abs_z(0)          
        elif  (local =="ly"):
            self.set_delivery_abs_ly(0.5)
            self.set_delivery_abs_ly(0)
        elif  (local =="lz"):
            self.set_delivery_abs_lz(0.5)
            self.set_delivery_abs_lz(0)

    # 电机失能及判断
    def scan_disenble_motor(self,local):
        self.is_stop_ack = False
        if local == "x":
            axis=b"\x00"
        elif local == "y":
            axis=b"\x01"
        elif local == "z":
            axis=b"\x02"
        elif local == "w":
            axis=b"\x03"
        elif local == "ly":
            axis=b"\x04"
        elif local == "lz":
            axis=b"\x05"                                    
        self.send_cmd_frame(b"\xB4",axis ,struct.pack(">i", self.zero_val))
        while not self.is_stop_ack :
            time.sleep(0.005)  
        self.is_busy = False
        self.read_cnt = 0

    ##################################其他外设############################################
    def led_rgbw_ctrl(self,r,g,b,w):
        self.is_rgbw_ack = False
        rgbw_val=(r&0xff)<<24|(g&0xff)<<16|(b&0xff)<<8|(w&0xff)
        # rgbw控制代码
        self.send_cmd_frame(b"\xBD", b"\x00", struct.pack(">i", rgbw_val)) 
        while not self.is_rgbw_ack :
            time.sleep(0.005) 


    # RGB灯控制
    # rgb_data[1]=1 ，1号玻片仓
    # rgb_data[2]=1 ，红色...=2，绿色...=3，黄色
    def light_rgb_ctrl(self,local,r,g,b):
        self.is_rgb_ack = False
        if local == "RGB1":
            rgb_num = b"\x00"
        elif local == "RGB2":
            rgb_num = b"\x01"                 
        # rgb控制代码
        rgb_val=(r&0xff)<<24|(g&0xff)<<16|(b&0xff)<<8|0x00
        self.send_cmd_frame(b"\xBE",rgb_num, struct.pack(">I", rgb_val)) 
        while not self.is_rgb_ack :
            time.sleep(0.005) 

    # 获取玻片数量
    def read_slide_nums(self,start_pos,end_pos):#45,159.2
        self.is_slide_ack = False
        self.slide_nums=0
        self.set_delivery_abs_lz(start_pos)
        time.sleep(1)
        end_abspos = int((end_pos / self.lz_pitch_mm) * 360 / (self.lz_step_angle/ self.lz_subdivision)*(-1))        
        self.send_cmd_frame(b"\xBC", b"\x00",struct.pack(">i", end_abspos))
        while not self.is_slide_ack :
            time.sleep(0.005) 
            # 解析前24位到slide_num列表
        for i in range(24):
            # 检查第i位是否为1 (从最低位开始)
            if self.slide_nums & (1 << i):
                self.slide_num_data[i] = 1
            else:
                self.slide_num_data[i] = 0      
        return self.slide_num_data
    

    ###################################调试用指令#############################################
    #设置虚拟限位开关
    def set_VirtualLimit(self,local,dir,limval):
        self.is_setup_ack = False
        self.limval = limval
        self.axis_dir = (local<<4)|dir
        if (local =="x"):
            self.send_cmd_frame(b"\xB3", self.axis_dir, struct.pack(">i", self.limval))
        elif (local =="y"):
            self.send_cmd_frame(b"\xB3", self.axis_dir, struct.pack(">i", self.limval))            
        elif (local =="z"):
            self.send_cmd_frame(b"\xB3", self.axis_dir, struct.pack(">i", self.limval)) 
        elif (local =="w"):
            self.send_cmd_frame(b"\xB3", self.axis_dir, struct.pack(">i", self.limval)) 
        elif (local =="ly"):
            self.send_cmd_frame(b"\xB3", self.axis_dir, struct.pack(">i", self.limval)) 
        elif (local =="lz"):
            self.send_cmd_frame(b"\xB3", self.axis_dir, struct.pack(">i", self.limval))
        while not self.is_setup_ack :
            time.sleep(0.005)                     

    #设置各个轴的零点
    def set_motor_zero(self,local):
        self.is_zero_ack = False        
        if (local =="x"):
            self.send_cmd_frame(b"\xB0", b"\x00", struct.pack(">i", self.zero_val))
        elif (local =="y"):
            self.send_cmd_frame(b"\xB0", b"\x01", struct.pack(">i", self.zero_val))            
        elif (local =="z"):
            self.send_cmd_frame(b"\xB0", b"\x02", struct.pack(">i", self.zero_val)) 
        elif (local =="w"):
            self.send_cmd_frame(b"\xB0", b"\x03", struct.pack(">i", self.zero_val)) 
        elif (local =="ly"):
            self.send_cmd_frame(b"\xB0", b"\x04", struct.pack(">i", self.zero_val)) 
        elif (local =="lz"):
            self.send_cmd_frame(b"\xB0", b"\x05", struct.pack(">i", self.zero_val))  
        while not self.is_zero_ack :
            time.sleep(0.005)               

    # 读取位置
    def read_abs_pos(self,local):
        self.is_read_ack = False 
        self.is_limit_rht_tri = False
        self.is_limit_let_tri = False       
        if (local =="x"):
            self.send_cmd_frame(b"\xB8", b"\x00", struct.pack(">i", self.zero_val))
        elif (local =="y"):
            self.send_cmd_frame(b"\xB8", b"\x01", struct.pack(">i", self.zero_val))            
        elif (local =="z"):
            self.send_cmd_frame(b"\xB8", b"\x02", struct.pack(">i", self.zero_val)) 
        elif (local =="w"):
            self.send_cmd_frame(b"\xB8", b"\x03", struct.pack(">i", self.zero_val)) 
        elif (local =="ly"):
            self.send_cmd_frame(b"\xB8", b"\x04", struct.pack(">i", self.zero_val)) 
        elif (local =="lz"):
            self.send_cmd_frame(b"\xB8", b"\x05", struct.pack(">i", self.zero_val))  
        while not self.is_read_ack :
            time.sleep(0.005)  

    def set_fans_state(self,fans,state):
        self.is_fans_ack = False
        fans_val=((fans<<8)|state)&0xff
        self.send_cmd_frame(b"\xBF", b"\x00", struct.pack(">i", fans_val))  
        while not self.is_fans_ack :
            time.sleep(0.005) 

    def read_temp_val(self):
        self.is_temp_ack = False
        self.send_cmd_frame(b"\xC2", b"\x00", struct.pack(">i", self.zero_val))  
        while not self.is_temp_ack :
            time.sleep(0.005)        

    def read_focus_val(self):
        self.is_focus_ack = False
        self.send_cmd_frame(b"\xC0", b"\x00", struct.pack(">i", self.zero_val))  
        while not self.is_focus_ack :
            time.sleep(0.005)
        return self.focus_val

    def light_ocr_ctrl(self,val):
        if val > 3.3:
            val = 3.3
        if val < 0:
            val = 0    
        self.is_light_ocr_ack = False   
        self.light_ocr_val = int(val*10)
        self.send_cmd_frame(b"\xC3", b"\x00", struct.pack(">i", self.light_ocr_val))  
        while not self.is_light_ocr_ack :
            time.sleep(0.005)   

    def enable_motor(self):
        self.is_enable_ack = False   
        self.send_cmd_frame(b"\xD0", b"\x00", struct.pack(">i", self.zero_val))  
        while not self.is_enable_ack :
            time.sleep(0.005)                   

    def beep_ctrl(self,sw):
        self.send_cmd_frame(b"\xC4", b"\x00", struct.pack(">i", sw)) 
    ##############################接收#############################        

    # 读取并处理下位机串口通信发送过来的数据
    def read_msg(self):
        self.flag_run = True
        while self.flag_run:
            if self.serial.read() == b"\xAA":
                rx_data = b"\xAA" + self.serial.read(7)
                # 校验通过
                if rx_data[0].to_bytes(1, byteorder='big')== b"\xAA" and rx_data[7]== 255:
                    cmd_id = rx_data[1].to_bytes(1, byteorder='big')
                    axis = rx_data[2].to_bytes(1, byteorder='big')
                    if cmd_id == b"\xB1":
                        self.is_read_ack = True
                        if axis == b"\x00":
                            read_steps= struct.unpack(">i", rx_data[3:7])[0]
                            self.x_input = ((-1)*(read_steps/(360/(self.x_step_angle/self.x_subdivision)))*self.x_pitch_mm)
                        elif axis == b"\x01":   
                            read_steps= struct.unpack(">i", rx_data[3:7])[0]
                            self.y_input = ((-1)*(read_steps/(360/(self.y_step_angle/self.y_subdivision)))*self.y_pitch_mm)
                        elif axis == b"\x02":   
                            read_steps= struct.unpack(">i", rx_data[3:7])[0]
                            self.z_input = (read_steps/(360/(self.z_step_angle/self.z_subdivision)))*self.z_pitch_mm
                        elif axis == b"\x03":   
                            read_steps= struct.unpack(">i", rx_data[3:7])[0]
                            self.w_input = (read_steps/(360/(self.w_step_angle/self.w_subdivision)))*self.w_pitch_mm
                        elif axis == b"\x04":   
                            read_steps= struct.unpack(">i", rx_data[3:7])[0]
                            self.ly_input = ((-1)*(read_steps/(360/(self.ly_step_angle/self.ly_subdivision)))*self.ly_pitch_mm)
                        elif axis == b"\x05":   
                            read_steps= struct.unpack(">i", rx_data[3:7])[0]
                            self.lz_input = ((-1)*(read_steps/(360/(self.lz_step_angle/self.lz_subdivision)))*self.lz_pitch_mm)
                    elif cmd_id == b"\xD1":  # 系统故障
                        self.is_warning = True
                    elif cmd_id == b"\xB0":  # 零位设置成功
                        self.is_zero_ack = True                            
                    elif cmd_id == b"\xB3":  # 虚拟限位设置成功
                        self.is_setup_ack = True   
                    elif cmd_id == b"\xB4":  # 强行停止
                        self.is_stop_ack = True  
                        self.is_busy = False                                                 
                    elif cmd_id == b"\xB5":  # 速度设置成功
                        self.is_vel_ack = True
                    elif cmd_id == b"\xB6":  # 加速度设置成功
                        self.is_acc_ack = True                        
                    elif cmd_id == b"\xBB":  # 复位完成
                        self.is_reset = True      
                    elif cmd_id == b"\xBC":  # 获取玻片数量
                        self.is_slide_ack = True
                        self.slide_nums = struct.unpack(">i", rx_data[3:7])[0] 
                    elif cmd_id == b"\xBD":  # RGBW值设置完成
                        self.is_rgbw_ack = True                                                                 
                    elif cmd_id == b"\xBE":  # RGB设置完成   
                        self.is_rgb_ack = True  
                    elif cmd_id == b"\xBF":  # pwm设置完成
                        self.is_fans_ack = True   
                    elif cmd_id == b"\xC0":  # 设置完成
                        self.is_focus_ack = True 
                        self.focus_val = (struct.unpack(">i", rx_data[3:7])[0])/1000.0                         
                    elif cmd_id == b"\xC1":  # 限位开关被触发
                        if axis == b"\x00": 
                            self.is_limit_rht_tri = True   
                        elif axis == b"\x01": 
                            self.is_limit_let_tri = True                           
                    elif cmd_id == b"\xC2":  # pwm设置完成
                        self.is_temp_ack = True 
                        self.temp_val = (struct.unpack(">i", rx_data[3:7])[0])/10
                    elif cmd_id == b"\xC3":  # OCR相机设置完成
                        self.is_light_ocr_ack = True
                    elif cmd_id == b"\xD0":  # 电机使能完成
                        self.is_enable_ack = True                        
                    elif cmd_id == b"\xEE":  # 设备故障
                        self.is_eeror_ack = True                                      


    ######################串口进程############################

    # 打印串口接收数据
    def receive_data(self):
        while True:
            print("pumpdata:{}".format())

    # 停止串口读取
    def stop_reading(self):
        self.flag_run = False
        self.serial_thread.join()  # 等待线程结束

    # 关闭串口进程
    def ser_close(self):
        self.stop_reading()
        self.serial.close()

#  手柄专用SDK
   # 控制x轴移动相对距离
    def set_handle_rel(self, local,rel):
        if local == "x":               
            self.x_relpos = int((rel / self.x_pitch_mm) * 360 / (self.x_step_angle/ self.x_subdivision)*(-1))
            self.send_cmd_frame(b"\xB2", b"\x00", struct.pack(">i", self.x_relpos))
        elif local =="y":
            self.y_relpos = int(((rel / self.y_pitch_mm) * 360 / (self.y_step_angle/ self.y_subdivision))*(-1))
            self.send_cmd_frame(b"\xB2", b"\x01", struct.pack(">i", self.y_relpos)) 
        elif local == "z":
            self.z_relpos = int((rel / self.z_pitch_mm) * 360 / (self.z_step_angle/ self.z_subdivision))
            self.send_cmd_frame(b"\xB2", b"\x02", struct.pack(">i", self.z_relpos))                                
