"""
클라이언트가 manifest 받은 뒤에 streaming 서버 요청 보내고, 이에 따른 청크 수신
chunk_rqst = {
    "type": "chunk_rqst",
    "movie_id": int,
    "encoding_type": str, # HQ/MQ/LQ
    "chunk_index": int,
    "last_watched_time": str, # 시청한 chunk의 마지막 시간 서버에 전달
}

chunk_rsp = {
    "type": "chunk_rsp",
    "movie_id": int,
    "encoding_type": str, 
    "chunk_index": int,
    "start_time": str,
    "end_time": str,
}
< 구현 필요 기능 > 
- 

+ 시나리오 결정 ->

"""

import sys
import json
import socket
import random
import time
from core.protocol import pack, unpack
from core.log_utils import get_logger
from core.time_utils import time_to_ms

# 몇 번째 청크부터 보낼지 
# 
def cal_start_index(chunks, last_watched_time):
    index = 0
    ms_last_watched_time = time_to_ms(last_watched_time)

    for i in range(len(chunks)):
        if time_to_ms(chunks[i]["start_time"]) <= ms_last_watched_time:
            index = i
    return index



def main():
    encoding_type = sys.argv[1]
    ports = {"HQ": 50010, "MQ": 50011, "LQ": 50012}
    port = ports[encoding_type]

    with open("data/chunks.json") as file:
        all_chunks = json.load(file)
    
    # 영화 9개 전체에 대한 청크 모은 딕셔너리 
    all_movie_chunks = {}
    for movie_id in all_chunks:
        all_movie_chunks[movie_id] = all_chunks[movie_id][encoding_type]
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", port))

    log = get_logger("streaming " + encoding_type)
    log.info(f"{encoding_type} ON: {port}")
    
    # congestion delay 시간 임의 설정 00:15 ~ 01:20까지 
    congestion_delay_start_ms = 15 * 1000 
    congestion_delay_end_ms = 80 * 1000

    while True:
        payload, client_addr = sock.recvfrom(4096)
        msg = unpack(payload)
        log.info(f"received from {client_addr}: {msg}")

        movie_id = str(msg["movie_id"])
        rqst_movie_chunks = all_movie_chunks[movie_id]

        start_index = cal_start_index(rqst_movie_chunks, msg["last_watched_time"])

        for i in range(start_index, len(rqst_movie_chunks)): 
            # server delay 구현 -> 일정 구간에서는 증가해야 함
            # 적절한 혼잡 발생 영상범위1 설정 필요
            # congestion delay 시간 임의 설정 00:15 ~ 01:20까지 

            if 15 * 1000 <= chunk_start_ms < 80 * 1000:
                server_to_client_delay = random.uniform(5.0, 7.0)
            else:
                server_to_client_delay = random.uniform(0.1, 0.4)
            time.sleep(server_to_client_delay)

            response = {
                "type": "chunk_rsp",
                "movie_id": int(movie_id),
                "encoding_type": encoding_type,
                "chunk_index": i,
                "start_time": rqst_movie_chunks[i]["start_time"],
                "end_time": rqst_movie_chunks[i]["end_time"],
            }
            sock.sendto(pack(response), client_addr)

if __name__ == "__main__":
    main()

        

        
