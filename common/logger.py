"""
logger.py: 로그 찍는 용도
time_utils에서 now_time 반환값 사용
인코딩 변경시 출력할 내용 명세 확인 
"""

import os
import logging
from common.time_utils import now_time

class MyFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        return now_time()

def get_logger(name):
    # logs 폴더 없으면 만들기
    if not os.path.exists("logs"):
        os.mkdir("logs")

    log = logging.getLogger(name)

    # 이미 핸들러 붙어있으면 그대로 리턴 (안그러면 두번 붙음)
    if len(log.handlers) > 0:
        return log

    log.setLevel(logging.DEBUG)
    formatter = MyFormatter("[%(asctime)s] [%(name)s] %(message)s")

    # 콘솔용
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    log.addHandler(console)

    # 파일용
    filepath = "logs/" + name + ".log"
    file_handler = logging.FileHandler(filepath)
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

    return log
