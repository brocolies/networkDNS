"""
서버에게 요청 전송
영화 선택 - 인덱스 수령 - 로컬서버에 전달 - manifest 수령 - hq로 청크 요청 - 청크 동적 선택

< 구현해야 할 내용 >
1. 영화 선택, 인덱스 수령, m
"""

import socket 
from core.protocol import pack, unpack, create_txid
from core.config_utils import parse_config

config = parse_config
netplus_web_addr = config["netplus_web_server"]
local_dns_addr = config["local_dns_server"]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

movie_id = 9
info_req = {}