# 요구사항과 검증 근거

대상은 [후보 지문](final-source/identity.json)의 소스다. 아래 CLI 근거는 테스트가 만든 독립 프로젝트, 실제 파일과 프로세스에서 관측한 결과다. 제품 모델에 원래 목적만 주어 얻은 성과는 별도 열에 둔다. `NOT_RUN`은 결측값이다. 정성적 인수 조건은 원래 계약의 의미를 따른다. [실행별 테스트 이름과 판정](final-source-tests.log) · [독립 개발 검사](development-audit/independent-audit.md)

## 기존 Gate와 요구사항

| Gate | 007ee7f | 이번 후보 인수 | 근거 및 남은 조건 |
|---|---|---|---|
| GT0 | PASS | PASS (기준 식별) | 공식 Git 객체와 보존된 395개 파일, 7개 공개 검토문 및 연결된 원본 해시 대조. 최종 평가 자원은 별도 |
| GT1 | PASS | HOLD | 양 호스트 역할 본문 동등성, CAP 계약, 정책 충돌 수정. 전체 계약 일관성의 독립 인수 보류 |
| GT2 | NOT_RUN | NOT_RUN | 원래 목적에서 적응 탐색과 작업자 배정을 일으키는 모델 연구 필요 |
| GT3 | PASS | HOLD | CLI 질문·관측·계보 재개, v1/v2·stale·공식 기록 적용성 회귀. 기존 원생성 v1 새 모델 세션까지 포함한 검증 필요 |
| GT4 | NOT_RUN | NOT_RUN | 실제 CLI 카운트·근거 파일·예산 경계 검사. 제품이 전수 조사와 후속 메타 연구를 수행하는 최종 세션 필요 |
| GT5 | NOT_RUN | NOT_RUN | 공개 기준과 통제된 오류 검사. 모델 Auditor의 독립 선고정·owner 재작업·재감사 필요 |
| GT6 | NOT_RUN | NOT_RUN | 신규 Q05-1에 맞춘 동일 프로젝트 내 조건부 전략 검색·적용/비적용 CLI 확인. 새 세션의 실제 전략 변경 필요 |
| GT7 | NOT_RUN | NOT_RUN (실행 차단) | 확정된 3개 분야 중 2개 이상에서 두 반복 모두 개선 필요. 0.28.0·0.28.1의 FAIL 보존 |
| GT8 | BLOCKED | BLOCKED | GT2·4·5·6·7 최종 제품 실행 근거 부재 |

| 요구 | 이전 주 Gate | 이번 책임·시나리오 | 이번 증거 및 한계 |
|---|---|---|---|
| R-01 기존 능력 | GT0 | AR01, MG0 | 원본 매니페스트·Git·이전 Gate 대조 |
| R-02 개방 관점 | GT1 | RI01, S01 | self-critical-workflow의 E01–E12 및 추가 관점 계약 보존 |
| R-03 계약 일관성 | GT1 | AR01, MG1 | CAP 표·양 호스트 역할 대응·정책 변경 이력 |
| R-04 적응 선택 | GT2 | RI01, S01 | 의존성과 예산에 따라 CLI가 ready 작업을 선별. 모델 선택 미실행 |
| R-05 다방향 재귀 | GT2 | RI01, RI03, S02 | 원인·해법 탐색 계약 유지. 새 revision의 자율 재귀 미실행 |
| R-06 작업자 발견 | GT2 | KI01, RI02, S04–05 | 실제 수치 출력을 proposal로 넘김. 모델의 미제시 문제 발견 미실행 |
| R-07 원인과 해법 | GT2/7 | RI03, RI06 | 경쟁 가설·Study 조건 비교. GT7 미실행 |
| R-08 의존 배정 | GT2 | AR05, S23/28/29 | coordinate claim 경쟁·전이적 무효화·간결 모드. 모델 dispatch 미실행 |
| R-09 연결 | GT3 | KI02/05, S03/04 | 소스 해시·질문·finding ID·재사용 조건·전달 영수증 |
| R-10 연속성 | GT3 | KI05/09, S10/11 | 독립 CLI 프로세스에서 동일 질문/기록/복구 조회 |
| R-11 노드 ID | GT3/4 | SI02, S10/18 | recovery rename/split/merge와 질문 ID 호환성 |
| R-12 유효 재요청 | GT4 | SI02, S18 | 중복 전송·설명·렌더·자동 rework 제외 |
| R-13 세 번째 즉시 전환 | GT4 | SI03, S18 | 3번째 CLI 이벤트가 exhaustive_now를 요구. 실제 제품 연구 미실행 |
| R-14 자율 부족 감지 | GT4 | SI01/KI08, S05/20 | 미반환/미처리/전달 누락, failed task 선별. 미발견 자체의 자율 탐지율 미확인 |
| R-15 실제 전수 | GT4 | SI03, S18 | verified-local 근거 모드 검사. 최종 제품 전수 미실행 |
| R-16 메타 진단 | GT4 | SI04, S19 | meta 전이·변경된 방법과 근거 검사. 실제 재연구 미실행 |
| R-17 무의미 반복 방지 | GT4 | SI01/02/GV07, S19/23 | idempotency, attempt 상한, 불명확 외부 효과 보류 |
| R-18 권한·자원 | GT4/8 | GV01–07, S12/13/28 | 지역 파일·CAS·승인/예산·실제 계정 admission 검사. 네이티브 전체 호스트 격리 보류 |
| R-19 독립 범위 | GT5 | KI08, S24/25 | blind scope 계약·선고정 의무. 실제 분리된 제품 Auditor 미실행 |
| R-20 수정·재감사 | GT5 | KI06/08, S24 | 개발자 감사와 재검증 기록. 제품 체인 미실행 |
| R-21 전략 축적 | GT6 | SI05/GV02, S20/21 | originating note에 증거와 회복 이력, counterfactual·한계 |
| R-22 조건부 재사용 | GT6 | SI06, S21/22 | 동일 프로젝트 조건 일치·불일치와 negative control. 외부 프로젝트 금지 |
| R-23 필수 품질 | GT7 | RI06, MG8 | breadth·반증·독립 판독 기준 유지 |
| R-24 실제 개선 | GT7 | RI01–06, MG8 | 0.28.1 두 반복 모두 개선 0/3, 후보 REAL 미실행 |
| R-25 자원·개입 비교 | GT7 | AR04/GV05, S28 | 이전 raw 비용표 보존, 이번 경계 시험과 자원 원장. 동일 품질 모델 비용 미측정 |
| R-26 호환성 | GT8 | GV06/AR06, S10/11 | CLI 회귀·양 호스트 메타데이터. 최신 실제 모델 연구 세션 미실행 |
| R-27 독립 인수 | GT8 | MG7–9 | 개발 검토/제품 Auditor/독립 연구 품질/실사용자 구분, 최종 차단 |

기존 결과의 출처는 공개 검토 ZIP의 `01-GATE-LEDGER.md`와 `evidence/C/TRACEABILITY.md.txt`다. 이전 Gate의 PASS는 위 후보 열에서 다시 판정했다. 별도 바탕화면 Runtime의 FR01–20/NFR01–12/G0–G8는 개발 대상이 달라 이번 실행으로 상태를 변경하지 않았다. [공개 증거 원본 대조](baseline-public-comparison.json)

## 확정된 제품 결정

| 결정 | 현재 경로 | 적용 확인 범위 |
|---|---|---|
| Q01 A 개인 연구자 | 명시적 프로젝트 루트와 단일 소유자 | CLI 확인. 다중 사용자 서비스 도입 없음 |
| Q02 B 연구·설계·시뮬레이션 | Study, metric, simulate, proposal | 실행 계산/실패/조건 변경 확인. REAL 품질 미실행 |
| Q03 C 중요 변경 자동 저장 | 신규 significant, 실행값의 선택적 proposal, 역할별 기록 | 실제 simulation→proposal 확인. 새 연구 질문의 중요도 판단은 모델 검증 필요 |
| Q04 C 주장·가설·반례·실패·질문 | findings/Study/plan/recovery | 서로 다른 상태·근거·관계. 실제 연구의 완전성 미실행 |
| Q05 A 프로젝트 지식 격리 | 외부 source 차단, 지역 검색, namespace | helper 범위 확인. 모델 호스트 차단 |
| Q05-1 A 전략 격리 | 현재 프로젝트의 originating note | 같은 프로젝트 조건 재검토. 모델 호스트 차단 |
| Q06 C 사용자 직접 수정 | direct edit, preimage, 검토와 receipt 무효화 | 정상/충돌/손상 경로 검증. 비협력 편집기의 원자적 병합 보장 없음 |
| Q07 B 최신성·적용성 | source 해시, Study assessment, finding conditions | 파일 변경·불일치 검증. 외부 인용 최신성은 새 조회 필요 |
| Q08 D 모드 전환 | learning session/lesson, Coordinator | 위임·지원·공동 모드 CLI. 실제 동적 제품 세션 미실행 |
| Q09 D 프로젝트 초월 이해 모델 | 분리된 일반 개념 profile | 합성 사용자로 생성·조회·수정·삭제, 제한 입력 검사 |
| Q10 C 계산·적용까지 확인 | 차원별 학습 상태, worked application | 확인 근거와 추론 구분. 실사용자 이해도 미측정 |
| Q11 C 독립 연구 능력 향상 | 선택적 과제와 전이 연습 | 실제 독립 능력 개선 NOT_RUN |
| Q12 C 참여·위임 | 사용자 관측/가설/정정의 기여 귀속 | CONTEXT CAS 변경과 위임 시 교육 생략 |
| Q13 C 상위 목적 문제와 대안 | 제안·추론·사용자 확정 목적, 변경 승인 | 승인 없는 확정 목표 변경 거절 검증. 목적 문제 자율 발견 미실행 |
| Q14 C 승인 자원 내 배분 | coordinate와 승인 스냅샷, 시뮬레이션 제한 | 지역 CAS 예약·실제 중단. 제공자 과금 상한 보장 미입증 |
| Q15 D 연구별 우선순위 | 기존 승인 근거와 quality/cost/time | 지역 투영 확인. 실사용자 최적화 효과 미측정 |

## 책임별 인수

아래 근거는 검증한 층에만 적용한다. “실행”은 지정한 CLI/개발 probe에서의 관측이다. 제품 연구 인수에 필요한 실제 모델 도구 사용과 판독은 MG7–MG9 원장에서 다룬다.

| 책임 | 개별 인수 조건과 결과 | 증거 |
|---|---|---|
| KI | KI01 계산→proposal 실행. KI02 주장·근거·조건 참조 실행. KI03 동일/상이 조건 비교와 명시적 중복 분리, 의미 판정 일반화 UNKNOWN. KI04 반박·상충 관계 보존. KI05 프로젝트 내 검색 및 적용 조건 구분. KI06 의존 무효화와 edit 보류. KI07 실제 반환·최종 문단 대조 실행. KI08 누락 주입 검출, 독립 모델의 의미적 누락 탐지 NOT_RUN. KI09 preimage·충돌 실행. KI10 제한 조회·전송과 선택적 수치 기록 실행, 실제 Context 비용 UNKNOWN | test_findings, test_knowledge, test_delivery, test_simulation, [통합 독립 검토](development-audit/integrated-proposal-audit.md) |
| RI | RI01 적응 재귀, RI02 미제시 문제 발견, RI03 양방향 실제 연구는 최종 모델 NOT_RUN. RI04 설계 변수 비교와 시뮬레이션 실행. RI05 폐형식 검산·재실행 결과 해시 검증. RI06 실제 과학적 충분성은 REAL 판독 필요 | test_simulation, test_study_amend, [공개 회귀 원자료와 답안](final-source/known/results.json) |
| SI | SI01 내부 실패/미반환 신호 검출, 자율 과학적 회복 NOT_RUN. SI02 의미 계보·카운트 실행. SI03 전수, SI04 메타는 근거 요구/지역 상태 전이만 확인. SI05 원 질문 내 실패/회복 축적 실행. SI06 적용·비적용 대조 실행, 인과 효과 UNKNOWN | test_recovery, test_strategy, test_coordination |
| HI | HI01 세 모드·HI02 목적의 출처·HI03 관측/가설 귀속·HI04 제한된 전역 모델·HI05 차원별 증거·HI06 차등 예제/반복 생략·HI08 단일 차원/개념/전체 삭제는 지역 실행. HI07 실제 연구 참여/판단 부담 개선 NOT_RUN. HI05·06의 인지 결과도 미확인 | test_learning, [차등 설명과 삭제 실제 출력](development-audit/learning-S16-S17-final-results.json) |
| AR | AR01 CAP 입출력 계약 정의. AR02 동일 입력 transport 경량 비교 실행. AR03 역할/스킬/helper의 현재 분배 및 실제 등록 대조. AR04 같은 기계적 성공 조건에서 비용 비교, 모델 품질대비 자원 UNKNOWN. AR05 무의미한 dispatch 거절 및 선택적 투영 확인, 실제 제품 배정 NOT_RUN. AR06 오프라인 호스트와 접근 통제 범위 실측 | [동일 조건 비교](architecture/matched-boundary-comparison.md), test_plugin_sync, [호스트 경계](evaluation/FEASIBILITY.md) |
| GV | GV01 지식·GV02 전략은 지역 API와 격리된 작업자에서 확인, 전체 호스트 BLOCKED. GV03 닫힌 학습 필드·프로필 비마운트 검증, unrestricted host 보장 BLOCKED. GV04 단일 원본·해시·Revision 검증. GV05 지역 예약·소진 검증, 외부 포함사용 강제 BLOCKED. GV06 신규·기존 정책과 v1/v2 회귀 실행. GV07 CAS/재시도·중단·편집 충돌 확인, 독립 외부 편집기 경쟁 한계 유지 | test_policy_boundaries, test_isolation, test_layout_migration, test_learning, test_coordination, [모델 없는 작업자 경계](evaluation/worker-controller-probe.json) |

## S01–S30 실행 범위

기본 입력은 일회용 프로젝트와 로컬 쓰기·계산 권한이다. 계정, 실제 장비, 실사용자 연구 기록을 사용하지 않았다. 아래의 CLI 출력은 개발 Host가 받은 값이다. 실제 모델 연구에서 사용자가 받은 답은 모든 행에서 미관측이다. 각 행은 실제 증거와 제품 인수를 위해 남은 관측을 함께 표시한다. 회귀 명령과 독립 판독은 [재현 절차](REPRODUCE.md)에 연결한다.

| ID | 입력·초기 상태 → 실행과 변경 | 확인된 출력 / 재개 조건 | 제품 검증 상태 |
|---|---|---|---|
| S01 | 새 프로젝트 목적 → init·연구 질문/의무 기록 | 사용자 목적·stable question 보존. 중요 미제시 질문은 모델이 직접 발견해야 함 | NOT_RUN |
| S02 | 경쟁 가설 → Study start/observe/amend/decide | 예측·판별 결과·조건 유지. 실제 설명 선택 독립 판독 필요 | 로컬 실행, REAL NOT_RUN |
| S03 | 프로젝트에 관련 finding/Study 있음 → 검색 후 조건·근거 재검토 | ID·revision·조건과 적용 상태 반환. 모델 자발 검색 미실행 | 로컬 실행 |
| S04 | 새 model/case → simulate --record-result → 새 프로세스 resume | 선택 수치·단위·코드/입력 hash, PROPOSED. 승인된 관측과 초기 가설 분리 | 독립 CLI 재검증 |
| S05 | 수치/조건/한계 빠진 역할 반환 → findings return | 거절·이전 revision 보존. 수정 반환만 통과 | 오류 주입·독립 재검증 |
| S06 | 기록과 불일치하는 실제 과거 답 → deliver → 교정 문단 | 누락 거절·교정 초안 hash·cold inspect. 모델 스스로 교정 미실행 | 알려진 자료 CLI 회귀 |
| S07 | 사용자 관측 입력 → learning contribute, Study 후속 관측/개정 | CONTEXT 기여 귀속, 변경 revision. 동일 모델 세션의 자동 재평가 미실행 | 구성요소 실행 |
| S08 | 상충 근거 및 모델 입력 변경 → impacts·source hash 재검사 | 영향받은 판단 재검토·STALE. 과학적 결론 변경 여부 미실행 | 로컬 실행 |
| S09 | source/target 조건 불일치 → assess/search | 충돌·미확정·근거 오래됨을 구분. 새 검증 필요 | 로컬 실행 |
| S10 | 종료 후 새 CLI → context --question, study, recovery | 기록/질문/전략/상태 복원. 새 모델 세션의 선택은 미관측 | 로컬 실행 |
| S11 | Markdown 직접 수정/경쟁 writer → inspect/review-edit | 수정 중 전이 거절, raw preimage·USER/UNKNOWN 재검토, stale CAS 거절 | 독립 CLI 재검증 |
| S12 | sibling/nested/legacy record/symlink → 접근·검색 시도 | 지역 경계 거절, 역사 보존. 새 대화·모든 호스트 도구의 격리 미입증 | 지역 실행, 전체 BLOCKED |
| S13 | 전역 프로필에 프로젝트 텍스트·식별자·임의 경로 → 입력 | 허용 필드 밖의 데이터 거절. 별도 작업자에서 profile 접근 차단 | 지역 실행, 전체 BLOCKED |
| S14 | 위임 모드 → session/lesson/coordinate concise | 교육·추가 자료 생성 생략. 실제 사용자 개입 절감 미측정 | 로컬 실행 |
| S15 | 사용자가 가설 제안 → learning contribute | 사용자 기여·가설/관측/결정 구분, 무승인 목표 변경 거절 | 로컬 실행 |
| S16 | 미확인 개념 차원 → 요청된 lesson | 선수 개념/검산 예제/적용 과제. 실제 이해 미측정 | 대리 입력 실행 |
| S17 | 확인된 차원 → 요청된 lesson | 기본 설명 생략·전이 문제. 확인 기록은 사용자 attestation | 대리 입력 실행 |
| S18 | 동일 노드에서 세 번째 유효 심화 → recovery | exhaustive_now와 실제 근거 제출 요구. 제품이 모든 관련 관점을 연구해야 인수 | helper 실행, 제품 NOT_RUN |
| S19 | 전수 이후 재요청 → recovery/meta-complete | 변경된 방법·실패 전제·근거 및 상태 확인. 실질적 새 연구는 미실행 | helper 실행, 제품 NOT_RUN |
| S20 | failed task나 미답 obligation → coordinate/return/deliver | 재작업 선별, 빠진 경계 차단. 모델의 자율 실패 감지 미실행 | 로컬 실행 |
| S21 | 동일 프로젝트의 적합 전략 → strategy-search/apply | 조건을 대조하고 원 노트에 실제 수행 주장·근거 hash·제한 기록 | 지역 실행, 효과 UNKNOWN |
| S22 | 조건/부정 대조 불일치 → strategy-apply | supported 판정 거절 및 비적용 근거 보존 | 로컬 실행 |
| S23 | 도구 실패·불명확한 외부 효과 → hold/coordinate | 불확정 작업 보류, 독립 작업 선택, 횟수 상한과 CAS | 로컬 실행 |
| S24 | 결함을 가진 revision → 독립 개발 감사·원 소유자 수정·재검사 | 출력 자원 경계, 조건 누락과 malformed JSON 재검사. 제품 Auditor 전체 체인은 별도 | 개발 감사 실행, 제품 NOT_RUN |
| S25 | 정상 수치/범위/조건 포함 → 독립 개발 검토 | 정상 fixture 거절 없이 통과. 실제 Auditor 오검출률 미측정 | 개발 대조, 제품 NOT_RUN |
| S26 | 출력·저항·열용량의 결합 → 두 설계 수치 적분 | 해석해와 비교하고 허용 온도에 따른 선택 구분. 물리 관측 미실행 | 실제 로컬 계산 |
| S27 | 발열량 또는 입력 파일 변경 → 재실행/기존 결과 조회 | 결과와 입력 hash 변화·오래된 근거 표시. 0 열용량 실패 | 실제 로컬 계산 |
| S28 | 계산 시간·출력·승인 자원 소진 → runner/coordinate | BUDGET_EXHAUSTED, 새 양수 예약 차단, 확인된 0수요 작업 가능. 계정 차단은 입증 필요 | 지역 실행, 제공자 BLOCKED |
| S29 | 상태 없는 간결 모드 → coordinate --mode concise | 파일·역할·등록 없이 응답. 실제 모델 출력 범위 미관측 | CLI 실행 |
| S30 | 200개 초과 질문 파일·한 파일에 100개 초과 관측 → 선택적 검색 | cursor로 후반 결과 회수, 조건·조회 범위 반환. 변경된 snapshot은 처음부터 재조회 | 규모 fixture 실행 |

개발용 기대 출력, 명령, 실제 출력과 실패 뒤 상태는 `test_findings.py`, `test_simulation.py`, `test_learning.py`, `test_coordination.py`, `test_strategy.py`, `test_isolation.py`, `test_policy_boundaries.py`의 각 시나리오 또는 [공개 자료 재생](final-source/known/results.json)에 있다. [통합 경계별 실제 명령·출력](development-audit/integrated-proposal-audit.json) · [학습 CLI 명령·출력](development-audit/learning-S16-S17-final-results.json)
