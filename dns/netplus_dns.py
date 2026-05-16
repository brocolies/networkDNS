"""
Local DNS가 처음으로 쿼리를 보내는 곳
여기에서 영상 1 ~ 9 각각을 담당하는 abCDN 주소 응답
해야할 일 
1. local dns의 요청 받아서 영상에 해당하는 abCDN 주소 응답하기
2. config에서 자기 포트 parsing해오기 -> bind 
3. 
"""

import socket
from core.protocol import pack, unpack
from core.log_utils import get_logger

# config.txt parsing
def parse_config(path="config.txt"):
    with open(path) as file:
        for addresses in file:
            if addresses.startswith("netplus_dns_server"):
                addresses = addresses.strip()
                key, val = addresses.split("=", 1)
                val = val.strip()
                ip, port = val.split(":", 1)
    return ip, port

parse_config()