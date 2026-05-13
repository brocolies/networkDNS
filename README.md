# 네트워크 프로그래밍 프로젝트

CDN 기반 OTT 스트리밍 시뮬레이터. 6개 노드가 localhost UDP로 통신하며, DNS 보안 공격/방어 모듈을 포함한다.

---

## 폴더 구조

```
network/
├── client/      클라이언트 — 스트리밍 수신·인코딩 전환
├── dns/         3종 DNS 서버 — Local, Net+, abCDN
├── server/      Net+ Web Server, abCDN Streaming Server
├── security/    DNS 공격·방어 모듈
├── common/      프로토콜, 시간, 로거 공통 모듈
├── data/        컨텐츠 메타데이터
├── logs/        실행 로그
└── run.sh       전체 노드 일괄 실행
```

---

## 진행 흐름

### Part 1. 공통 기반

코드를 짜기 전에 모든 노드가 공유할 토대를 먼저 깐다.

- `common/protocol.py` — 메시지 종류 정의 (dns_query/response, metadata_request/response, chunk_request/response)
- `common/time_utils.py` — `HH:MM:SS:ms` 포맷
- `common/logger.py` — 노드별 통합 로깅
- 라운드트립 직렬화 검증

### Part 2. DNS 계층

명세 2.2, 2.5, 2.8 ~ 2.11. iterative resolution이 핵심.

- `dns/local_dns.py` — 클라이언트 진입점, 상위 DNS에 반복 질의
- `dns/net_plus_dns.py` — Net+ Web Server IP 응답
- `dns/abcdn_dns.py` — 부하·가중치 기반 스트리밍 서버 선택
- DNS 응답 캐시 + TTL 만료
- 체인 통과 end-to-end 검증

### Part 3. 서버 계층

명세 2.3 ~ 2.4, 2.6, 2.12 ~ 2.13. 컨텐츠 메타데이터와 청크가 실제로 흐르게 한다.

- `server/net_plus_web.py` — 컨텐츠 정보 응답
- `server/abcdn_stream.py` — 청크 단위 전송
- `data/content_metadata.json` — 컨텐츠 카탈로그
- 단일 클라이언트 메타 → 청크 흐름 검증

### Part 4. 클라이언트 핵심 로직

명세 2.1, 2.7, 2.16 ~ 2.18. 이 프로젝트의 알고리즘적 본질이 여기 있다.

- `client/client.py` — 메인 루프 (DNS 질의 → 메타 → 청크 요청)
- `client/buffer.py` — R_buffer 가중이동평균 (α = 0.5)
- `client/encoding_switch.py` — case (i)/(ii) + t_S* 매칭
- 한 컨텐츠 끝까지 스트리밍, 인코딩 전환 시연 가능

### Part 5. 통합과 운영

명세 2.14 ~ 2.15. 단일 노드 동작에서 시스템으로.

- threading 적용, 다중 클라이언트 처리
- 노드별 로그 통합 포맷
- `run.sh` — 6개 노드 일괄 실행
- 명세 2.1 ~ 2.18 전수 점검

### Part 6. 보안 모듈

자기소개서·계획서에서 약속한 부분. 면접의 핵심 어필 포인트.

- `security/attacker.py` — Kaminsky 류 cache poisoning 재현
- `security/txid_defense.py` — transaction ID 검증 방어
- 공격 성공률 before / after 측정
- DNSSEC가 해결하려는 본질(서명 기반 인증의 필연성)을 코드 수준에서 실증

### Part 7. 마감

- README 최종 정리, 코드 주석 정돈
- 10분 데모 시나리오 리허설
- 시연 영상 녹화 (면접 대비)
- 명세 체크리스트 전수 검증

---

## 파라미터

| 이름 | 값 | 비고 |
|---|---|---|
| chunk size | 1 KB | 명세 |
| buffer size `k` | 10 chunks | 명세 |
| α | 0.5 | R_buffer 가중치 |
| β | 0.8 | 인코딩 상승 임계 |
| γ | 0.3 | 인코딩 하강 임계 |
| TTL | 60 s | DNS 캐시 |

---

## 통신 규칙

- 모든 노드는 localhost UDP, 포트 번호로 식별
- 메시지는 `dict → JSON 문자열 → UTF-8 바이트` 순으로 직렬화
- 한 패킷 = 한 메시지

---

## 일정

| 구분 | 일자 |
|---|---|
| 개인 데드라인 | 5/24 (일) |
| 학교 공식 제출 | 6/01 (월) 13:00 |
| 면접 | 6/02 (화) |

---

## 실행

```bash
./run.sh
```