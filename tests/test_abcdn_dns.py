"""
dns_rqst(abCDN url을 달고 옴)가 들어왔을 때, 적절한 manifest file을 반환하는지

"""
import socket
from core.protocol import pack, unpack
from core.config_utils import parse_config

config = parse_config()
abcdn_dns_addr = config["abCDN_dns_server"]

test_query = {
    "type": "dns_rqst",
    "url": "abCDN.net/cdn3",
    "txid": 42,
}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(pack(query), abcdn_dns_addr)
print(f"sent: {query}")

payload, _ = sock.recvfrom(4096) 
response = unpack(payload)

assert response["txid"] == query["txid"]
assert response["url_echo"] == query["url"]
assert response["answer"]["HQ"] == "127.0.0.1:50010"
assert response["answer"]["MQ"] == "127.0.0.1:50011"
assert response["answer"]["LQ"] == "127.0.0.1:50012"

print(f"recv: {response}")
