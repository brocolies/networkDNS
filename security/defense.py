"""
security/defenses.py — DNS resolver의 보안 계층 모음

방어 함수가 여기에 모임:
- L1 txid_matching: 응답의 txid_echo가 내가 보낸 txid와 같은지 검증, 다르면 폐기
- L2 query_upstream (SPR): 업스트림 질의마다 새 ephemeral 포트로 송수신
- L1.5 0x20: (예정) 이름 대소문자 무작위화 + echo 검증

각 토글(defense_txid, defense_spr 등)은 호출자(local_dns)에서 인자로 넘긴다.
"""

import secrets
import socket
from core.protocol import pack, unpack


def txid_matching(sock, expected_txid, log, defense_txid=True, expected_url=None, defense_0x20=False):
    # defense_txid가 켜져 있으면 내가 보낸 txid와 응답의 txid_echo가 일치하는 것만 받아들이고
    # 나머지(위조 의심)는 버린 뒤 진짜가 올 때까지 계속 recvfrom
    # defense_0x20만 false -> expected_url 없을 때도 있기 때문
    while True:
        payload, _ = sock.recvfrom(4096)
        response = unpack(payload)
        response_txid_echo = response.get("txid_echo")
        response_url_echo = response.get("url_echo")

        # txid 검증
        if defense_txid and response_txid_echo != expected_txid:
            log.warning(f"TXID MISMATCH \n"
                        f"sent: {expected_txid} \n"
                        f"got : {response.get('txid_echo')}")
            continue

        # url, url_echo 대소문자 정확히 같은지 검증
        if defense_0x20 and response_url_echo != expected_url:
            log.warning(f"0x20 MISMATCH \n"
                        f"sent: {expected_url} \n"
                        f"got : {response.get('url_echo')}")
            continue

        return response


def query_upstream(addr, req, expected_txid, log, defense_txid, defense_spr, defense_0x20, client_sock):
    # 0x20 T/F
    if defense_0x20:
        req["url"] = random_upper_lower(req["url"])

    # SPR T/F
    if defense_spr:
        upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        upstream_sock.bind(("", 0))
    else:
        upstream_sock = client_sock
    upstream_sock.sendto(pack(req), addr)

    # txid_matching
    response = txid_matching(upstream_sock, expected_txid, log,
                             defense_txid, req["url"], defense_0x20)

    if defense_spr:
        upstream_sock.close()
    return response

# 0x20 구현 위해 대소문자 랜덤해서 반환
def random_upper_lower(url):
    randomized_url = ""
    for char in url:
        if secrets.randbits(1):
            randomized_url += char.upper()
        else:
            randomized_url += char.lower()
    return randomized_url
