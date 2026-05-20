"""
영상번호에 따른 인덱스 URL 응답
< 구현할 내용 >
- 클라이언트 패킷 수신
- movie id 기반으로 index url 응답
- 응답 송신
"""

import socket
from core.protocol import pack, unpack 
from core.log_utils import get_logger
from core.config_utils import parse_config

def main():
    config = parse_config()
    node_name = "netplus_web_server"
    netplus_web_addr = config[node_name]

    movie_url = {
        index: f"index.netplus.com/movie{index}"
        for index in range(1, 10)
    }

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(netplus_web_addr)
    log = get_logger(node_name)
    log.info(f"{node_name}: {netplus_web_addr} ON")

    while True:
        payload, client_addr = sock.recvfrom(4096)
        msg = unpack(payload)
        log.info(f"received from {client_addr}: {msg}")

        if msg.get("type") != "info_rqst":
            log.warning(f"unexpected type: {msg}")
            continue

        movie_id = msg["movie_id"]
        wanted_index_url = movie_url.get(movie_id, "")
        response = {
            "type": "info_rsp",
            "movie_id_echo": movie_id,
            "index_url": wanted_index_url,
        }

        sock.sendto(pack(response), client_addr)
        log.info(f"sent to {client_addr}: {response}")

if __name__ == "__main__":
    main()
    