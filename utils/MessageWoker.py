# -*- encoding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor
from queue import Queue


class Message_Woker:
    """
    """

    def __init__(self, maxworkers, queuenumber, requester):
        """
        """
        super().__init__()
        # 初始化图像变量
        self.requester = requester

        # 初始化队列
        self.queue = Queue(queuenumber)

        # 初始化状态变量
        self.stopped = False  # 停止标志
        self.executor = ThreadPoolExecutor(max_workers=maxworkers)
        self.maxworkers = maxworkers
        self.start_processing()

    def process_queue(self):
        """
        """
        while not self.stopped:
            try:
                # 从队列中获取任务数据
                [scan_info, file_name, file_names, location, view_filed_group, img, is_end] = self.queue.get(
                    timeout=0.1)
                field_recommend = scan_info['field_recommend']
                field_stitch = scan_info['field_stitch']
                slide_id = scan_info['slide_id']
                # 高低倍配合扫描
                if field_recommend:
                    # 发送视野推荐拼图
                    if field_stitch and self.requester is not None and img is not None and view_filed_group == 0:
                        # data = self.requester.send_stitch_image(img,
                        #                                         scan_info['field_scan']['field_recommend_model_id'],
                        #                                         scan_info['field_scan']['field_recommend_count'],
                        #                                         slide_id, 'once', scan_info['field_scan_startX']
                        #                                         , scan_info['field_scan_startY'],
                        #                                         scan_info['field_scan']['len_params']['calibration'])
                        # center_points = data['data']['center_points']
                        # center_points_px = data['data']['center_points_px']
                        # self.high_points_signal.emit(center_points,center_points_px)
                        data = self.requester.update_stitch_info(slide_id, file_name)
                        del data

                    elif field_stitch and self.requester is not None and img is None and view_filed_group != 0:
                        self.requester.create_view(slide_id, file_name, file_names, location, view_filed_group, is_end)
                else:
                    if self.requester is not None and img is None:
                        self.requester.create_view(slide_id, file_name, file_names, location, view_filed_group, is_end)
                del field_recommend
                del field_stitch
                del slide_id
                del scan_info
                del file_name
                del location
                del view_filed_group
                del img

                self.queue.task_done()
            except Exception as e:
                pass

    def enqueue(self, scan_info, file_name, file_names, location, view_filed_group, img, is_end):
        """
        """
        try:
            self.queue.put_nowait(
                [scan_info, file_name, file_names, location, view_filed_group, img, is_end])
        except:
            print('imageSaver queue is full, image discarded')

    def start_processing(self):
        """
        启动线程池执行队列中的任务。
        """
        for _ in range(self.maxworkers):
            self.executor.submit(self.process_queue)

    def stop(self):
        """
        停止处理队列中的任务。
        """
        self.stopped = True
