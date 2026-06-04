# CDN OTT 스트리밍 시뮬레이터

CDN 기반 영상 스트리밍의 DNS 해석과 적응적 화질 전환, 그리고 DNS 캐시 포이즈닝 공격과 다층 방어를 localhost UDP 위에서 동작하도록 구현한 컴퓨터네트워크프로그래밍 과제.

## 실행

```bash
python -m run_program
```

7개 노드(클라이언트 + DNS 3개 + Net+ 웹 + 스트리밍 3개)가 자동으로 기동되고, 영화 번호(1~9) 입력 프롬프트가 뜬다. 9번 영화는 중간 구간에 네트워크 혼잡이 삽입되어 있어 화질 다운/업시프트 동작을 확인할 수 있다.

공격 시연:

```bash
python -m security.attacker
```

`dns/local_dns.py`의 방어 플래그(txid / SPR / 0x20)를 켜고 끄면서 공격 성공률 변화를 비교할 수 있다.

## 구조

```
core/        프로토콜 직렬화, txid 생성, 로깅, config 파싱
dns/         로컬 DNS, Net+ DNS, abCDN DNS
server/      Net+ 웹 서버, 스트리밍 서버 (HQ/MQ/LQ)
client/      클라이언트 (수신 스레드 + 재생 스레드)
security/    방어 모듈, 공격 모듈
data/        영화 청크 생성
config.txt   노드 주소
run_program  전체 노드 부팅
```

## 주요 동작

반복적 DNS 해석으로 영화 manifest를 받아오고, 클라이언트가 버퍼 상태를 평활화한 값(R_buffer)을 기준으로 화질을 동적으로 전환한다. 공격자가 가짜 응답을 burst로 쏘아 캐시를 오염시키려 할 때, txid 검증·SPR·0x20 인코딩 세 계층의 누적 엔트로피로 막아낸다.
