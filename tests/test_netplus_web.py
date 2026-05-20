"""

"""

import socket
from core.protocol import pack, unpack
from core.config_utils import parse_config

config = parse_config()
netplus_web_addr = config["netplus_web_server"]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

test_query = {
    "type": "info_rqst",
    "movie_id": 9,
}

sock.sendto(pack(test_query), netplus_web_addr)
print(f"sent: {test_query}")

payload, _ = sock.recvfrom(4096)
response = unpack(payload)

assert response["type"] == "info_rsp"
assert response["movie_id_echo"] == test_query["movie_id"]
assert response["index_url"] == "index.netplus.com/movie9"
print(f"recv: {response}")