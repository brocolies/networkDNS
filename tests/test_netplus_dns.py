"""
Net+ DNS 단독 검증
실행 전 터미널에서 `python -m dns.netplus_dns` 먼저 띄울 것
"""
import socket
from core.protocol import pack, unpack
from core.config_utils import parse_config

config = parse_config()
netplus_addr = config["netplus_dns_server"]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# test용 query
test_query = {
    "type": "dns_rqst", 
    "url": "index.netplus.com/movie3", 
    "txid": 42
    }

# sendto: 보낼 bytes/주소
sock.sendto(pack(query), netplus_addr)
print(f"sent: {query}")

# data = 응답 bytes
# _ = 보낸 사람 주소 (이미 알고 있는 Net+ DNS라 안 씀)
payload, _ = sock.recvfrom(4096)
response = unpack(payload)

# 6단계 · 응답 검증 (assert — 실패 시 즉시 AssertionError)
assert response["txid"] == query["txid"]                 # txid echo 확인
assert response["url_echo"] == query["url"]              # url echo 확인
assert response["answer"] == "abCDN.net/cdn3"            # 매핑 lookup 결과 확인

print(f"recv: {response}")