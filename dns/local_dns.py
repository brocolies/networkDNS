"""
클라이언트에게 rqst 수신 

보안모듈로 올린 txid 주의 
txid: 16-bit 무작위 ID: query와 resp 매칭
송신자: query마다 새로 생성하고 수신자는 응답에 그대로 echo해서 전송
수신자: 전송한 txid 저장하고 응답이 오면 비교

< 구현 필요 기능 >
1. 클라이언트로부터 UDP 패킷 수신/파싱
2. type 필터링 -> dns_rqst
3. url -> manifest dict 매핑

"""

import socket
from core.protocol import pack, unpack, create_txid
from core.log_utils import get_logger
from core.config_utils import parse_config
from security.defense import query_upstream

def main():
    defense_txid = True
    defense_spr = False
    defense_0x20 = False

    config = parse_config()
    local_addr = config["local_dns_server"]
    netplus_addr = config["netplus_dns_server"]
    abcdn_addr = config["abcdn_dns_server"]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(local_addr)

    log = get_logger("local_dns")
    log.info(f"local_dns_server: {local_addr} ON")

    while True:
        # 클라이언트로부터 UDP 패킷 수신 
        payload, client_addr = sock.recvfrom(4096)
        client_msg = unpack(payload)

        # dns_rqst 공격 대비 
        if client_msg.get("type") != "dns_rqst":
            continue

        # 클라이언트에게 응답할 때 url_echo, txid에 넣어서 보내야 함
        client_url = client_msg["url"]
        client_txid = client_msg["txid"]


        # netplus 서버에 요청 전송
        netplus_txid = create_txid()
        send_to_netplus_dns = {
            "type": "dns_rqst",
            "url": client_url,
            "txid": netplus_txid,
        }
        # netplus 응답 수신 + txid 검증 + spr
        netplus_response = query_upstream(netplus_addr, send_to_netplus_dns, netplus_txid, log, defense_txid, defense_spr, defense_0x20, sock)
        abcdn_url = netplus_response["answer"]

        # abCDN 서버에 요청 전송
        abcdn_txid = create_txid()
        send_to_abcdn_dns = {
            "type": "dns_rqst",
            "url": abcdn_url,
            "txid": abcdn_txid,
        }

        # abCDN 응답 수신 + txid 검증 + spr
        abcdn_response = query_upstream(abcdn_addr, send_to_abcdn_dns, abcdn_txid, log, defense_txid, defense_spr, defense_0x20, sock)
        # 클라이언트에게 응답할 manifest file 추출
        mainfest_file = abcdn_response["answer"]

        # 클라이언트에 응답 전송
        response_to_client = {
            "type": "dns_rsp",
            "url_echo": client_url,
            "txid_echo": client_txid,
            "answer": mainfest_file,
        }
        sock.sendto(pack(response_to_client), client_addr)

if __name__ == "__main__":
    main()
