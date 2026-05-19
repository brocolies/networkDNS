"""
client가 dns_rqst를 local_dns에 전송하면 manifest 정상적으로 수신하는지

"""
import socket
from core.protocol import pack, unpack
from core.config_utils import parse_config

config = parse_config()
local_dns_addr = config["local_dns_server"]
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

test_query = {
    "type": "dns_rqst",
    "url": "index.netplus.com/movie3",
    "txid": 42
    }

sock.sendto(pack(test_query), local_dns_addr)
print(f"sent: {test_query}")

payload, _ = sock.recvfrom(4096)
response = unpack(payload)

assert response["type"] == "dns_rsp"
assert response["txid"] == test_query["txid"]
assert response["url_echo"] == test_query["url"]
assert response["answer"]["HQ"] == "127.0.0.1:50010"
assert response["answer"]["MQ"] == "127.0.0.1:50011"
assert response["answer"]["LQ"] == "127.0.0.1:50012"

print(f"recv: {response}")