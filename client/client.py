"""
서버에게 요청 전송
영화 선택 - 인덱스 수령 - 로컬서버에 전달 - manifest 수령 - hq로 청크 요청 - 청크 동적 선택
R = aR + (1-a)fullness -> fullness의 누적 추이 표현
- R이 낮다: 버퍼가 비어 있는 추세 -> 청크가 늦게 도착함 = 네트워크가 혼잡함 -> 화질 하향조절
- R이 높다: 버퍼가 차있는 추세 -> 청크가 제때 잘 도착함 = 네트워크가 정상 -> 화질 올려도 되거나 유지
0 < r < b < 1일 때 -> 각 부등호마다 화질 하향/유지/상향
결정해야 할 것: 처음에 얼마나 버퍼를 채울 것인가? -> 0.3? 이후 필요하다면 튜닝

< 구현해야 할 내용 >
1. 영화 선택
2. 인덱스 수령
3. local DNS에 인덱스 질의
4. manifest 수령
5. CDN 서버에 요청 전송
6. 버퍼 생성해서 cdn server에게 들어오는 청크 저장(일정량 저장 이후 재생)
7. sleep 사용해서 영상 재생

"""

import socket 
import queue
from core.protocol import pack, unpack, create_txid
from core.config_utils import parse_config
from core.log_utils import get_logger

def main():
    node_name = "client"
    log = get_logger(node_name)
    config = parse_config()
    netplus_web_addr = config["netplus_web_server"]
    local_dns_addr = config["local_dns_server"]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 보고싶은 영화 클릭 -> web server에 request 전송
    movie_id = 9
    info_req = {
        "type": "info_rqst", 
        "movie_id": movie_id,
    }
    sock.sendto(pack(info_req), netplus_web_addr)

    # rsp에서 index 수령 / 수신 로그
    payload, _ = sock.recvfrom(4096)
    movie_index_url = unpack(payload)["index_url"]
    log.info(f"received from {netplus_web_addr}: {movie_index_url}")

    # local DNS에 인덱스 질의 
    dns_req = {
        "type": "dns_rqst",
        "url": movie_index_url,
        "txid": create_txid(),
    }
    sock.sendto(pack(dns_req), local_dns_addr)

    # mainfest 수령 / 수신 로그 
    payload, _ = sock.recvfrom(4096)
    manifest = unpack(payload)["answer"]
    log.info(f"received from {local_dns_addr}: {manifest}")

    # CDN 서버에 청크 요청
    ip, port = manifest["HQ"].split(":")
    port = int(port)
    hq_chunk_addr = (ip, port)

    chunk_req = {
        "type": "chunk_rqst",
        "movie_id": movie_id,
        "encoding_type": "HQ",
        "chunk_index": 0,
        "last_watched_time": "00:00:00:000",
    }
    sock.sendto(pack(chunk_req), hq_chunk_addr)

    # CDN 서버에서 청크 수령 / 버퍼에 저장 / 수신 로그
    buffer = queue.Queue()
    initial_encoding = "HQ"
    
    while True:
        payload, _ = sock.recvfrom(4096)
        chunk = unpack(payload)
        log.info(f"received from {hq_chunk_addr}: {chunk}")
        buffer.append(chunk)

if __name__ == "__main__":
    main()