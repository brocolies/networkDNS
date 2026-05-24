"""
서버에게 요청 전송
영화 선택 - 인덱스 수령 - 로컬서버에 전달 - manifest 수령 - hq로 청크 요청 - 청크 동적 선택

< 구현해야 할 내용 >
1. 영화 선택
2. 인덱스 수령
3. local DNS에 인덱스 질의
4. manifest 수령
5. 버퍼 생성해서 cdn server에게 들어오는 청크 저장
"""

import socket 
from core.protocol import pack, unpack, create_txid
from core.config_utils import parse_config
from core.log_utils import get_logger

def main():
    node_name = "client"
    log = get_logger(node_name)
    config = parse_config()
    netplus_web_addr = config["netplus_web_server"]
    local_dns_addr = config["local_dns_server"]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 보고싶은 영화 클릭 -> web server에 request 전송
    movie_id = 9
    info_req = {
        "type": "info_rqst", 
        "movie_id": movie_id,
    }
    sock.sendto(pack(info_req), netplus_web_addr)

    # rsp에서 index 수령 / 수신 로그
    payload, _ = sock.recvfrom(4096)
    movie_index_url = unpack(payload)["index_url"]
    log.info(f"received from {netplus_web_addr}: {movie_index_url}")

    # local DNS에 인덱스 질의 
    dns_req = {
        "type": "dns_rqst",
        "url": movie_index_url,
        "txid": create_txid(),
    }
    sock.sendto(pack(dns_req, local_dns_addr))

    # mainfest 수령 / 수신 로그 
    payload, _ = sock.recvfrom(4096)
    manifest = unpack(payload)["answer"]
    log.info(f"received from {local_dns_addr}: {manifest}")

