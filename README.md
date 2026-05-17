# 네트워크 프로그래밍 프로젝트

CDN 기반 OTT 스트리밍 시뮬레이터. 6개 노드가 localhost UDP로 통신하며, DNS 보안 공격/방어 모듈을 포함한다.

각 항목은 한 번의 커밋 단위로 설계됐다. 끝낸 항목은 `[ ]`를 `[x]`로 바꾸고 그 줄 끝에 커밋 해시를 적어 작업 흐름을 기록한다.

---

## 폴더 구조

```
network/
├── core/                            ← 가장 먼저 짤 라이브러리 (8개 노드의 공통 언어)
│   ├── protocol.py                  메시지 6종 dict + pack/unpack
│   ├── time_utils.py                HH:MM:SS:ms 포맷
│   ├── log_utils.py                 노드별 로거
│   └── config_utils.py              config.txt 파싱
│
├── dns/                             Phase 2
│   ├── netplus_dns.py     :50002    URL → abCDN URL lookup (leaf)
│   ├── abcdn_dns.py       :50003    URL → manifest dict lookup (leaf)
│   └── local_dns.py       :50000    orchestrator (재귀↔반복)
│
├── server/                          Phase 3
│   ├── net_plus_web.py    :50001    영상번호 → 인덱스 URL
│   └── abcdn_streaming.py :50005    청크 전송 + 인공 지연
│
├── client/                          Phase 4 — 가장 복잡
│   ├── client.py          :50000    메인 + 3 스레드 (수신·재생·probe)
│   ├── buffer.py                    BufferEstimator (R_buffer)
│   ├── encoding_switch.py           case (i)/(ii) + β/γ 결정
│   └── gui.py                       (Phase 5) tkinter 최소 시각화 — 명세 "가능하면" 선택
│
├── security/                        Phase 6 (보너스 — 자소서·기술서 약속)
│   ├── attacker.py        :50099    위조 응답 송신
│   ├── fake_streaming.py  :50098    가짜 CDN
│   └── txid_defense.py              local_dns 패치
│
├── data/
│   ├── content_metadata.json        9 영상 × 3 인코딩 × 청크
│   └── gen_chunks.py                생성 스크립트
│
├── tests/                           단위·통합 검증 스크립트
│   ├── test_core.py                 Phase 1 공통 모듈 라운드트립
│   ├── test_netplus_dns.py          Net+ DNS 단독 검증
│   └── test_*.py                    노드별 추가
│
├── config.txt                       포트 정의 (위 포트는 예시)
├── run.sh                           6개 노드 일괄 실행
├── logs/                            노드별 로그
└── README.md
```

**노드 = 같은 컴퓨터의 별개 Python 프로세스**. `127.0.0.1`의 서로 다른 포트로 UDP datagram을 던져 통신. 포트 번호만 `config.txt`에서 합의되면 6대 노트북에 흩뿌려도 동일 코드로 작동.

---

## 통신 흐름

한 사이클 = 10단계 메시지 교환.

```
① 클라이언트  → Net+ Web        영상 N 요청
② Net+ Web    → 클라이언트      인덱스 URL
③ 클라이언트  → Local DNS       DNS query (인덱스 도메인)
④ Local DNS   → Net+ DNS        query
⑤ Net+ DNS    → Local DNS       abCDN 주소
⑥ Local DNS   → abCDN DNS       query                   ← 공격자 침투 지점
⑦ abCDN DNS   → Local DNS       manifest
⑧ Local DNS   → 클라이언트      manifest
⑨ 클라이언트  → abCDN Stream    chunk 요청
⑩ abCDN Stream → 클라이언트     chunk 응답              ← 반복 + 적응형 등급 전환
```

**①~②**: 영상 인덱스 URL 발급 — Net+ Web 단순 응답.
**③~⑧**: DNS 체인 — 인덱스 도메인을 manifest까지 풀어내는 과정. Local DNS는 클라이언트에 대해선 재귀(recursive), 상위 DNS에 대해선 반복(iterative) 질의.
**⑨~⑩**: 청크 스트리밍 — 반복하면서 클라이언트가 R_buffer 측정 + 인코딩 동적 전환.

### 보안 모듈 침투 지점

⑥과 ⑦ 사이. 공격자가 위조 `manifest` 응답을 ⑦보다 빠르게 Local DNS에 도착시키면 캐시 오염 → 클라이언트가 가짜 스트리밍 서버로 유도 (Kaminsky 류 cache poisoning). 방어는 random 16-bit txid 매칭으로 위조 응답 drop. **txid는 식별, DNSSEC는 인증** — 같은 16-bit인데 본질이 다른 이유가 면접 어필 포인트.

---

## 진행 흐름

### Part 1. 공통 기반  ✅ 완료

**목표**: 모든 노드가 공유할 메시지 포맷·시간 표기·로거를 먼저 정의한다. 코드 한 줄 짜기 전에 "두 노드가 무엇을 주고받을지"부터 합의해야 송신·수신 양쪽을 짤 수 있다.

**핵심 감각**: UDP는 패킷 단위라서 한 패킷 = 한 메시지로 설계해야 한다. 메시지는 `dict → JSON 문자열 → UTF-8 바이트`로 직렬화한다.

- [x] `core/protocol.py` — 메시지 6종 (`info_rqst`/`rsp`, `dns_rqst`/`rsp`, `chunk_rqst`/`rsp`) + `pack`/`unpack` + `HQ`/`MQ`/`LQ` 상수
- [x] `core/time_utils.py` — `now_time()`, `time_to_ms()`, `elapsed_time()`
- [x] `core/log_utils.py` — `get_logger(node_name)` — 콘솔 + `logs/{node}.log` 동시 기록
- [x] `core/config_utils.py` — `parse_config()` config.txt → `{key: (ip, port)}` dict
- [x] **검증**: `tests/test_core.py` — 6종 메시지 라운드트립 통과

---

### Part 2. DNS 계층  🟡 진행 중

**목표**: 클라이언트가 URL로 manifest를 받아내는 전 과정 구현. 명세 3.2, 3.3.2, 3.3.3.

**핵심 감각**: Local DNS는 클라이언트에 대해서는 재귀(recursive), 상위 DNS에 대해서는 반복(iterative) 질의를 수행한다. leaf 두 개(Net+/abCDN DNS)는 단순 lookup, Local DNS만 orchestrator.

- [🟡] `dns/netplus_dns.py` — 인덱스 URL → abCDN URL 응답 (작업 중)
- [ ] `dns/abcdn_dns.py` — abCDN URL → manifest dict (HQ/MQ/LQ 서버 IP) 응답
- [ ] `dns/local_dns.py` — 클라 query 받아 Net+/abCDN DNS 순차 forward 후 manifest 클라에 응답
- [ ] (선택) DNS 캐시 — TTL 60s. Phase 2엔 스킵, 시간 남으면 추가
- [ ] **검증**: `tests/test_netplus_dns.py`, `test_abcdn_dns.py`, `test_local_dns.py` 각 단독 + 통합 시 클라 → manifest 한 사이클 성공

---

### Part 3. 서버 계층

**목표**: 컨텐츠 메타데이터와 청크가 실제로 흘러나오게 한다. 명세 2.3 ~ 2.4, 2.6, 2.12 ~ 2.13.

**핵심 감각**: 서버는 무한 루프로 `recvfrom`을 돌면서 들어온 요청을 분기 처리한다. 청크는 임의 바이트 페이로드(예: `b"\x00" * 1024`)로 시뮬레이션해도 충분하다 — 명세에 실제 영상 데이터는 요구되지 않음.

- [ ] `data/content_metadata.json` — 컨텐츠 2~3개, 각각 인코딩 레벨별 청크 리스트와 청크 크기 명시
- [ ] `server/net_plus_web.py` — `metadata_request` 수신 → JSON에서 해당 컨텐츠 메타데이터 응답
- [ ] `server/abcdn_stream.py` — `chunk_request` 수신 → 지정 크기 청크 전송, 약간의 지연(`random.uniform`) 시뮬레이션
- [ ] **검증**: 임시 클라이언트 스크립트로 메타데이터 조회 → 청크 1개 받기까지 한 사이클 성공, 로그에 송수신 시각 기록

---

### Part 4. 클라이언트 핵심 로직

**목표**: 이 프로젝트의 알고리즘적 본질. 명세 2.1, 2.7, 2.16 ~ 2.18.

**핵심 감각**: R_buffer는 측정값(`R_chunk`)과 누적값을 α로 가중평균한 값이다. 인코딩 전환은 `R_buffer / R_current` 비율이 β 이상이면 상승, γ 이하면 하강 — hysteresis로 진동을 막는다. case (i)/(ii)는 다음 청크가 목표 시각 t_S* 안에 도착 가능한지에 따라 분기한다.

- [ ] `client/client.py` — 사용자 입력(컨텐츠명, 시작 시각) 수신
- [ ] `client/client.py` — DNS 질의 → 메타데이터 요청 → 청크 요청 메인 루프
- [ ] `client/buffer.py` — `BufferEstimator` 클래스, `R_buffer = α·R_chunk + (1-α)·R_buffer_prev`
- [ ] `client/encoding_switch.py` — case (i)/(ii) 판정 + t_S* 매칭
- [ ] `client/encoding_switch.py` — β/γ 임계 기반 인코딩 레벨 결정
- [ ] 버퍼 모니터링·종료 처리 (명세 2.7)
- [ ] **검증**: 한 컨텐츠를 끝까지 받아내면서 R_buffer 값이 로그에 찍히고, 네트워크 지연을 강제로 늘렸을 때 인코딩이 한 단계 내려가는 게 관찰됨

---

### Part 5. 통합과 운영

**목표**: 단일 노드 시연에서 시스템 시연으로. 명세 2.14 ~ 2.15.

**핵심 감각**: 각 노드는 독립 프로세스로 띄운다. 노드 내에서 다중 요청 처리는 `threading.Thread(daemon=True)`로 분산. 로그 포맷이 노드별로 다르면 디버깅이 지옥이 되므로 통일한다.

- [ ] 서버 측 threading — 동시에 여러 클라이언트 요청 처리
- [ ] `run.sh` — 6개 노드를 백그라운드로 띄우고 `trap`으로 일괄 종료
- [ ] 로그 포맷 통일: `[HH:MM:SS:ms] [node_name] [event_type] details`
- [ ] **검증**: 명세 2.1 ~ 2.18 모든 항목 수동 점검, 동시 클라이언트 2개로 충돌 없는지 확인

---

### Part 6. 보안 모듈

**목표**: 자기소개서·계획서에서 약속한 부분. 면접의 핵심 어필 포인트.

**핵심 감각**: Kaminsky 공격의 본질은 "UDP는 무연결 + DNS txid가 16-bit밖에 안 되니까 위조 응답을 합법 응답보다 먼저 도착시키면 캐시 오염 가능"이다. txid 검증은 합리적인 첫 방어선이지만, 충분히 빠른 위조 시도 앞에서는 뚫린다 — 그래서 DNSSEC가 서명 기반 인증으로 본질적 해결을 시도한다.

- [ ] `security/attacker.py` — Local DNS 응답 포트로 위조 `dns_response` 송신 (합법 응답보다 먼저 도착시키기)
- [ ] 공격 시연: 클라이언트가 악성 IP로 유도되는 시나리오 로그 캡처
- [ ] `security/txid_defense.py` — Local DNS에 txid 매칭 검증 추가, 불일치 응답 drop
- [ ] 방어 시연: 동일 공격이 차단되는 시나리오 로그 캡처
- [ ] 공격 성공률 측정 — 방어 전/후 N회 시행, 비율 기록
- [ ] DNSSEC 본질 정리 — `security/README.md`에 "왜 txid만으로 부족하고 서명이 필요한가" 정리
- [ ] **검증**: 공격/방어 두 시나리오가 같은 `run.sh`에서 토글로 실행 가능, 로그에 결과가 명확히 드러남

---

### Part 7. 마감

**목표**: 5/24 개인 데드라인 → 6/01 학교 제출 → 6/02 면접 시연까지의 최종 정돈.

- [ ] README 최종 정리 (구현 결정·trade-off 추가 기록)
- [ ] 코드 주석 정돈, 죽은 코드 제거
- [ ] 10분 데모 시나리오 스크립트 작성
- [ ] 데모 리허설 1회
- [ ] 시연 영상 녹화 (면접 백업용)
- [ ] 명세 2.1 ~ 2.18 체크리스트 최종 전수 확인
- [ ] `git tag v1.0-final`

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
| Phase 1 (공통 기반) | ✅ 5/14 완료 |
| Phase 2 (DNS 체인) | 🟡 5/15~17 진행 중 |
| 화이트햇 필기시험 | 5/23 (토) |
| 개인 데드라인 (본 시스템 완성) | 5/24 (일) |
| 보안 모듈 완성 | 5/27 (수) |
| 화이트햇 면접 | 5/30 (토) |
| 학교 공식 제출 | 6/01 (월) 13:00 |
| 학교 면접 | 6/02 (화) |

---

## 실행

```bash
./run.sh
```

---

## 커밋 컨벤션

작업 단위가 작아 매일 여러 커밋이 가능하다. 메시지는 짧고 동사로 시작.

```
feat(common): define dns_query/response messages
feat(dns): local_dns iterative resolution
feat(client): R_buffer weighted moving average
feat(security): kaminsky-style cache poisoning attacker
fix(dns): cache TTL expiry off-by-one
docs: update README part 4 completion
```

각 체크박스 항목 하나가 대략 한 커밋에 대응. 끝낸 줄은 `[x]` + 커밋 해시 7자리 추가:

```
- [x] `common/protocol.py` — dns_query/response 정의 (a1b2c3d)
```