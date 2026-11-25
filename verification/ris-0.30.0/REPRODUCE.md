# 재현 및 인계

공식 저장소에서 이 디렉터리는 `verification/ris-0.30.0/`이다. 검증 대상은 [후보 식별자](final-source/identity.json), [소스 파일 해시](final-source/source-manifest.json), [배포용 디렉터리 구조의 소스 ZIP](final-source/candidate-source.zip)이다. 원본 Git의 커밋을 추가하거나 설치본을 갱신하지 않고 독립 디렉터리에 전개하여 시험했다.

## 환경과 실행

Linux x86-64, Python 3.10, pytest, Linux bubblewrap와 util-linux prlimit가 필요하다. 모델 없이 실행하는 제품 CLI와 검증에 사용한 설치 버전은 [환경](environment.txt)에 있다. Claude Code 및 Codex의 실제 계정 로그인과 일반 환경의 설정 변경은 이 절차에 필요하지 않다. 아래 명령은 이 보고서가 있는 디렉터리에서 실행한다.

```bash
packet="$PWD"
trial_dir=$(mktemp -d)
unzip -q "$packet/final-source/candidate-source.zip" -d "$trial_dir"
plugin_dir="$trial_dir/moontaehyung"
python3 "$plugin_dir/skills/ris/scripts/ris.py" --help
(cd "$plugin_dir" && python3 -m pytest -v -s --tb=short skills/ris/tests skills/project-plan/tests skills/faust/tests)
python3 "$packet/replay_known.py" "$plugin_dir/skills/ris/scripts/ris.py" "$packet" "$trial_dir/known"
python3 "$packet/engineering_replay.py" "$plugin_dir" "$trial_dir/thermal"
```

`replay_known.py`는 승인된 과거 공개 자료에만 의존한다. 새 체크아웃에서는 이 폴더의 공개 데이터·원본 답안으로 회귀를 실행한다. 과거 원본 디렉터리 세 개까지 보유한 경우 `python3 verify_baseline.py "$HOME/ris-verification"`로 Git 기준 객체 및 [0.29.0 공개 아키텍처 검토 ZIP](historical/RIS-0.29.0-007ee7f-architecture-review.zip)과 원본을 다시 대조할 수 있다. 실패를 재현할 때 입력 원본은 건드리지 않고 새 출력 디렉터리를 지정한다. 재생의 각 질문 폴더에는 입력 JSON, 과거 답안, 수정 문단, 실제 명령 및 정본 Markdown이 남는다. 온도 재생은 정상·동일 재실행·발열량 변경·0 열용량 실패에 대해 입력과 응답을 보존한다. [원본 대조](baseline-public-comparison.json) · [답안 재생](final-source/known/results.json) · [온도 모형의 실제 입출력](final-source/thermal/receipts.json)

최종 파일 검증은 아래처럼 실행한다. 각 파일의 해시는 manifest상의 같은 상대 경로를 가리킨다.

```bash
python3 - "$packet/final-source" "$plugin_dir" <<'PY'
import hashlib, json, sys
from pathlib import Path
packet,root=map(Path,sys.argv[1:])
raw=(packet/'source-manifest.json').read_bytes()
identity=json.loads((packet/'identity.json').read_text())
sha=lambda data:hashlib.sha256(data).hexdigest()
assert sha(raw)==identity['manifest_sha256']
assert sha((packet/'candidate-source.zip').read_bytes())==identity['archive_sha256']
for rel,expected in json.loads(raw).items():
    assert sha((root/rel).read_bytes())==expected,rel
print(identity)
PY
```

호스트 메타데이터 스크립트는 지정 지문을 먼저 검사한다. 네트워크와 실제 홈·로그인 자료가 없는 임시 환경에서 실행한다. SDK 초기화·역할/스킬 열거와 실제 모델 실행을 구분한다. [호스트 검증기](final-host-validation/verify_hosts.py)

## 복구와 후속 검증

- 다른 프로젝트로 전환할 때는 이전 대화·cache·전역 프로필·다른 연구 파일이 없는 새 작업자 환경을 준비한다. 기존 외부 참조를 삭제하지 않고 지역 근거로 재조사한다. 인증된 호스트 전체가 제한된 환경으로 동작함을 실제 읽기 실패와 허용 대조로 먼저 입증한다.
- CAS 실패는 현재 revision과 사용자 수정 내용을 다시 읽고 의미를 검토한 뒤 재시도한다. 동일 요청 재전송은 같은 식별자를 사용한다. 재작업은 변경된 주장과 그 의존 항목에 한정한다. CLI에서 직접 편집된 기록을 발견하면 `findings inspect` 후 검토와 preimage 보존을 거친다. 손상된 기록은 확인된 이력에서 복구한다.
- 예산·권한·외부 효과가 불명확하면 해당 작업을 보류하고 기존 근거와 예약 상태를 보존한다. 제공자의 포함 사용만 강제하는 실제 통제와 전체 작업자 격리를 확인할 때까지 모델 평가를 시작하지 않는다. 주간 비율 확인만으로는 유료 크레딧 전환의 강제 차단을 입증할 수 없다.
- 위 조건이 충족되면 확정된 상한 안에서 알려진 사례 회귀와 최소 제품 E2E부터 실시한다. 중요 내용의 선택 자체, 역할 반환, 정본 통합, 최종 문장과 독립 감사/재감사를 각각 판정한다. 이때 Host는 연구 판단을 대행하지 않는다. 모델 사용량과 실제 응답 지연을 계측한다.
- GT7·새 다단계 연구·미공개 Holdout은 승인된 개발 4세션 범위 밖이다. 별도 자원과 독립 관리자, 최종 지문에 맞는 사전등록 및 두 반복·세 분야 기준이 필요하다. 미공개 평가 결과를 본 후보를 수정하면 해당 문제를 새 Holdout으로 재사용할 수 없다. 인간 이해 검증은 당사자 동의와 실제 과제 수행이 전제다. [독립 재등록 검토](evaluation/V2-COVERAGE-AUDIT.md)

대화/모델 입력의 제한과 사용자의 실제 학습 능력은 로컬 Python 테스트만으로 재현할 수 없다. 이 부분은 [인수 원장](ACCEPTANCE.md)의 별도 Gate에 남겨 두었다.

이 revision에서 확인한 런타임 등록과 모델 비실행 한계는 [최종 호스트 영수증](final-host-validation/final-tsuvgfmy/SUMMARY.md)에 있다. 기존 지도 링크 검사는 전개한 플러그인 디렉터리에서 `node skills/archify/tests/tree-document-links.mjs`로 재현한다. 이 묶음의 소스와 공식 편집 사본의 마지막 대조는 [인계 검증](handoff-check.json)에 있다.
