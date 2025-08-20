import cv2
import requests


class requester(object):
    def __init__(self, logger, local_config):
        self.logger = logger
        self.local_config = local_config
        self.url_server = 'http://' + str(local_config.serve_host) + ':' + str(local_config.serve_port)

    def get_device_info(self):
        try:
            response = requests.get(self.url_server + "/api/v1_0/parameters")
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error('get device info error')
                return {}
        except Exception as e:
            self.logger.error('get device info error' + str(e))
            return {}

    def get_plan_list(self):
        try:
            response = requests.get(self.url_server + "/api/v1_0/plans_list")
            return response.json()['data']
        except Exception as e:
            self.logger.error('get plan list error' + str(e))
            return {}

    def get_plan_info(self, plan_id):
        try:
            response = requests.get(self.url_server + "/api/v1_0/plan/" + str(plan_id))
            return response.json()['data']
        except:
            self.logger.error('get plan list error')
            return {}

    def create_task_id(self, plan_id, storage_id, user_id):
        data = {
            "plan_id": plan_id,
            "storage_id": storage_id,
            "user_id": user_id
        }
        response = requests.post(self.url_server + "/api/v1_0/task", params=data)
        if response.status_code == 200:
            return str(response.json()['data']['task_id']), str(response.json()['data']['serial_number'])
        else:
            return None, None

    def finfish_task(self, task_id):
        data = {
            "task_id": task_id,
        }
        response = requests.put(self.url_server + "/api/v1_0/task/finish", params=data)
        return response.status_code, response.json()

    def create_slide_count(self, task_id, slide_count):
        data = {
            "task_id": task_id,
            "slide_count": int(slide_count)
        }
        response = requests.put(self.url_server + "/api/v1_0/slide_count", params=data)
        if response.status_code == 200:
            return str(response.json()['data'])
        else:
            return None

    def create_slide_id(self, task_id, sub_path, slide_position, is_last_slide):
        data = {
            "task_id": task_id,
            "sub_path": sub_path,
            "slide_position": int(slide_position),
            "last_one": is_last_slide
        }
        response = requests.post(self.url_server + "/api/v1_0/slide", params=data)
        if response.status_code == 200:
            if response.json()['code'] == 200:
                return str(response.json()['data']['slide_id'])
            else:
                return None
        else:
            return None

    def finish_silde(self, slide_id, slide_pic):
        data = {
            "slide_id": slide_id,
            "slide_pic": slide_pic
        }
        response = requests.put(self.url_server + "/api/v1_0/slide/finish", params=data)
        return response.status_code, response.json()

    def get_scan_info(self, flow_id):
        data = {
            "flow_id": flow_id,
        }
        response = requests.get(self.url_server + "/api/v1_0/flow/" + str(flow_id), params=data)
        if response.status_code == 200:
            return response.json()['data']
        else:
            return None

    def create_slide_label_flow(self, slide_id, flow_id, label_name, name_label_position
                                , sample_no_label_position, patient_no_label_position,
                                sample_category_label_position, preparation_method_label_position):
        data = {
            "slide_id": slide_id,
            "flow_id": flow_id,
            "label_pic": label_name,
            "name_label": name_label_position
            , "sample_no_label": sample_no_label_position,
            "patient_no_label": patient_no_label_position,
            "sample_category_label": sample_category_label_position,
            "preparation_method_label": preparation_method_label_position
        }
        response = requests.put(self.url_server + "/api/v1_0/slide_label_flow/", params=data)
        if response.status_code == 200:
            return response.json()['data']
        else:
            return None

    # def create_view(self, slide_id, file_name, location, view_filed_group, is_end):
    #
    #     data = {
    #         "slide_id": slide_id,
    #         "file_name": file_name,
    #         "location": location,
    #         "view_field_group": int(view_filed_group),
    #         "finished": is_end
    #     }
    #
    #     response = requests.post(self.url_server + "/api/v1_0/view_field", json=data)
    #     return response.status_code, response.json()

    def create_view(self, slide_id, file_name,file_names, location, view_filed_group, is_end):

        data = {
            "slide_id": slide_id,
            "file_name": file_name,
            "file_names": file_names,
            "location": location,
            "view_field_group": int(view_filed_group),
            "finished": is_end
        }

        response = requests.post(self.url_server + "/api/v1_0/view_field", json=data)
        return response.status_code, response.json()

    def send_ocr_label_image(self, img_label, model_id):
        # 将 OpenCV 图像转换为 JPEG 字节流
        _, img_encoded = cv2.imencode('.jpg', img_label)
        img_bytes = img_encoded.tobytes()  # 转换为字节流

        form_data = {
            "model_id": model_id,

        }
        # 准备文件数据（关键：使用元组指定文件名和类型）
        files = {
            "image": ('image.jpg', img_bytes, 'image/jpeg')  # 字段名/文件名/类型/内容
        }
        # 发送 POST 请求
        response = requests.post(self.url_server + '/model_bus/label_identify', data=form_data, files=files)
        if response.status_code == 200:
            if response.json()['code'] == 200:
                return response.json()['data']
            else:
                return []
        else:
            return []

    def send_stitch_image(self, img, model_id, field_recommend_count, slider_id, flag, startX, startY, px2distance):
        # 将 OpenCV 图像转换为 JPEG 字节流
        _, img_encoded = cv2.imencode('.jpg', img)
        img_bytes = img_encoded.tobytes()  # 转换为字节流
        # 准备表单数据（注意：修正了字段名中的多余空格）
        form_data = {
            "model_id": model_id,
            "field_recommend_count": field_recommend_count,  # 服务器通常接收字符串形式的表单数据
            "slider_id": slider_id,
            "flag": flag,
            "startX": startX,
            "startY": startY,
            "px2distance": px2distance,
        }
        # 准备文件数据（关键：使用元组指定文件名和类型）
        files = {
            "image": ('image.jpg', img_bytes, 'image/jpeg')  # 字段名/文件名/类型/内容
        }
        # 发送 POST 请求
        response = requests.post(self.url_server + '/model_bus/view_recommend', data=form_data, files=files)
        self.logger.info(response.json())
        # 打印响应状态码和内容
        return response.json()

    def update_stitch_info(self, slide_id, stitch_name):
        data = {
            "slide_id": slide_id,
            "slide_pic": stitch_name
        }
        response = requests.put(self.url_server + "/api/v1_0/slide_pic/", params=data)
        if response.status_code == 200:
            return response.json()['data']
        else:
            return None

    def update_task_info(self, task_id, status, msg, user_id):
        data = {
            "task_id": task_id,
            "status": status,
            "msg": msg,
            "user_id": user_id

        }
        response = requests.put(self.url_server + "/api/v1_0/task_status/", params=data)
        if response.status_code == 200:
            return response.json()['data']
        else:
            return None

    def update_slide_info(self, slide_id, status, msg, user_id):
        data = {
            "slide_id": slide_id,
            "status": status,
            "msg": msg,
            "user_id": user_id

        }
        response = requests.put(self.url_server + "/api/v1_0/slide_status/", params=data)
        if response.status_code == 200:
            return response.json()['data']
        else:
            return None

    def get_plan_info_from_task_id(self, task_id):
        data = {
            "task_id": task_id
        }
        response = requests.get(self.url_server + "/api/v1_0/task/", params=data)
        if response.status_code == 200:
            if response.json()['code'] == 200:
                return response.json()['data']
            else:
                return None
        else:
            return None

    def get_storage(self):
        try:
            response = requests.get(self.url_server + "/api/v1_0/storage")
            return response.json()['data']
        except:
            self.logger.error('get plan list error')
            return {}

    def get_storage_from_storageid(self, storageid):
        try:
            response = requests.get(self.url_server + "/api/v1_0/storage/" + str(storageid))
            if response.status_code == 200:
                if response.json()['code'] == 200:
                    return response.json()['data']
                else:
                    return None
            else:
                return None
        except:
            self.logger.error('get plan list error')
            return None

    def login(self, username, password):
        try:
            data = {
                "username": username,
                "password": password
                , "scopes": self.local_config.serve_username
            }
            response = requests.post(self.url_server + "/api/v1_0/login", params=data)
            if response.status_code == 200:
                if response.json()['msg'] == '登录成功':
                    return True, response.json()['data']
                else:
                    return False, ''
            else:
                return False, ''
        except Exception as e:
            self.logger.error(e)
            return False, ''

    def logout(self, username):
        try:
            data = {
                "username": username
            }
            response = requests.get(self.url_server + "/api/v1_0/logout", params=data)
            if response.status_code == 200:
                if response.json()['msg'] == '退出登录成功':
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            self.logger.error(e)
            return False
