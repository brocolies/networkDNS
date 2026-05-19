"""
protocol.py: 1과 2를 정의하는 파일
    1. 메시지: JSON dict의 key:field가 어떤 모양인지 정의
    2. 운반: UDP 페이로드에 JSON bytes 넣기 → pack/unpack 함수 사용

메시지 종류 분류
    1. 클라이언트 <-> Net+ 서버: info_rqst/rsp
    2. DNS 질답: dns_rqst/rsp
    3. 클라이언트 <-> abCDN: chunk_rqst/rsp
"""
import json
import secrets

HQ, MQ, LQ = "HQ", "MQ", "LQ" # chunk에서 사용할 상수 강제

info_rqst = {
    "type": "info_rqst", 
    "movie_id": int,
}

info_rsp = {
    "type": "info_rsp",
    "movie_id": int, # 1 ~ 9 중 항상 선택
    "index_url": str,
}

dns_rqst = {
    "type": "dns_rqst",
    "url": str,
    "txid": int, # 보안 모듈에서 사용하기 위해 미리 추가
}

dns_rsp = {
    "type": "dns_rsp",
    "url_echo": str, # 질의 echo(식별 위해 클라이언트 질의 그대로 돌려줌)
    "txid": int,
    "answer": str | dict, # str(abCDN URL) 또는 dict(manifest)
}

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

def pack(msg: dict) -> bytes:
    return json.dumps(msg).encode("utf-8")

def unpack(data: bytes) -> dict:
    return json.loads(data.decode("utf-8"))

def create_txid() -> int:
    return secrets.randbits(16)