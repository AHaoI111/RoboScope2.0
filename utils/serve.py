import asyncio
import base64
import json
import threading

import cv2
import numpy as np
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from uvicorn import Server, Config


class Move(BaseModel):
    value: float

class ExposureTime(BaseModel):
    value: float


class objective_number(BaseModel):
    value: int


class led_color(BaseModel):
    R: int
    G: int
    B: int
    W: int


class plan_name(BaseModel):
    value: str


class roboscope_server(threading.Thread):
    def __init__(self, ipadd, port, DeviceConnect, logger, my_devices_info):
        super().__init__()
        self.app = FastAPI()
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 允许所有来源
            allow_credentials=True,
            allow_methods=["*"],  # 允许所有HTTP方法
            allow_headers=["*"]  # 允许所有请求头
        )
        self.config = Config(app=self.app, host=ipadd, port=port)
        self.server = Server(self.config)
        self._stop_event = threading.Event()

        # 注册 FastAPI 事件处理程序
        self.app.add_event_handler("startup", self.startup_event)
        self.app.add_event_handler("shutdown", self.shutdown_event)

        @self.app.get("/device/info", tags=["设备信息"])
        async def get_device_info():
            logger.info("设备信息查询")
            return {
                "status": "success",
                "info": my_devices_info
            }

        @self.app.get("/device/connected", tags=["设备状态"])
        async def check_device_connected():
            return {"status": "success", "message": "设备连接状态查询成功", "connected": DeviceConnect.connected_state}

        @self.app.post("/device/connect", tags=["设备连接测试"])
        async def device_connect_test():
            flag, msg = DeviceConnect.connect()
            if flag:
                return {"status": "success", "message": "设备连接成功"}
            else:
                return {"status": "error", "message": "设备连接失败" + msg}

        @self.app.post("/device/disconnect", tags=["设备连接测试"])
        async def device_connect_test():
            flag, msg = DeviceConnect.disconnect()
            if flag:
                return {"status": "success", "message": "设备断开成功"}
            else:
                return {"status": "error", "message": "设备断开失败" + msg}

        @self.app.post("/stage/x/debug", tags=["位移台控制"])
        async def debug_stage_x(X: Move):
            if 60 < X.value < 0:
                return {"status": "error", "message": "X轴位移超出范围"}
            if DeviceConnect.microscope is None:
                return {"status": "error", "message": "设备未处于连接状态"}
            DeviceConnect.microscope.set_delivery_abs_x(X.value)
            return {"status": "success", "message": "X轴位移调试成功"}

        @self.app.post("/stage/y/debug", tags=["位移台控制"])
        async def debug_stage_y(Y: Move):
            if 61 < Y.value < 0:
                return {"status": "error", "message": "Y轴位移超出范围"}
            if DeviceConnect.microscope is None:
                return {"status": "error", "message": "设备未处于连接状态"}
            DeviceConnect.microscope.set_delivery_abs_y(Y.value)
            return {"status": "success", "message": "Y轴位移调试成功"}

        @self.app.post("/stage/z/debug", tags=["位移台控制"])
        async def debug_stage_z(Z: Move):
            if 0 > Z.value > 7:
                return {"status": "error", "message": "Z轴位移超出范围"}
            if DeviceConnect.microscope is None:
                return {"status": "error", "message": "设备未处于连接状态"}
            DeviceConnect.microscope.set_delivery_abs_z(Z.value)
            return {"status": "success", "message": "Z轴位移调试成功"}

        @self.app.post("/stage/LED/debug", tags=["光源控制"])
        async def debug_led(color: led_color):
            if DeviceConnect.microscope is None:
                return {"status": "error", "message": "设备未处于连接状态"}
            DeviceConnect.microscope.led_rgbw_ctrl(color.R, color.G, color.B, color.W)
            return {"status": "success", "message": "RGBW调试成功"}

        @self.app.post("/objective/turret/debug", tags=["物镜控制"])
        async def debug_objective_turret(number: objective_number):
            if number.value < 0 or number.value > 5:
                return {"status": "error", "message": "物镜编号超出范围"}
            if DeviceConnect.microscope is None:
                return {"status": "error", "message": "设备未处于连接状态"}
            if number.value == 1:
                DeviceConnect.microscope.select_objective_num1()
            elif number.value == 2:
                DeviceConnect.microscope.select_objective_num2()
            elif number.value == 3:
                DeviceConnect.microscope.select_objective_num3()
            elif number.value == 4:
                DeviceConnect.microscope.select_objective_num4()
            return {"status": "success", "message": "物镜转盘调试成功"}

        @self.app.post("/objective/Laser/debug", tags=["激光测距"])
        async def debug_Laser_distance():
            if DeviceConnect.connected_state:
                focus_val = DeviceConnect.microscope.read_focus_val()
                return {"status": "success", "message": "激光测距成功", "focus_val": focus_val}
            return {"status": "error", "message": "设备未处于连接状态"}

        @self.app.post("/loader/z/down/debug", tags=["装载仓控制"])
        async def debug_loader_down(Z: Move):
            if Z.value < 0:
                return {"status": "error", "message": "下降距离不能小于0"}
            if DeviceConnect.microscope is None:
                return {"status": "error", "message": "设备未处于连接状态"}
            DeviceConnect.microscope.set_delivery_abs_lz(Z.value)
            return {"status": "success", "message": "装载仓下降调试成功"}

        @self.app.post("/slide/push/debug", tags=["玻片操作"])
        async def debug_push_slide(Y: Move):
            if Y.value < 0:
                return {"status": "error", "message": "上升距离不能小于0"}
            if DeviceConnect.microscope is None:
                return {"status": "error", "message": "设备未处于连接状态"}
            DeviceConnect.microscope.set_delivery_abs_ly(Y.value)
            return {"status": "success", "message": "推片动作调试成功"}

        # 添加新的流式传输接口
        @self.app.get("/camera/image/stream", tags=["获取图片"])
        async def stream_images():
            """
            实时传输图像流
            """

            async def image_generator():
                while True:
                    try:
                        if DeviceConnect.connected_state:
                            # 发送触发信号
                            DeviceConnect.scan_camera.send_trigger()
                            # 读取帧
                            img = DeviceConnect.scan_camera.read_frame()

                            # 将图像转换为base64编码
                            if isinstance(img, np.ndarray):
                                # 编码为JPEG格式
                                _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 80])
                                img_base64 = base64.b64encode(buffer).decode('utf-8')

                                # 通过 Server-Sent Events 发送数据
                                response_data = {
                                    "status": "success",
                                    "message": "Image captured successfully",
                                    "image": img_base64
                                }
                                yield f"data: {json.dumps(response_data)}\n\n"
                            else:
                                # 错误情况
                                response_data = {
                                    "status": "error",
                                    "message": "图像数据格式错误"
                                }
                                yield f"data: {json.dumps(response_data)}\n\n"
                        else:
                            response_data = {
                                "status": "error",
                                "message": "设备未处于连接状态"
                            }
                            yield f"data: {json.dumps(response_data)}\n\n"

                        # 控制帧率 (每秒10帧)
                        await asyncio.sleep(0.1)

                    except Exception as e:
                        response_data = {
                            "status": "error",
                            "message": f"获取图片失败: {str(e)}"
                        }
                        yield f"data: {json.dumps(response_data)}\n\n"
                        await asyncio.sleep(1)  # 出错后等待1秒再重试

            return StreamingResponse(
                image_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                }
            )

        @self.app.post("/camera/ExposureTime/debug", tags=["曝光设置"])
        async def debug_ExposureTime(et: ExposureTime):
            if DeviceConnect.connected_state:
                DeviceConnect.scan_camera.set_exposure_time(et.value)
                return {"status": "success", "message": "相机设置曝光成功"}
            return {"status": "error", "message": "设备未处于连接状态"}

        @self.app.get("/camera/WB", tags=["白平衡系数获取设置"])
        async def debug_WB():
            if DeviceConnect.connected_state:
                DeviceConnect.scan_camera.send_trigger()
                img = DeviceConnect.scan_camera.read_frame()
                awb_r, awb_g, awb_b = DeviceConnect.scan_camera.get_awb_ratios()
                return {"status": "success", "message": "白平衡系数获取成功", "awb_r": awb_r, "awb_g": awb_g,
                        "awb_b": awb_b}
            return {"status": "error", "message": "设备未处于连接状态"}

        @self.app.post("/OCR/LED/debug", tags=["ocr光源"])
        async def debug_OCRLED(intensity: float):
            if DeviceConnect.microscope is None:
                return {"status": "error", "message": "设备未处于连接状态"}
            DeviceConnect.microscope.light_ocr_ctrl(intensity)
            return {"status": "success", "message": "ocr光源调试成功"}

        @self.app.post("/slide/count/debug", tags=["玻片操作"])
        async def debug_count_slides():
            if DeviceConnect.connected_state:
                slide_num_data = DeviceConnect.microscope.read_slide_nums(157.2)
                return {"status": "success", "message": "玻片计数测试成功", "slide_num_data": str(slide_num_data)}
            return {"status": "error", "message": "设备未处于连接状态"}

        @self.app.post("/slide/go/debug", tags=["测试第一张上片操作"])
        async def debug_slide_go():
            # 复位
            if DeviceConnect.connected_state:
                DeviceConnect.microscope.motor_reset("z")
                DeviceConnect.microscope.motor_reset("w")
                DeviceConnect.microscope.motor_reset("y")
                DeviceConnect.microscope.motor_reset("ly")
                DeviceConnect.microscope.set_delivery_abs_ly(4.6)
                DeviceConnect.microscope.motor_reset("x")
                DeviceConnect.microscope.motor_reset("lz")
                #
                DeviceConnect.microscope.set_delivery_abs_lz(float(my_devices_info['loader']['z']))
                DeviceConnect.microscope.set_delivery_abs_x(float(my_devices_info['microscope']['slidextransfer']))
                DeviceConnect.microscope.set_delivery_abs_y(float(my_devices_info['microscope']['slideytransfer']))
                DeviceConnect.microscope.set_delivery_abs_z(float(my_devices_info['microscope']['slideztransfer']))
                #
                DeviceConnect.microscope.set_delivery_abs_ly(float(my_devices_info['loader']['slidepushly']))
                DeviceConnect.microscope.set_delivery_abs_ly(float(my_devices_info['loader']['slidepushly']) - 1)
                #
                DeviceConnect.microscope.set_delivery_abs_x(
                    float(my_devices_info['microscope']['scan_reference_point_x']))
                DeviceConnect.microscope.set_delivery_abs_y(
                    float(my_devices_info['microscope']['scan_reference_point_y']))

                return {"status": "success", "message": "载物台对齐测试成功"}
            return {"status": "error", "message": "设备未处于连接状态"}

        @self.app.post("/slide/re/debug", tags=["测试第一张取片操作"])
        async def debug_slide_re():
            #
            if DeviceConnect.connected_state:
                DeviceConnect.microscope.set_delivery_abs_ly(float(my_devices_info['loader']['slidepushly']))
                DeviceConnect.microscope.set_delivery_abs_ly(float(my_devices_info['loader']['slidepushly']) - 1)
                #
                DeviceConnect.microscope.set_delivery_abs_z(float(my_devices_info['microscope']['slideztransfer']))
                DeviceConnect.microscope.set_delivery_abs_y(float(my_devices_info['microscope']['slideytransfer']))
                DeviceConnect.microscope.set_delivery_abs_x(float(my_devices_info['microscope']['slidextransfer']))

                # 扫描完成送片
                DeviceConnect.microscope.set_delivery_abs_ly(float(my_devices_info['loader']['slidepullly']))
                DeviceConnect.microscope.set_delivery_abs_ly(float(my_devices_info['loader']['slidepullly_offset']))

                DeviceConnect.microscope.motor_reset("z")
                DeviceConnect.microscope.motor_reset("w")
                DeviceConnect.microscope.motor_reset("y")
                DeviceConnect.microscope.motor_reset("ly")
                DeviceConnect.microscope.set_delivery_abs_ly(float(my_devices_info['loader']['slidepullly_offset']))
                DeviceConnect.microscope.motor_reset("x")
                DeviceConnect.microscope.motor_reset("lz")

                return {"status": "success", "message": "载物台对齐测试成功"}
            return {"status": "error", "message": "设备未处于连接状态"}

    def run(self):
        # 启动 FastAPI 应用
        self.server.run()

    def stop(self):
        # 停止 FastAPI 应用
        self.server.should_exit = True  # 设置退出标志
        self._stop_event.set()

    def startup_event(self):
        print("FastAPI application starting up")

    def shutdown_event(self):
        print("FastAPI application shutting down")
