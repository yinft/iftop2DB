import os
import urllib

PASS_WORD = urllib.parse.quote("123456")


class BaseConfig:  # 基本配置类
    DATABASE_URL = os.getenv('DATABASE_URL', 'some secret words')
    #     网卡
    NETWORK_INTERFACE = 'en0'


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    DATABASE_URL = 'mongodb://root:123456@192.168.100.122:27017/iftop?authSource=admin'
    NETWORK_INTERFACE = 'en0'


class PreConfig(BaseConfig):
    DATABASE_URL = 'mongodb://admin:'+PASS_WORD+'@192.168.100.251:27017/iftop?authSource=admin'
    NETWORK_INTERFACE = 'eth0'


class MasterConfig(BaseConfig):
    DATABASE_URL = 'mongodb://admin:'+PASS_WORD+'@192.168.100.143:27017/iftop?authSource=admin'
    NETWORK_INTERFACE = 'eth0'


config = {
    'development': DevelopmentConfig,
    'pre': PreConfig,
    'master': MasterConfig
}
