import json


def apply_task_info(config_info):
    task_info = {}
    if config_info['Microscope']['sys']['当前系统'] == 'single':
        boxes = [1, 2, 3, 4]
        task_info = {
            'sys': config_info['Microscope']['sys']['当前系统'],
            'Multiple': int(config_info['Microscope']['single']['单镜头倍数']),
            'FocusMode': config_info['Microscope']['single']['单镜头对焦方式'],
            'center_x': float(config_info['Microscope']['single']['单镜头扫描中心xy']['x']),
            'center_y': float(config_info['Microscope']['single']['单镜头扫描中心xy']['y']),
            'region_w': int(config_info['Microscope']['single']['单镜头扫描区域']['w']),
            'region_h': int(config_info['Microscope']['single']['单镜头扫描区域']['h']),
            'calibration': float(config_info['Camera']['single']['单镜头标定']),
            'zpos_start': float(config_info['Microscope']['single']['对焦经验值单镜头']),
            'focu_number': int(config_info['Microscope']['single']['单镜头对焦步数']),
            'focu_size': float(config_info['Microscope']['single']['单镜头对焦分辨率']),
            'ImageStitchSize': int(config_info['ImageSaver']['imagestitchsize']),
            'correction_model': int(config_info['ImageSaver']['correction_model']),
            'fcous_Gap': int(config_info['Microscope']['single']['单镜头隔点对焦步长']),
            'Xend': float(config_info['Microscope']['sys']['xend']),
            'Yend': float(config_info['Microscope']['sys']['yend']),
            'Yend': float(config_info['Microscope']['sys']['scanmode']),
            'savepath': config_info['ImageSaver']['savepath'],
            'boxes': boxes,
            'Network': config_info['Network']['flag'],
            'pump': config_info['Loader']['oilflag']
        }
    elif config_info['Microscope']['sys']['当前系统'] == 'double':
        boxes = [1, 2, 3, 4]
        task_info = {
            'sys': config_info['Microscope']['sys']['当前系统'],
            'scanmode': config_info['Microscope']['sys']['scanmode'],
            'scanmultiple': config_info['Microscope']['sys']['scanmultiple'],
            'Multiple_low': int(config_info['Microscope']['low']['低倍倍数']),
            'Multiple_high': int(config_info['Microscope']['high']['高倍倍数']),
            'FocusMode_low': config_info['Microscope']['low']['低倍对焦方式'],
            'FocusMode_high': config_info['Microscope']['high']['高倍对焦方式'],
            'center_x_low': float(config_info['Microscope']['low']['低倍扫描中心xy']['x']),
            'center_y_low': float(config_info['Microscope']['low']['低倍扫描中心xy']['y']),
            'center_x_high': float(config_info['Microscope']['high']['高倍扫描中心xy']['x']),
            'center_y_high': float(config_info['Microscope']['high']['高倍扫描中心xy']['y']),
            'region_w_low': int(config_info['Microscope']['low']['低倍扫描区域']['w']),
            'region_h_low': int(config_info['Microscope']['low']['低倍扫描区域']['h']),
            'region_w_high': int(config_info['Microscope']['high']['高倍扫描区域']['w']),
            'region_h_high': int(config_info['Microscope']['high']['高倍扫描区域']['h']),
            'calibration_low': float(config_info['Camera']['low']['低倍标定']),
            'calibration_high': float(config_info['Camera']['high']['高倍标定']),
            'zpos_start_low': float(config_info['Microscope']['low']['对焦经验值低倍']),
            'zpos_start_high': float(config_info['Microscope']['high']['对焦经验值高倍']),
            'focu_number_low': int(config_info['Microscope']['low']['低倍对焦步数']),
            'focu_number_high': int(config_info['Microscope']['high']['高倍对焦步数']),
            'focu_size_low': float(config_info['Microscope']['low']['低倍对焦分辨率']),
            'focu_size_high': float(config_info['Microscope']['high']['高倍对焦分辨率']),
            'ImageStitchSize': int(config_info['ImageSaver']['imagestitchsize']),
            'correction_model': int(config_info['ImageSaver']['correction_model']),
            'fcous_Gap_low': int(config_info['Microscope']['low']['低倍隔点对焦步长']),
            'fcous_Gap_high': int(config_info['Microscope']['high']['高倍隔点对焦步长']),
            'Xend': float(config_info['Microscope']['sys']['xend']),
            'Yend': float(config_info['Microscope']['sys']['yend']),
            'lens_gap_x': float(config_info['Microscope']['sys']['lensgapx']),
            'lens_gap_y': float(config_info['Microscope']['sys']['lensgapy']),
            'savepath': config_info['ImageSaver']['savepath'],
            'boxes': boxes,
            'Network': config_info['Network']['flag'],
            'pump': config_info['Loader']['oilflag']

        }
    return task_info


def create_task_plan_default(task_info):
    task_info['name'] = 'default'
    task_info['pre_request_flag'] = False
    task_info['task_id'] = None
    task_info['task_type_id'] = None
    task_info['scan_label'] = True
    task_info['field_view_type'] = None

    return task_info


def create_task_plan(task_info, download_plan):
    task_info['pre_request_flag'] = False
    task_info['task_id'] = None
    task_info['name'] = download_plan['name']
    task_info['task_type_id'] = download_plan['task_type_id']
    task_info['scan_label'] = download_plan['scan_label']
    task_info['field_view_type'] = download_plan['field_view_type']
    task_info['camera'] = download_plan['camera']
    if task_info['sys'] == 'single':
        task_info['scanmode'] = False
        task_info['FocusMode'] = download_plan['focus_mode']['id']
        task_info['region_w'] = download_plan['scan_width']
        task_info['region_h'] = download_plan['scan_hight']
        if download_plan['focus_mode']['Gap_flag'] == "true":
            task_info['fcous_Gap'] = download_plan['focus_mode']['gap']
        task_info['recommend_view_source'] = None
    elif task_info['sys'] == 'double':
        if download_plan['field_view_type'] != "None" and download_plan['camera'] == "all":
            task_info['scanmode'] = True
            task_info['region_w_low'] = download_plan['scan_width']
            task_info['region_h_low'] = download_plan['scan_hight']
            task_info['FocusMode_low'] = download_plan['focus_mode']['id']
            if download_plan['focus_mode']['Gap_flag'] == "true":
                task_info['fcous_Gap_low'] = download_plan['focus_mode']['gap']
            task_info['scan_api'] = download_plan['field_view_model_url']
            task_info['max_views'] = download_plan['max_views']
            task_info['max_areas'] = download_plan['max_areas']
            task_info['recommend_view_source'] = download_plan['recommend_view_source']
        elif download_plan['field_view_type'] == "None" and download_plan['camera'] != "all":
            task_info['scanmode'] = False
            task_info['scanmultiple'] = download_plan['camera']
            if download_plan['camera'] == "low":
                task_info['region_w_low'] = download_plan['scan_width']
                task_info['region_h_low'] = download_plan['scan_hight']
                task_info['FocusMode_low'] = download_plan['focus_mode']['id']
                if download_plan['focus_mode']['Gap_flag'] == "true":
                    task_info['fcous_Gap_low'] = download_plan['focus_mode']['gap']
                task_info['recommend_view_source'] = None
            elif download_plan['camera'] == "high":
                task_info['region_w_high'] = download_plan['scan_width']
                task_info['region_h_high'] = download_plan['scan_hight']
                task_info['FocusMode_high'] = download_plan['focus_mode']['id']
                if download_plan['focus_mode']['Gap_flag'] == "true":
                    task_info['fcous_Gap_high'] = download_plan['focus_mode']['gap']
                task_info['recommend_view_source'] = None
    return task_info


def save_json(data, filename):
    """
    保存数据到 JSON 文件

    参数:
    data (dict 或 list): 要保存的数据，通常是字典或列表。
    filename (str): 文件路径或文件名。
    """
    try:
        with open(filename + '/' + data['name']+'.json', 'w', encoding='utf-8') as f:
            # 使用 json.dump 将 Python 数据结构写入文件
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"数据已成功保存到 {filename + '/' + data['name']}")
    except Exception as e:
        print(f"保存文件时发生错误: {e}")


def read_json(filename):
    """
    读取 JSON 文件并返回数据

    参数:
    filename (str): 文件路径或文件名。

    返回:
    dict 或 list: 从 JSON 文件中读取的数据，通常是字典或列表。
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            # 使用 json.load 从文件中读取数据
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"文件 {filename} 不存在")
        return None
