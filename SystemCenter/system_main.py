# -*- coding: utf-8 -*-
# @Time    : 2025/04/19 12:33
# @Author  : DSTBP
# @File    : SystemCenter/system_main.py
# @Description : 系统中心主函数
from loguru import logger
from business.core import SystemCenter
from business.config import SystemCenterConfig

if __name__ == "__main__":
    # 启动可信中心服务（8085端口）
    sc = SystemCenter(SystemCenterConfig(
        host='10.24.37.4',
        port=8085
    ))

    sc.initialize({
        # 'p': getPrime(1024),  # 生成1024位素数
        # P-192（secp192r1）
        'p': 6277101735386680763835789423207666416083908700390324961279,
        'a': -3,
        'b': 2455155546008943817740293915197451784769108058161191238065,
        'Gx': 602046282375688656758213480587526111916698976636884684818,
        'Gy': 174050332293622031404857552280219410364023488927386650641,
        'N': 6277101735386680763835789423176059013767194773182842284081,
        'n': 5,  # 云服务器总数
        't': 3  # 门限值
    })
    sc.run_server()

    # 保持主线程运行
    try:
        while True:
            pass
    except KeyboardInterrupt:
        logger.info("系统关闭")