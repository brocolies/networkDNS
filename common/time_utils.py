"""
time_utils.py: protocols.py의 시간 관련 필드에 사용할 함수
xx:yy:zz:abc 형태로 출력

의문: 영상 1개를 재생하다가 중간에 다른 영상 재생 쿼리 보내면 어떻게 하지?
-> 일단 단일 세션 기준으로 구현
"""
from datetime import datetime

def now_time() -> str:
    now = datetime.now()
    formatted_time = now.strftime("%H:%M:%S:%f")[:-3]
    return formatted_time

def time_to_ms(time: str) -> int:
    h, m, s, ms = map(int, time.split(":"))
    calculated_ms = h * 3600000 + m * 60000 + s * 1000 + ms
    return calculated_ms

def elapsed_time(start_time: str, end_time: str) -> int:
    elapsed_ms = time_to_ms(end_time) - time_to_ms(start_time)
    return elapsed_ms