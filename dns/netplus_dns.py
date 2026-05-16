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
from core.config_utils import parse_config

abCDN_URL = {
    f"index.netplus.com/movie{i}": f"abCDN.net/cdn{i}"
    for i in range(1,10)
}

def main():
    parsed_config = parse_config()
    DNS_addr = parsed_config["netplus_dns_server"]
    dns_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dns_socket.bind(DNS_addr)
    
    log = get_logger("netplus_dns")
    log.info(f"")

    