"""
서버에게 요청 전송
영화 선택 - 인덱스 수령 - 로컬서버에 전달 - manifest 수령 - hq로 청크 요청 - 청크 동적 선택
R = aR + (1-a)fullness -> fullness의 누적 추이 표현
- R이 낮다: 버퍼가 비어 있는 추세 -> 청크가 늦게 도착함 = 네트워크가 혼잡함 -> 화질 하향조절
- R이 높다: 버퍼가 차있는 추세 -> 청크가 제때 잘 도착함 = 네트워크가 정상 -> 화질 올려도 되거나 유지
0 < r < b < 1일 때 -> 각 부등호마다 화질 하향/유지/상향
결정해야 할 것: 처음에 얼마나 버퍼를 채울 것인가? -> 0.3? 이후 필요하다면 튜닝

< 구현해야 할 내용 > / 함수
1. 영화 골라서 Net+ Web에 요청 -> 인덱스 URL 받기 / initial_setup()
2. 그 URL로 local DNS에 질의 -> manifest 받기 / initial_setup()
3. manifest에서 HQ 서버 주소 꺼내서 첫 청크 요청 보내기 / initial_setup()
4. 받기 스레드 만들기 -> push로 오는 청크 계속 받아서 버퍼에 쌓기 / receive_chunks()
5. 버퍼 어느 정도 차면 재생 시작 / play_chunks()
6. 재생 스레드 만들기 -> 버퍼에서 청크 꺼내서 sleep으로 재생 / play_chunks()
7. 재생하면서 버퍼 얼마나 찼나 재고(probe) R 계산하기 / probe()
8. R 보고 화질 올릴지 내릴지 정하기 (decide)
9. 화질 바뀌면 새 서버에 다시 요청 + 전환 로그 찍기 (decide)

< 명세 주의사항 > 
1. 영화의 적절한 범위에서 네트워크 딜레이 결정 -> streaming.py 파일 수정
    - 적절한 delay 값 선택 필요 random.uniform(x, y) 
2. 첫 k번 probe 전까지는 R 무의미하다는 것 반영
3. 적절한 alpha 값 선정 필요 0.8은 너무 이전 애들이 반영 많이 돼서 변화가 더딤
    - 적정값 테스트해서 찾기

"""

import socket
import queue
import time
import threading
from core.protocol import pack, unpack, create_txid
from core.time_utils import time_to_ms
from core.config_utils import parse_config
from core.log_utils import get_logger

buffer = queue.Queue()
selected_encoding = "HQ"
n = 10 # 버퍼 크기
alpha = 0.8
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
manifest = None 
movie_id = None 
node_name = "client"
log = get_logger(node_name)

def main():
    initial_setup()

# movie_id 선택 -> index 수령 -> local에 질의 -> manifest local에게 수령 -> CDN에 chunk 첫 요청
def initial_setup():
    global manifest, movie_id
    config = parse_config()
    netplus_web_addr = config["netplus_web_server"]
    local_dns_addr = config["local_dns_server"]

    # 1. 보고싶은 영화 클릭 -> web server에 request 전송
    movie_id = 9
    info_req = {
        "type": "info_rqst", 
        "movie_id": movie_id,
    }
    sock.sendto(pack(info_req), netplus_web_addr)

    # 2. rsp에서 index 수령 / 수신 로그
    payload, _ = sock.recvfrom(4096)
    movie_index_url = unpack(payload)["index_url"]
    log.info(f"received from {netplus_web_addr}: {movie_index_url}")

    # 3. local DNS에 인덱스 질의 
    dns_req = {
        "type": "dns_rqst",
        "url": movie_index_url,
        "txid": create_txid(),
    }
    sock.sendto(pack(dns_req), local_dns_addr)

    # 4. mainfest 수령 / 수신 로그 
    payload, _ = sock.recvfrom(4096)
    manifest = unpack(payload)["answer"]
    log.info(f"received from {local_dns_addr}: {manifest}")

    # 5. CDN 서버에 첫 청크 요청
    ip, port = manifest[selected_encoding].split(":")
    port = int(port)
    initial_chunk_addr = (ip, port)

    chunk_req = {
        "type": "chunk_rqst",
        "movie_id": movie_id,
        "encoding_type": selected_encoding,
        "chunk_index": 0,
        "last_watched_time": "00:00:00:000",
    }
    sock.sendto(pack(chunk_req), initial_chunk_addr)

def receive_chunks():
    # CDN 서버에서 청크 수령 / 버퍼에 저장 / 수신 로그
    while True:
        payload, cdn_addr = sock.recvfrom(4096)
        chunk = unpack(payload)
        log.info(f"received from {cdn_addr}: {chunk}")
        if chunk["encoding_type"] == selected_encoding:
            buffer.put(chunk)

def play_chunks():
    probe_cnt = 0
    R_buffer = 0.0
    # 버퍼에 저장된 청크 가져와서 재생 -> 초기값 정해야함(얼마나 저장하고 시작할지)
    # sleep으로 영상 재생 구현
    initial_size = int(n * 0.3)
    while buffer.qsize() < initial_size:
            time.sleep(0.1) # initial_size보다 커질 때까지 대기

    while True:
        chunk = buffer.get()
        probe_cnt += 1
        R_buffer = probe_buffer(R_buffer)
        select_encoding(R_buffer, probe_cnt)
        calculate_length_to_s = (time_to_ms(chunk["end_time"]) - time_to_ms(chunk["start_time"])) / 1000
        time.sleep(calculate_length_to_s)
        if time_to_ms(chunk["end_time"]) >= time_to_ms("00:01:59:000"):
            break

def probe_buffer(R_buffer):
    # R_buffer 값 계산 (명세 공식 참고)
    fullness = buffer.qsize() / n
    R_buffer = alpha * R_buffer + (1 - alpha) * fullness
    return R_buffer

def select_encoding(R_buffer, probe_cnt):
    global selected_encoding

    # 첫 k번 probe 전까지는 R 무의미하다는 것 반영
    if probe_cnt <= 5:
        return 
    beta, gamma = 0.8, 0.4
    

if __name__ == "__main__":
    main()