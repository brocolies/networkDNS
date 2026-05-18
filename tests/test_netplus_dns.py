"""
Net+ DNS 단독 검증
실행 전 터미널에서 `python -m dns.netplus_dns` 먼저 띄울 것
"""
import socket
from core.protocol import pack, unpack
from core.config_utils import parse_config

config = parse_config()
netplus_dns_addr = config["netplus_dns_server"]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 3단계 · 테스트용 dns_rqst 메시지 만들기
# url: 임의 영상 인덱스 (movie3 — INDEX_TO_ABCDN에 등록된 키)
# txid: 임의값 42. 응답에 echo돼서 돌아오는지 검증용
query = {
    "type": "dns_rqst", 
    "url": "index.netplus.com/movie3", 
    "txid": 42
    }

# 4단계 · pack(dict→bytes) 후 Net+ DNS에 송신
sock.sendto(pack(query), netplus_dns_addr)
print(f"sent: {query}")

# 5단계 · 응답 대기 (recvfrom은 블로킹)
# data = 응답 bytes
# _ = 보낸 사람 주소 (이미 알고 있는 Net+ DNS라 안 씀)
data, _ = sock.recvfrom(4096)
response = unpack(data)

# 6단계 · 응답 검증 (assert — 실패 시 즉시 AssertionError)
assert response["txid"] == query["txid"]                 # txid echo 확인
assert response["url_echo"] == query["url"]              # url echo 확인
assert response["answer"] == "abCDN.net/cdn3"            # 매핑 lookup 결과 확인

print(f"recv: {response}")