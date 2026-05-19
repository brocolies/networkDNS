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

def main():
    config = parse_config()
    node_name = "netplus_dns_server"
    dns_addr = config[node_name]

    abcdn_url = {
        f"index.netplus.com/movie{i}": f"abCDN.net/cdn{i}"
        for i in range(1,10)
    }

    # UDP 소켓 생성
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 포트 OS에 등록 -> 이 포트로 오는 패킷 수신
    sock.bind(dns_addr)
    # 명세 내용, 로거 생성
    log = get_logger(node_name)
    log.info(f"{node_name}: {dns_addr} ON")

    while True:
        # recvfrom(): (payload, sender addr) 튜플 반환
        payload, client_addr = sock.recvfrom(4096)
        msg = unpack(payload)
        log.info(f"received from {client_addr}: {msg}")

        if msg.get("type") != "dns_rqst":
            log.warning(f"not expected type: {msg}")
            continue
        
        url = msg["url"]
        # dict.get(key, default=None), key가 없을 떄 반환할 내용
        answer = abcdn_url.get(url, "")

        response = {
            "type": "dns_rsp",
            "url_echo": url,
            "txid": msg["txid"], 
            "answer": answer,
        }

        sock.sendto(pack(response), client_addr)
        log.info(f"sent to {client_addr}: {response}")
        
if __name__ == "__main__":
    main()
