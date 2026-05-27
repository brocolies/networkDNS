# 네트워크 프로그래밍 프로젝트

CDN 기반 OTT 스트리밍 시뮬레이터. 6종 노드가 localhost UDP로 통신하며, DNS 보안 공격/방어 모듈을 포함한다.

각 항목은 한 번의 커밋 단위로 설계됐다. 끝낸 항목은 `[ ]`를 `[x]`로 바꿔 작업 흐름을 기록한다.

---

## 폴더 구조

```
network/
├── core/                            공통 라이브러리 (모든 노드의 공통 언어)
│   ├── protocol.py                  메시지 6종 dict + pack/unpack + create_txid
│   ├── time_utils.py                HH:MM:SS:ms 포맷 (now_time / time_to_ms / elapsed_time)
│   ├── log_utils.py                 노드별 로거
│   └── config_utils.py              config.txt 파싱
│
├── dns/                             Phase 2 ✅
│   ├── netplus_dns.py    :50002     인덱스 URL → abCDN URL lookup (leaf)
│   ├── abcdn_dns.py      :50003     abCDN URL → manifest dict lookup (leaf)
│   └── local_dns.py      :50000     orchestrator (재귀↔반복)
│
├── server/                          Phase 3 ✅
│   ├── netplus_web.py    :50001     영상번호 → 인덱스 URL
│   └── streaming.py      :50010-2   청크 push 전송 + 랜덤 지연 (HQ/MQ/LQ 3 인스턴스)
│
├── client/                          Phase 4 🟡 진행 중 — 가장 복잡
│   └── client.py                    메인 1파일: 셋업 + 받기/재생 스레드 + probe·R + ABR 전환
│
├── security/                        Phase 6 (보너스 — 자소서·기술서 약속)
│   ├── attacker.py                  Kaminsky 류 위조 dns_rsp burst
│   └── measure.py                   layer별 공격 성공률 측정
│   (방어 Layer 1·1.5·2는 local_dns.py에 붙고, Layer 3 DNSSEC은 별도 stub)
│
├── data/
│   ├── create_chunks.py             9 영상 × 3 인코딩 청크 메타 생성기
│   └── chunks.json                  생성 결과 (HQ 45 / MQ 30 / LQ 15 청크)
│
├── tests/                           단위·통합 검증 스크립트
│   ├── test_core.py                 Phase 1 공통 모듈 라운드트립
│   ├── test_netplus_dns.py          Net+ DNS 단독
│   ├── test_abcdn_dns.py            abCDN DNS 단독
│   ├── test_local_dns.py            DNS 체인 통합 ⭐
│   ├── test_netplus_web.py          Net+ Web 단독
│   └── test_streaming.py            streaming push 청크 순서 검증
│
├── config.txt                       4 노드 주소 (local_dns / netplus_web / netplus_dns / abcdn_dns)
├── run_all.py                       (Phase 5) 8 프로세스 일괄 실행 러너
├── logs/                            노드별 로그
└── README.md
```

**노드 = 같은 컴퓨터의 별개 Python 프로세스.** `127.0.0.1`의 서로 다른 포트로 UDP datagram을 던져 통신. 스트리밍 서버 포트(50010-2)는 config.txt가 아니라 manifest로 전달된다 (명세는 config 4줄만 허용).

---

## 통신 흐름

한 사이클 = 10단계 메시지 교환.

```
(1) 클라이언트   → Net+ Web        영상 N 요청 (info_rqst)
(2) Net+ Web     → 클라이언트      인덱스 URL (info_rsp)
(3) 클라이언트   → Local DNS       DNS query (dns_rqst, txid 포함)
(4) Local DNS    → Net+ DNS        query
(5) Net+ DNS     → Local DNS       abCDN URL                ← 위조 응답 침투 지점
(6) Local DNS    → abCDN DNS       query
(7) abCDN DNS    → Local DNS       manifest
(8) Local DNS    → 클라이언트      manifest (dns_rsp)
(9) 클라이언트   → abCDN Stream    chunk_rqst
(10) abCDN Stream → 클라이언트     chunk_rsp (push, 연속 전송) ← 적응형 등급 전환
```

**(1)~(2)**: 영상 인덱스 URL 발급 — Net+ Web 단순 응답.
**(3)~(8)**: DNS 체인 — 인덱스 도메인을 manifest까지 풀어내는 과정. Local DNS는 클라에 대해선 재귀(recursive), 상위 DNS에 대해선 반복(iterative) 질의.
**(9)~(10)**: 청크 스트리밍 — 서버가 push로 연속 전송(전송 사이 랜덤 지연), 클라가 buffer 측정 + 인코딩 동적 전환. 전환 시 클라가 t_N(last_watched_time) 실어 새 화질 서버에 재요청, 서버는 t_N으로 시작 청크 찾음.

### 보안 모듈 — 다층 방어 thesis

**자소서 thesis**: DNS는 구조적으로 인증 부재인데 우리가 안전한 이유는 **여러 방어층이 서로 약점을 메우는 구조**. 이를 코드로 입증.

침투 지점은 Local DNS가 받는 응답(5/7). 공격자가 위조 응답을 합법 응답보다 빠르게 Local DNS에 도착시키면 캐시 오염 → 클라가 가짜 스트리밍 서버로 유도 (Kaminsky 류 cache poisoning).

**다층 방어 — off-path 엔트로피 계열 + in-path 암호 계열**:
- Layer 1 — txid 매칭 (16-bit, secrets로 CSPRNG 생성). 모든 방어의 토대.
- Layer 1.5 — 0x20 encoding (질의 대소문자 랜덤화, 알파벳 수만큼 엔트로피). 거의 공짜.
- Layer 2 — SPR (Source Port Randomization, ~32-bit로 확장). 카민스키 burst 차단.
- Layer 3 (시간 되면) — DNSSEC stub (RSA 서명 인증). in-path까지 막는 본질적 해결.

핵심: txid·0x20·SPR은 off-path 추측을 곱셈으로 어렵게 하지만 in-path엔 무력 → DNSSEC가 그 구멍을 메움. 각 층 추가 시 공격 성공률 정량 측정. 상세 설계는 통합 자료실 "DNS 다층 방어" 페이지.

---

## 진행 흐름

### Part 1. 공통 기반  ✅ 완료

모든 노드가 공유할 메시지 포맷·시간 표기·로거를 먼저 정의. UDP는 패킷 단위라 한 패킷 = 한 메시지, `dict → JSON 문자열 → UTF-8 바이트`로 직렬화.

- [x] `core/protocol.py` — 메시지 6종 + `pack`/`unpack` + `HQ`/`MQ`/`LQ` 상수 + `create_txid`
- [x] `core/time_utils.py` — `now_time()`, `time_to_ms()`, `elapsed_time()`
- [x] `core/log_utils.py` — `get_logger(node_name)` — 콘솔 + `logs/{node}.log`
- [x] `core/config_utils.py` — `parse_config()` config.txt → `{key: (ip, port)}`
- [x] **검증**: `tests/test_core.py` — 6종 메시지 라운드트립 통과

### Part 2. DNS 계층  ✅ 완료

클라가 URL로 manifest를 받아내는 전 과정. 명세 3.2, 3.3.2, 3.3.3. Local DNS는 클라에 재귀, 상위 DNS에 반복 질의. leaf 둘은 단순 lookup, Local DNS만 orchestrator.

- [x] `dns/netplus_dns.py` — 인덱스 URL → abCDN URL + 단위 테스트
- [x] `dns/abcdn_dns.py` — abCDN URL → manifest dict + 단위 테스트
- [x] `dns/local_dns.py` — 클라 query 받아 Net+/abCDN DNS 순차 forward 후 manifest 응답
- [x] `core/protocol.py`에 `create_txid()` 추가 (16-bit 무작위 ID)
- [x] **통합 검증** — `tests/test_local_dns.py`: 한 사이클 통과 ⭐

### Part 3. 서버 계층  ✅ 완료

컨텐츠 메타와 청크가 실제로 흘러나오게. 명세 3.3.1, 3.3.4. 서버는 무한 루프 `recvfrom` + 분기. streaming은 명세 "연속적으로 전송"대로 push.

- [x] `data/create_chunks.py` + `chunks.json` — 9 영상 × 3 인코딩(HQ 45/MQ 30/LQ 15) 청크 메타
- [x] `server/netplus_web.py` — `info_rqst` → 인덱스 URL 응답 + 단위 테스트
- [x] `server/streaming.py` — 화질별 별도 서버(CLI 인자), `chunk_rqst` 받으면 t_N부터 끝까지 push, 전송 사이 랜덤 지연
- [x] streaming의 `cal_start_index` — t_N(시각)으로 시작 청크 매칭 (명세 3.3.4)
- [x] **검증** — `tests/test_streaming.py`: 청크 0~44 순서대로 도착 통과

### Part 4. 클라이언트 핵심 로직  🟡 진행 중

이 프로젝트의 알고리즘적 본질. 명세 2절, 3.1. **단일 파일 `client.py`** (과분리 안 함). push 스트림을 받으며 동시에 재생·판단 → 스레드 2개(받기/재생).

- [x] Step 1 — 셋업: 영화 선택 → `info_rqst` → 인덱스 URL → `dns_rqst` → manifest 수신
- [x] Step 2 — 받기 스레드: `recvfrom` → 현재 화질 청크만 buffer 적재 (queue.Queue)
- [x] Step 3 — 재생 스레드: buffer 일정 수준 차면 시작, 청크 start~end 길이만큼 소비
- [x] Step 4 — probe + R: `R_buffer = α·R_prev + (1−α)·fullness`, fullness = 남은 청크 수 / n (play가 상태 들고 인자로 전달)
- [ ] Step 5 — 전환 판단 + case(i)/(ii): R≥β 상향 / γ≤R<β 유지 / R<γ 하향, t_N 실어 새 서버 요청 (select_encoding 결정부 미구현)
- [ ] Step 5 — 전환 로그 (명세 4절 Fail 조항): α/β/γ + 현재→목표 encoding + 최신 R
- [ ] Step 6 — 스레드 묶기: 셋업 → 받기·재생 동시 시작 (main 와이어링 남음)
- [ ] **검증**: 6노드 띄우고 지연 조절로 HQ↔MQ↔LQ 전환 관찰

### Part 5. 통합과 운영  ⬜

단일 노드 시연에서 시스템 시연으로. 각 노드 독립 프로세스. 로그 포맷 통일.

- [ ] `run_all.py` — 8 프로세스(DNS 3 + Web + streaming 3 + client) 순서대로 띄우고 일괄 종료
- [ ] (선택) `client/gui.py` — tkinter 최소 시각화 (명세 "가능하면" 조건부)
- [ ] **검증**: 명세 전 항목 수동 점검, end-to-end 한 영상 재생 + 전환 관찰

### Part 6. 보안 모듈 — 다층 방어 입증  ⬜

자소서 thesis를 코드로 입증. 면접 핵심. Kaminsky = "UDP 무연결 + 16-bit txid + race"의 합, 단일 방어로 못 막음.

- [ ] `security/attacker.py` — Local DNS에 위조 `dns_rsp` burst (합법보다 먼저 도착)
- [ ] 공격 시연: 클라가 악성 서버로 유도되는 시나리오 로그 캡처
- [ ] **Layer 1** — txid 매칭 검증 (`create_txid`를 `secrets`로) + 성공률 측정
- [ ] **Layer 1.5** — 0x20 encoding (질의 케이스 랜덤화 + echo 검증)
- [ ] **Layer 2** — SPR: local_dns upstream forward를 매번 ephemeral 포트로
- [ ] (선택) **Layer 3** — DNSSEC stub: RSA 키쌍 + 서명 + 검증 (`cryptography`)
- [ ] 실험 — random vs secrets / SPR off-on / DNSSEC off-on 성공률 표 (`measure.py`)
- [ ] **Wireshark** — lo0 캡처로 위조 burst vs 정상 응답 타임라인 시연 (면접 결정타)

### Part 7. 마감  ⬜

- [ ] 설계보고서 A4 4장 (구조·알고리즘·trade-off)
- [ ] 소스코드 PDF 출력본 (11pt 이상) + zip/github
- [ ] 10분 데모 시나리오 + 리허설
- [ ] 명세 전 항목 최종 전수 확인

---

## 파라미터

명세 3.1: 데모 10분 내 시연되고 ABR 전환이 관찰되도록 상호 조율하여 결정. 아래는 Phase 4 버퍼 동역학 모의로 확정한 값.

| 이름 | 값 | 비고 |
|---|---|---|
| 영상 길이 | 2분 | 명세 기준 |
| 청크 수 | HQ 45 / MQ 30 / LQ 15 | 명세 권장 |
| 버퍼 크기 n | 10 | 청크 단위 (확정) |
| α | 0.5 | R_buffer 가중치(이전값 비중). 명세 예시 0.8보다 작게 → LQ 복귀 적시화 |
| β | 0.8 | 인코딩 상향 임계 |
| γ | 0.4 | 인코딩 하향 임계 (0 ＜ γ ＜ β ＜ 1) |
| initial_size | n의 0.3 | 재생 시작 전 채울 양 |
| probe 주기 | 청크당 | 청크 하나 재생마다 1회 probe |
| 워밍업 | 첫 5 probe | R_buffer 초기 0이라 그동안 판단 보류 |
| 전송 지연(정상) | 0.1~0.4초 | streaming 청크 사이 랜덤 |
| 전송 지연(혼잡) | 5~7초 | 영상 [15s, 80s] 구간 청크 (영상시각 기준) |

청크 크기·DNS 캐시 TTL은 명세 미요구 → 미사용 (probe는 청크 개수 기반). 재생은 정속(실시간) — 배속 변수 없음, 2분이라 10분 데모에 충분. 혼잡은 청크 *번호*가 아니라 *영상 시각*으로 키잉 (화질별 청크 수가 달라 공통 축 필요).

> ※ 코드 동기화 메모: 현재 `client.py`의 `alpha` 기본값이 0.8로 남아 있음 — 위 확정값 **0.5**로 한 줄 수정 필요.

---

## 통신 규칙

- 모든 노드는 localhost UDP, 포트 번호로 식별
- 메시지는 `dict → JSON 문자열 → UTF-8 바이트` 순 직렬화, 한 패킷 = 한 메시지
- 각 노드는 수신 메시지를 화면에 출력 (명세 4절)

---

## 일정

| 구분 | 일자 |
|---|---|
| Phase 1 (공통 기반) | ✅ 완료 |
| Phase 2 (DNS 체인) | ✅ 완료 ⭐ |
| Phase 3 (서버 계층) | ✅ 완료 |
| Phase 4 (클라이언트 + ABR) | 🟡 진행 중 |
| 화이트햇 필기시험 | 5/23 (토) |
| Phase 5 (통합 + GUI) | ⬜ |
| Phase 6 (보안 모듈) | ⬜ |
| 화이트햇 면접 | 5/30 (토) |
| 학교 공식 제출 | 6/01 (월) 13:00 |
| 학교 면접 | 6/02 (화) |

---

## 실행

```bash
# 개별 노드 (각각 별도 터미널)
python -m dns.netplus_dns
python -m dns.abcdn_dns
python -m dns.local_dns
python -m server.netplus_web
python -m server.streaming HQ
python -m server.streaming MQ
python -m server.streaming LQ
python -m client.client

# (Phase 5) 일괄 실행
python run_all.py
```

---

## 커밋 컨벤션

작업 단위가 작아 매일 여러 커밋. 메시지는 짧고 동사로 시작.

```
feat(core): define dns_rqst/rsp messages
feat(dns): local_dns iterative resolution
feat(server): streaming push with t_N start matching
feat(client): R weighted moving average + encoding switch
feat(security): kaminsky-style cache poisoning attacker
docs: update README part 4 progress
```
