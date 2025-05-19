import os
import threading
import time
import base64
import cv2

import uvicorn
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
import serial_microscope
import serial_loader
import utils.read_config as read_config
import utils.action_loader as action_loader
import utils.action_microscope as action_microscope
from utils.ImageSaver import Image_Saver
from utils.MessageWoker import Message_Woker
import utils.Scan as Scan
from utils.task_info import apply_task_info, create_task_plan, save_json, read_json, create_task_plan_default
import utils.taskwork as taskwork

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"]  # 允许所有请求头
)
# 获取文件内容
config = read_config.ConfigReader()
my_devices_info = config.get_config_info()
Image_Saver = Image_Saver(my_devices_info['ImageSaver'])
Message_Woker = Message_Woker(my_devices_info['ImageSaver'])
microscope_controller = None
loader_controller = None
scan_action_loader = None
scan_action_microscope = None
Scanning = None
ConnectionStatus = False
my_task = {}


class Move(BaseModel):
    value: float


class device_sn(BaseModel):
    sn: str


class scan_info(BaseModel):
    plan: str
    slide_list: list


class fcous_camera(BaseModel):
    camera: str


class plan(BaseModel):
    config_info: dict


@app.get("/roboscope_info", description="注册设备信息")
async def get_config_info():
    global my_devices_info
    try:
        return my_devices_info
    except Exception as e:
        return {
            "result": "error",
            "msg": str(e)
        }


@app.get("/getConnectionStatus", description="获取当前设备的连接状态")
async def get_Connection_Status():
    return ConnectionStatus


@app.get("/getplan", description="获取当前设备的扫描方案")
async def get_plans():
    # 任务文件目录
    directory_path = './plan'
    # 扫描该目录下的所有 JSON 文件
    json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]
    json_file_name_list = []
    # 输出不带扩展名的文件名
    for json_file in json_files:
        # 获取文件名并去掉扩展名
        file_name_without_extension = os.path.splitext(json_file)[0]
        json_file_name_list.append({'value': file_name_without_extension})
    return json_file_name_list


@app.post("/download_plan", description="下载方案，参数为方案的json数据")
async def download_plan(info: plan):
    # 任务文件目录
    directory_path = './plan'
    taskinfo = apply_task_info(my_devices_info)
    default = create_task_plan_default(taskinfo)
    save_json(default, directory_path)
    task_plan = create_task_plan(taskinfo, info.config_info)
    save_json(task_plan, directory_path)


@app.post("/connect2device", description="初始化显微镜设备连接并验证通信")
async def connect_device():
    global microscope_controller
    global loader_controller
    global scan_action_loader
    global scan_action_microscope
    global Scanning
    global ConnectionStatus
    try:
        sn = my_devices_info['Device']['sn']
        if sn == my_devices_info['Device']['sn']:
            config_info = my_devices_info
            if config_info['Device']['loaderflage']:
                microscope_controller = serial_microscope.SerialMicroscope(config_info)
                loader_controller = serial_loader.SerialLoader(config_info['Loader']['串口']
                                                               , config_info['Loader']['滴油器串口']
                                                               , config_info['Loader']['oilflag'])
                microscope_controller.open()
                loader_controller.open()
                scan_action_loader = action_loader.ActionLoader(loader_controller.Loader, my_devices_info)
                scan_action_microscope = action_microscope.ActionMicroscope(microscope_controller)
                Scanning = Scan.Scanning(scan_action_microscope, Image_Saver, Message_Woker)
            else:
                microscope_controller = serial_microscope.SerialMicroscope(config_info)
                microscope_controller.open()
                scan_action_microscope = action_microscope.ActionMicroscope(microscope_controller)
                Scanning = Scan.Scanning(scan_action_microscope, Image_Saver, Message_Woker)
            ConnectionStatus = True
            return {
                "result": "success",
                "msg": "调用成功"
            }
        else:
            ConnectionStatus = False
            return {
                "result": "error",
                "msg": " 设备未注册"
            }
    except Exception as e:
        ConnectionStatus = False
        return {
            "result": "error",
            "msg": str(e)
        }


@app.post("/disconnect2device", description="显微镜设备断开连接并验证通信")
async def disconnect_device():
    global microscope_controller
    global loader_controller
    global scan_action_loader
    global scan_action_microscope
    global Scanning
    global ConnectionStatus
    try:
        sn = my_devices_info['Device']['sn']
        if sn == my_devices_info['Device']['sn']:
            config_info = my_devices_info
            if config_info['Device']['loaderflage']:
                microscope_controller.close()
                loader_controller.close()
                scan_action_microscope.release_camera()
            else:
                microscope_controller.close()
            microscope_controller = None
            loader_controller = None
            scan_action_loader = None
            scan_action_microscope = None
            Scanning = None
            ConnectionStatus = False
            return {
                "result": "success",
                "msg": "调用成功"
            }
        else:
            ConnectionStatus = False
            return {
                "result": "error",
                "msg": " 设备未连接"
            }

    except Exception as e:
        ConnectionStatus = False
        return {
            "result": "error",
            "msg": str(e)
        }


@app.post("/microscopemovex2", description="显微镜设备x移动,值大于0小于60")
async def microscope_move_x_2(info: Move):
    try:
        if scan_action_microscope is not None:
            # 假设移动的方法是 move_x，具体实现依赖于你的显微镜库
            if 0 <= info.value <= 60:
                scan_action_microscope.microscope_move_x_to(info.value)
            return {
                "result": "success",
                "msg": "调用成功"
            }
        else:
            return {
                "result": "error",
                "msg": "显微镜未连接"
            }
    except Exception as e:
        return {
            "result": "error",
            "msg": str(e)
        }


@app.post("/microscopemovey2", description="显微镜设备y移动,值大于0小于60")
async def microscope_move_y_2(info: Move):
    try:
        if scan_action_microscope is not None:
            # 假设移动的方法是 move_x，具体实现依赖于你的显微镜库
            if 0 <= info.value <= 60:
                scan_action_microscope.microscope_move_y_to(info.value)
            return {
                "result": "success",
                "msg": "调用成功"
            }
        else:
            return {
                "result": "error",
                "msg": "显微镜未连接"
            }
    except Exception as e:
        return {
            "result": "error",
            "msg": str(e)
        }


@app.post("/microscopemovez2", description="显微镜设备z移动,值大于0小于6")
async def microscope_move_z_2(info: Move):
    try:
        if scan_action_microscope is not None:
            # 假设移动的方法是 move_x，具体实现依赖于你的显微镜库
            if 0 <= info.value <= 6:
                scan_action_microscope.microscope_move_z_to(info.value)
            return {
                "result": "success",
                "msg": "调用成功"
            }
        else:
            return {
                "result": "error",
                "msg": "显微镜未连接"
            }
    except Exception as e:
        return {
            "result": "error",
            "msg": str(e)
        }


@app.post("/loadermovex2", description="装载器设备x移动,值大于0小于300")
async def loader_move_x_2(info: Move):
    try:
        if scan_action_loader is not None:
            # 假设移动的方法是 move_x，具体实现依赖于你的显微镜库
            if 0 <= info.value <= 300:
                scan_action_loader.move_x_to(info.value)
            return {
                "result": "success",
                "msg": "调用成功"
            }

        else:
            return {
                "result": "error",
                "msg": "装载器未连接"
            }
    except Exception as e:
        return {
            "result": "error",
            "msg": str(e)
        }


@app.post("/loadermovey2", description="装载器设备y移动,值大于-91小于-1")
async def loader_move_y_2(info: Move):
    try:
        if scan_action_loader is not None:
            # 假设移动的方法是 move_x，具体实现依赖于你的显微镜库
            if -91 <= info.value <= -1:
                scan_action_loader.move_y_to(info.value)
            return {
                "result": "success",
                "msg": "调用成功"
            }

        else:
            return {
                "result": "error",
                "msg": "装载器未连接"
            }
    except Exception as e:
        return {
            "result": "error",
            "msg": str(e)
        }


@app.post("/loadermovez2", description="装载器设备z移动,值大于0小于150")
async def loader_move_z_2(info: Move):
    try:
        if scan_action_loader is not None:
            # 假设移动的方法是 move_x，具体实现依赖于你的显微镜库
            if 0 <= info.value <= 150:
                scan_action_loader.move_z_to(info.value)
            return {
                "result": "success",
                "msg": "调用成功"
            }

        else:
            return {
                "result": "error",
                "msg": "装载器未连接"
            }
    except Exception as e:
        return {
            "result": "error",
            "msg": str(e)
        }


@app.post("/testgetslide", description="装载器装载第一个玻片仓的第一张玻片到显微镜载物台")
async def test_get_slide_():
    try:
        sn = my_devices_info['Device']['sn']
        if sn == my_devices_info['Device'][
            'sn'] and scan_action_microscope is not None and scan_action_loader is not None:
            scan_action_microscope.microscope_homezxy()
            scan_action_loader.loader_reset()
            slide__points = scan_action_loader.get_box_points(1)

            # 移动取片
            # 移动到盒子取玻片处
            scan_action_loader.move_x_to(slide__points[0][0])
            scan_action_loader.move_z_to(slide__points[0][1])
            # 取片(动作为y伸出、z上台、y回收)
            scan_action_loader.get_slide_from_box(slide__points[0][1])
            # 显微镜移动至接片处等待
            scan_action_microscope.move_2_loader_get_wait(float(my_devices_info['Microscope']['sys']['xend']),
                                                          float(my_devices_info['Microscope']['sys']['yend']))
            # 装载器移动
            scan_action_loader.move_2_microscope_give_location()
            # 确认完成动作
            scan_action_microscope.wait_busy()
            # 放片到载物台
            scan_action_loader.give_slide_to_microscope()
            if scan_action_loader.loader.is_warning:
                return
            # 避位
            scan_action_loader.loader_avoid()
            # 失能
            scan_action_loader.disenble_motor()
            return {
                "result": "success",
                "msg": "调用成功"
            }

        else:
            return {
                "result": "error",
                "msg": "装载器未连接"
            }
    except Exception as e:
        return {
            "result": "error",
            "msg": str(e)
        }


@app.post("/testputslide", description="装载器装载第一个玻片仓的第一张玻片到显微镜载物台")
async def test_put_slide_():
    try:
        sn = my_devices_info['Device']['sn']
        if sn == my_devices_info['Device'][
            'sn'] and scan_action_microscope is not None and scan_action_loader is not None:
            scan_action_microscope.microscope_home_z()
            # 显微镜移动至交接处
            scan_action_microscope.move_2_loader_give(float(my_devices_info['Microscope']['sys']['xend']),
                                                      float(my_devices_info['Microscope']['sys']['yend']))
            # 移动至显微镜处下方
            scan_action_loader.move_2_microscope_get_location()
            # 取片
            scan_action_loader.get_slide_from_microscope()
            if scan_action_loader.loader.is_warning:
                return
            # 显微镜复位
            scan_action_microscope.microscope_homezxy_wait()
            # 获取玻片位置
            slide__points = scan_action_loader.get_box_points(1)
            # 返回玻片仓位置放片
            scan_action_loader.move_x_to(slide__points[0][0])
            scan_action_loader.move_z_to(slide__points[0][1] - scan_action_loader.boxzgap)
            # 放片
            scan_action_loader.give_slide_to_box(slide__points[0][1] - scan_action_loader.boxzgap)
            if scan_action_loader.loader.is_warning:
                return
            scan_action_microscope.wait_busy()

            return {
                "result": "success",
                "msg": "调用成功"
            }

        else:
            return {
                "result": "error",
                "msg": "装载器未连接"
            }
    except Exception as e:
        return {
            "result": "error",
            "msg": str(e)
        }


@app.post("/autofcous", description="确保载物台上有一张玻片后，单独测试自动对焦")
async def test_autofocus(info: fcous_camera):
    try:
        if Scanning is not None and scan_action_microscope is not None:
            camera = info.camera
            if camera == "high":
                scan_action_microscope.set_high_light()
                scan_action_microscope.microscope_move_y_to(
                    float(my_devices_info['Microscope']['high']['高倍扫描中心xy']['y']))
                scan_action_microscope.microscope_move_x_to(
                    float(my_devices_info['Microscope']['high']['高倍扫描中心xy']['x']))
                Scanning.number = int(my_devices_info['Microscope']['high']['高倍对焦步数'])
                Scanning.step = float(my_devices_info['Microscope']['high']['高倍对焦分辨率'])
                zpos, img = Scanning.AutofocusWorker(float(my_devices_info['Microscope']['high']['对焦经验值高倍']),
                                                     scan_action_microscope.get_image_camera_high, True)
            elif camera == "low":
                scan_action_microscope.set_low_light()
                scan_action_microscope.microscope_move_y_to(
                    float(my_devices_info['Microscope']['low']['低倍扫描中心xy']['y']))
                scan_action_microscope.microscope_move_x_to(
                    float(my_devices_info['Microscope']['low']['低倍扫描中心xy']['x']))
                Scanning.number = int(my_devices_info['Microscope']['low']['低倍对焦步数'])
                Scanning.step = float(my_devices_info['Microscope']['low']['低倍对焦分辨率'])
                zpos, img = Scanning.AutofocusWorker(float(my_devices_info['Microscope']['low']['对焦经验值低倍']),
                                                     scan_action_microscope.get_image_camera_low, True)
            elif camera == "single":
                scan_action_microscope.microscope_move_y_to(
                    float(my_devices_info['Microscope']['single']['单镜头扫描中心xy']['y']))
                scan_action_microscope.microscope_move_x_to(
                    float(my_devices_info['Microscope']['single']['单镜头扫描中心xy']['x']))
                Scanning.number = int(my_devices_info['Microscope']['single']['单镜头对焦步数'])
                Scanning.step = float(my_devices_info['Microscope']['single']['单镜头对焦分辨率'])
                zpos, img = Scanning.AutofocusWorker(float(my_devices_info['Microscope']['single']['对焦经验值单镜头']),
                                                     scan_action_microscope.get_image_camera_one, True)
            _, buffer = cv2.imencode('.jpg', img)
            img_base64 = base64.b64encode(buffer).decode('utf-8')

            return {
                "result": "success",
                "msg": "调用成功",
                "data": img_base64
            }
        else:
            return {
                "result": "error",
                "msg": "装载器未连接",
                "data": None
            }
    except Exception as e:
        return {
            "result": "error",
            "msg": str(e),
            "data": None
        }


@app.post("/scan", description="扫描接口")
async def scan_(info: scan_info):
    try:
        Taskinfo = read_json('./plan/' + info.plan + '.json')
        if loader_controller is not None and Taskinfo is not None:
            task = taskwork.Task(scan_action_loader, scan_action_microscope, Scanning)
            thread_Task = threading.Thread(target=task.run, args=(Taskinfo, info.slide_list))
            thread_Task.start()
            return {
                "result": "success",
                "msg": "调用成功"
            }
        else:
            return {
                "result": "error",
                "msg": "扫描任务失败"
            }

    except Exception as e:
        return {
            "result": "error",
            "msg": str(e)
        }


if __name__ == "__main__":
    uvicorn.run("main:app", host="192.168.0.177", port=51121)
