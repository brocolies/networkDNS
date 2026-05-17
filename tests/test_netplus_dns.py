import socket
from core.protocol import pack, unpack 
from core.config_utils import parse_config

config = parse_config()
target = config["netplus_dns_server"]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
query = {"type": "dns_rqst", "url": "index.netplus.com/movie3", "txid": 42}
sock.sendto(pack(query), target)
print(f"sent: {query}")

data, _ = sock.recvfrom(4096)
response = unpack(data)
assert response["txid"] == query["txid"]
assert response["url_echo"] == query["url"]
assert response["answer"] == "abCDN.net/cdn3"
print(f"recv: {response}")