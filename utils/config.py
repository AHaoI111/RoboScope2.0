class Configuration:
    def __init__(self):
        """
        程序初始化参数配置类
        """
        # 应用基本配置
        self.app_name = "RoboScope"
        self.version = "1.0.0"

        # 本地接口网络配置
        self.local_host = '0.0.0.0'
        self.local_port = 51121

        # ScopeCore服务器配置
        self.serve_host = 'localhost'
        self.serve_port = 8000
        self.serve_username = 'roboscope_s1'

