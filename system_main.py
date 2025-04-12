"""
Description:
Author: DSTBP
Date: 2025-04-08 21:06:13
LastEditTime: 2025-04-09 08:28:38
LastEditors: DSTBP
"""
from loguru import logger
from SystemCenter.core.systemcenter import SystemCenter
from SystemCenter.model.config import SystemCenterConfig

if __name__ == "__main__":
    # 启动可信中心服务（6666端口）
    sc = SystemCenter(SystemCenterConfig(
        host='127.0.0.1',
        port=6666
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