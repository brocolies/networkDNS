"""

"""

import socket
from core.protocol import pack, unpack

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

test_query = {
    "type": "chunk_rqst",
    "movie_id": 9,
    "encoding_type": "HQ",
    "chunk_index": 0,
    "last_watched_time": "00:00:00:000",
}

send_addr = ("127.0.0.1", 50010)
sock.sendto(pack(test_query), send_addr)

index_cnt = 0;

for index_cnt in range(45):
    payload, _ = sock.recvfrom(4096)
    response = unpack(payload)

    assert response["type"] == "chunk_rsp"
    assert response["chunk_index"] == index_cnt

    print(f"recv: chunk[{response['chunk_index']}]")
    if response["chunk_index"] == 44:
        print(f"movie_id: {response['movie_id']} sent complished")
        break