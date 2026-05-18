"""
클라이언트에게 rqst 수신 

보안모듈로 올린 txid 주의 
txid: 16-bit 무작위 ID: query와 resp 매칭
송신자: query마다 새로 생성하고 수신자는 응답에 그대로 echo해서 전송
수신자: 전송한 txid 저장하고 응답이 오면 비교

< 구현 필요 기능 >
1. 클라이언트로부터 UDP 패킷 수신/파싱
2. type 필터링 -> dns_rqst
3. url -> manifest dict 매핑

"""

import socket
from core.protocol import pack, unpack, create_txid
from core.config_utils import parse_config

config = parse_config()
local_addr = config["local_dns_server"]
netplus_addr = config["netplus_dns_server"]
abcdn_addr = config["local_dns_server"]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(local_addr)

# 클라이언트로부터 UDP 패킷 수신 
payload, client_addr = sock.recvfrom(4096)
client_msg = unpack(payload)

# 클라이언트에게 응답할 때 url_echo, txid에 넣어서 보내야 함
client_url = client_msg["url"]
client_txid = client_msg["txid"]

netplus_txid = create_txid()
send_to_netplus_dns = {
    "type": "dns_rqst",
    "url": client_url,
    "txid": netplus_txid,
}



