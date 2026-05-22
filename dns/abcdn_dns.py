"""
abCDN DNS server: manifest file 응답
화질별로 다른 서버에서 관리
"""

import socket 
from core.protocol import pack, unpack
from core.log_utils import get_logger
from core.config_utils import parse_config

def main():
    node_name = "abcdn_dns_server"
    parsed_config = parse_config()
    abcdn_addr = parsed_config[node_name]

    # abCDN URL → 화질별 streaming 서버 주소 매핑 (이 노드 내부에서만 쓰는 lookup 테이블)
    manifest_url = {
        f"abCDN.net/cdn{i}": {
            "HQ": "127.0.0.1:50010",
            "MQ": "127.0.0.1:50011",
            "LQ": "127.0.0.1:50012",
        }
        for i in range(1,10)
    }

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(abcdn_addr)
    log = get_logger(node_name)
    log.info(f"{node_name}: {abcdn_addr} ON")

    while True:
        payload, client_addr = sock.recvfrom(4096) 
        msg = unpack(payload)
        log.info(f"received from {client_addr}: {msg}")

        if msg.get("type") != "dns_rqst":
            log.warning(f"not expected type: {msg}")
            continue
    
        url = msg["url"]
        answer = manifest_url.get(url, {})

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