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

ABCDN_URL = {
    f"index.netplus.com/movie{i}": f"abCDN.net/cdn{i}"
    for i in range(1,10)
}

def main():
    parsed_config = parse_config()
    node_name = "netplus_dns_server"
    dns_addr = parsed_config[node_name]
    dns_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dns_socket.bind(dns_addr)
    
    log = get_logger("netplus_dns")
    log.info(f"{node_name}: {dns_addr} ON")

    while True:
        payload, client_addr = dns_socket.recvfrom(4096)
        ip, port = client_addr
        msg = unpack(payload)
        log.info(f"received from {ip}:{port}: {msg}")

        if msg.get("type") != "dns_rqst":
            log.warning(f"Not expected type: {msg}")
            continue
        
        url = msg["url"]
        answer = ABCDN_URL.get(url, "")

        response = {
            "type": "dns_rsp",
            "url_echo": url,
            "txid": msg["txid"], 
            "answer": answer,
        }

        dns_socket.sendto(pack(response), client_addr)
        log.info(f"sent to {dns_addr}: {response}")
        
    main()
