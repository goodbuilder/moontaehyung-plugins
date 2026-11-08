# 넓이와 깊이를 보이는 합성 탐색 예시

실제 문헌 조사나 실험 결과가 아닙니다. 센서·자료·배치 조건이 서로의 실현 가능성을 바꾸므로 개별 선택을 독립적으로 확정하면 안 됩니다. 모든 조합은 별도 타당성 검토가 필요합니다.

```project-plan
{
  "schema_version": 1,
  "plan_id": "example-wildfire-expanded",
  "revision": 3,
  "goal": "합성 예시: 작은 산불 조기 발견의 연구 경로",
  "current_node": "D-001",
  "nodes": [
    {
      "id": "O-001",
      "kind": "outcome",
      "title": "작은 산불 조기 발견의 연구 기여",
      "status": "provisional",
      "success_criteria": "탐지 지연·오경보·관측 범위의 우선순위와 평가 조건을 사용자와 합의"
    },
    {
      "id": "D-001",
      "kind": "decision",
      "title": "어떤 관측 접근으로 목표를 달성할까?",
      "status": "provisional",
      "options": [
        {
          "id": "baseline",
          "title": "기존 관측·순찰 개선",
          "forecast": "기존 자산 활용과 절차 개선을 비교 기준으로 삼을 수 있음",
          "conditions": "관측 인력·고정 관측 자료 접근",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "드론 연구 기여가 약해질 수 있음",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "같은 구역·조건에서 탐지 지연과 오경보를 비교",
          "evidence": []
        },
        {
          "id": "rgb",
          "title": "일반 영상 중심",
          "forecast": "연기·불꽃의 시각 단서를 활용할 가능성",
          "conditions": "가시광 영상과 라벨",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "야간·구름·연무 혼동",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "낮/밤과 유사 연기 조건을 분리 평가",
          "evidence": []
        },
        {
          "id": "thermal",
          "title": "열화상 중심",
          "forecast": "가시 단서와 다른 온도 이상 단서를 활용할 가능성",
          "conditions": "방사 정보와 환경 메타데이터",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "태양 가열·거리·온도 보정 영향",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "온도와 환경별 비화재 열원 포함 비교",
          "evidence": []
        },
        {
          "id": "fusion",
          "title": "일반 영상+열화상 결합",
          "forecast": "두 관측의 보완성 여부를 연구할 수 있음",
          "conditions": "정합·동기화된 영상",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "정합 오차·결측 센서",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "단일 센서와 결합 방식 및 결측 조건 비교",
          "evidence": []
        },
        {
          "id": "spectral",
          "title": "다중 분광 관측",
          "forecast": "파장별 구분 가능성을 연구할 수 있음",
          "conditions": "센서 파장·보정 데이터 확보",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "장비·데이터 접근성과 과적합",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "장소·시기 외부 검증으로 밴드 조합 비교",
          "evidence": []
        }
      ],
      "component": "관측 방식"
    },
    {
      "id": "D-010",
      "kind": "decision",
      "title": "기존 관측의 어느 병목을 개선할까?",
      "status": "provisional",
      "options": [
        {
          "id": "schedule",
          "title": "순찰 일정",
          "forecast": "위험 조건별 관측 빈도 조정",
          "conditions": "기존 탐지 지연 자료",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "접근성·인력 제약",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "기존 일정 대비 재현 평가",
          "evidence": []
        },
        {
          "id": "alert",
          "title": "신고 검증",
          "forecast": "오경보 검증 절차 개선",
          "conditions": "신고·확인 이력",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "지연 증가 가능성",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "검증 시간과 누락 사건 비교",
          "evidence": []
        }
      ],
      "component": "기존 관측 개선"
    },
    {
      "id": "D-020",
      "kind": "decision",
      "title": "영상에서 어떤 단서를 모델링할까?",
      "status": "provisional",
      "options": [
        {
          "id": "smoke",
          "title": "연기 시공간 변화",
          "forecast": "불꽃 전 단계 단서 검토",
          "conditions": "연속 영상 라벨",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "구름·안개 혼동",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "프레임 단독 대비 시계열 비교",
          "evidence": []
        },
        {
          "id": "flame",
          "title": "불꽃 형태",
          "forecast": "가시 불꽃 단서 비교",
          "conditions": "충분한 불꽃 장면",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "가림·작은 불꽃",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "크기·가림별 성능 평가",
          "evidence": []
        },
        {
          "id": "joint",
          "title": "연기·불꽃 공동 모델",
          "forecast": "상호 단서 활용",
          "conditions": "두 대상 라벨",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "데이터 불균형",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "대상별 소거 실험",
          "evidence": []
        }
      ],
      "component": "영상 단서"
    },
    {
      "id": "D-021",
      "kind": "decision",
      "title": "영상 모델을 어떻게 구성할까?",
      "status": "provisional",
      "options": [
        {
          "id": "spatial",
          "title": "프레임별 탐지",
          "forecast": "단일 영상 기준선 확보",
          "conditions": "장면 라벨",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "시간 단서 누락",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "동일 장면의 시계열 모델과 비교",
          "evidence": []
        },
        {
          "id": "temporal",
          "title": "시간 누적 탐지",
          "forecast": "변화 패턴 활용",
          "conditions": "동기화 연속 영상",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "응답 지연",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "누적 창 길이별 지연·오경보 비교",
          "evidence": []
        }
      ],
      "component": "영상 모델"
    },
    {
      "id": "D-030",
      "kind": "decision",
      "title": "열화상을 어떤 값으로 해석할까?",
      "status": "provisional",
      "options": [
        {
          "id": "absolute",
          "title": "절대 온도",
          "forecast": "물리량을 활용한 이상 정의",
          "conditions": "방사 보정·방사율 가정",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "거리·환경 편향",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "참조 열원과 환경별 오차 확인",
          "evidence": []
        },
        {
          "id": "relative",
          "title": "주변 대비 이상",
          "forecast": "지역 대비 정보를 활용",
          "conditions": "주변 영역 품질",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "주변 열원 혼동",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "태양 가열 물체를 포함한 평가",
          "evidence": []
        }
      ],
      "component": "열화상 해석"
    },
    {
      "id": "D-031",
      "kind": "decision",
      "title": "열 이상을 어떻게 판별할까?",
      "status": "provisional",
      "options": [
        {
          "id": "rule",
          "title": "물리 기준·규칙",
          "forecast": "설명 가능한 기준선",
          "conditions": "명시한 보정 가정",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "환경별 기준 변화",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "조건별 민감도 평가",
          "evidence": []
        },
        {
          "id": "learned",
          "title": "학습 기반 이상 판별",
          "forecast": "복잡한 패턴 학습 가능성",
          "conditions": "독립 장소 열화상 데이터",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "배경 과적합",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "새 장소와 시간대 검증",
          "evidence": []
        }
      ],
      "component": "열 이상 판별"
    },
    {
      "id": "D-040",
      "kind": "decision",
      "title": "서로 다른 영상을 어떻게 맞출까?",
      "status": "provisional",
      "options": [
        {
          "id": "calibration",
          "title": "기하 보정",
          "forecast": "보정된 대응 위치 사용",
          "conditions": "내외부 파라미터",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "진동·열 변화",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "거리·진동별 정합 오차 측정",
          "evidence": []
        },
        {
          "id": "learned",
          "title": "특징 기반 정합",
          "forecast": "장면에 따른 대응 활용",
          "conditions": "공통 특징",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "연기·가림에서 실패",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "특징 부족 장면으로 실패 검증",
          "evidence": []
        }
      ],
      "component": "영상 정합"
    },
    {
      "id": "D-041",
      "kind": "decision",
      "title": "두 센서의 정보를 언제 결합할까?",
      "status": "provisional",
      "options": [
        {
          "id": "early",
          "title": "입력 단계 결합",
          "forecast": "초기 공동 표현 학습",
          "conditions": "밀접한 픽셀 정합",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "정합 오차 증폭",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "정합 오차 주입 비교",
          "evidence": []
        },
        {
          "id": "feature",
          "title": "특징 단계 결합",
          "forecast": "표현 상호 보완",
          "conditions": "동일 관측 시점",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "결측 시 불안정",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "센서 누락·지연 조건 비교",
          "evidence": []
        },
        {
          "id": "late",
          "title": "판정 단계 결합",
          "forecast": "독립 센서 결과 조정",
          "conditions": "신뢰도 보정",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "상충 판정 처리",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "상충 사건과 센서별 소거 비교",
          "evidence": []
        }
      ],
      "component": "센서 융합"
    },
    {
      "id": "D-050",
      "kind": "decision",
      "title": "어떤 파장 정보를 확보할까?",
      "status": "provisional",
      "options": [
        {
          "id": "available",
          "title": "가용 밴드",
          "forecast": "현재 장비에 맞는 실험",
          "conditions": "센서 사양 확인",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "문제 구분력 부족",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "비화재 유사 물체와 밴드별 비교",
          "evidence": []
        },
        {
          "id": "targeted",
          "title": "문제에 맞는 밴드",
          "forecast": "목표 구분 근거 기반 조합",
          "conditions": "검증된 광학 근거와 장비 접근",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "자료·비용 제약",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "독립 자료로 밴드 선택 재검증",
          "evidence": []
        }
      ],
      "component": "관측 파장"
    },
    {
      "id": "D-051",
      "kind": "decision",
      "title": "분광 표현을 어떻게 구성할까?",
      "status": "provisional",
      "options": [
        {
          "id": "index",
          "title": "물리 지표",
          "forecast": "설명 가능한 표현",
          "conditions": "파장 해석 근거",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "조건 의존성",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "조도·계절별 지표 안정성 검증",
          "evidence": []
        },
        {
          "id": "representation",
          "title": "학습 표현",
          "forecast": "복잡한 밴드 상호작용 학습",
          "conditions": "충분한 데이터",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "고차원 과적합",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "장소 분리와 밴드 소거 비교",
          "evidence": []
        }
      ],
      "component": "분광 표현"
    },
    {
      "id": "D-060",
      "kind": "decision",
      "title": "어떤 데이터 경로로 검증할까?",
      "status": "provisional",
      "options": [
        {
          "id": "public",
          "title": "공개 자료 재사용",
          "forecast": "재현 가능한 초기 비교",
          "conditions": "자료의 라이선스·센서·조건 확인",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "실환경 대표성 부족",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "중복 장면과 누출을 제거하고 외부 평가",
          "evidence": []
        },
        {
          "id": "collect",
          "title": "직접 수집",
          "forecast": "목표 조건에 맞춘 관측",
          "conditions": "현장·안전·장비 접근의 별도 승인",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "표본 부족과 수집 편향",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "비화재 대조군·조건별 표본 검토",
          "evidence": []
        },
        {
          "id": "combine",
          "title": "공개+수집 자료",
          "forecast": "다양성과 목표 조건을 함께 검토",
          "conditions": "두 도메인의 메타데이터",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "도메인 차이",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "자료별 결과와 전이 효과 분리",
          "evidence": []
        }
      ],
      "component": "데이터 확보"
    },
    {
      "id": "D-070",
      "kind": "decision",
      "title": "어디에서 판별할까?",
      "status": "provisional",
      "options": [
        {
          "id": "onboard",
          "title": "기체 내부",
          "forecast": "통신 의존성 감소 가능성",
          "conditions": "전력·계산·열 예산",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "모델 지연·전력 제한",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "기체 예산에서 지연·전력 측정",
          "evidence": []
        },
        {
          "id": "ground",
          "title": "지상 처리",
          "forecast": "더 큰 모델 검토 가능성",
          "conditions": "영상 전송 품질",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "망 지연·단절",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "망 부하와 단절 조건 평가",
          "evidence": []
        }
      ],
      "component": "처리 위치"
    },
    {
      "id": "D-080",
      "kind": "decision",
      "title": "일반화를 어떤 실험으로 입증할까?",
      "status": "provisional",
      "options": [
        {
          "id": "site",
          "title": "장소 분리",
          "forecast": "배경 암기 여부 확인",
          "conditions": "독립 지역 데이터",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "시기 편향 잔존",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "학습 지역과 겹치지 않는 검증",
          "evidence": []
        },
        {
          "id": "time",
          "title": "시기 분리",
          "forecast": "계절·조도 변화 평가",
          "conditions": "장기 자료",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "장소 편향 잔존",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "시간 누출을 차단하고 외부 장소 병행",
          "evidence": []
        },
        {
          "id": "stress",
          "title": "조건별 스트레스 평가",
          "forecast": "실패 경계 탐색",
          "conditions": "조건 메타데이터",
          "resources": "요구 자원·데이터의 실제 확보 가능성 조사",
          "risk": "합성 실패의 현실성",
          "uncertainty": "합성 예시: 실제 성능·비용은 미측정이며 아래 검증으로 확인해야 함",
          "verification": "실제 관측과 모의 실패를 분리 보고",
          "evidence": []
        }
      ],
      "selection_mode": "multiple",
      "component": "일반화 검증"
    },
    {
      "id": "G-001",
      "kind": "gate",
      "title": "성공 기준 충족 여부와 재계획",
      "status": "unexplored"
    }
  ],
  "edges": [
    {
      "from": "O-001",
      "to": "D-001",
      "relation": "AND"
    },
    {
      "from": "D-001",
      "to": "D-010",
      "relation": "CHOOSE",
      "option": "baseline"
    },
    {
      "from": "D-001",
      "to": "D-020",
      "relation": "CHOOSE",
      "option": "rgb"
    },
    {
      "from": "D-001",
      "to": "D-030",
      "relation": "CHOOSE",
      "option": "thermal"
    },
    {
      "from": "D-001",
      "to": "D-040",
      "relation": "CHOOSE",
      "option": "fusion"
    },
    {
      "from": "D-001",
      "to": "D-050",
      "relation": "CHOOSE",
      "option": "spectral"
    },
    {
      "from": "D-010",
      "to": "D-060",
      "relation": "CHOOSE",
      "option": "schedule"
    },
    {
      "from": "D-010",
      "to": "D-060",
      "relation": "CHOOSE",
      "option": "alert"
    },
    {
      "from": "D-020",
      "to": "D-021",
      "relation": "CHOOSE",
      "option": "smoke"
    },
    {
      "from": "D-020",
      "to": "D-021",
      "relation": "CHOOSE",
      "option": "flame"
    },
    {
      "from": "D-020",
      "to": "D-021",
      "relation": "CHOOSE",
      "option": "joint"
    },
    {
      "from": "D-021",
      "to": "D-060",
      "relation": "CHOOSE",
      "option": "spatial"
    },
    {
      "from": "D-021",
      "to": "D-060",
      "relation": "CHOOSE",
      "option": "temporal"
    },
    {
      "from": "D-030",
      "to": "D-031",
      "relation": "CHOOSE",
      "option": "absolute"
    },
    {
      "from": "D-030",
      "to": "D-031",
      "relation": "CHOOSE",
      "option": "relative"
    },
    {
      "from": "D-031",
      "to": "D-060",
      "relation": "CHOOSE",
      "option": "rule"
    },
    {
      "from": "D-031",
      "to": "D-060",
      "relation": "CHOOSE",
      "option": "learned"
    },
    {
      "from": "D-040",
      "to": "D-041",
      "relation": "CHOOSE",
      "option": "calibration"
    },
    {
      "from": "D-040",
      "to": "D-041",
      "relation": "CHOOSE",
      "option": "learned"
    },
    {
      "from": "D-041",
      "to": "D-060",
      "relation": "CHOOSE",
      "option": "early"
    },
    {
      "from": "D-041",
      "to": "D-060",
      "relation": "CHOOSE",
      "option": "feature"
    },
    {
      "from": "D-041",
      "to": "D-060",
      "relation": "CHOOSE",
      "option": "late"
    },
    {
      "from": "D-050",
      "to": "D-051",
      "relation": "CHOOSE",
      "option": "available"
    },
    {
      "from": "D-050",
      "to": "D-051",
      "relation": "CHOOSE",
      "option": "targeted"
    },
    {
      "from": "D-051",
      "to": "D-060",
      "relation": "CHOOSE",
      "option": "index"
    },
    {
      "from": "D-051",
      "to": "D-060",
      "relation": "CHOOSE",
      "option": "representation"
    },
    {
      "from": "D-060",
      "to": "D-070",
      "relation": "CHOOSE",
      "option": "public"
    },
    {
      "from": "D-060",
      "to": "D-070",
      "relation": "CHOOSE",
      "option": "collect"
    },
    {
      "from": "D-060",
      "to": "D-070",
      "relation": "CHOOSE",
      "option": "combine"
    },
    {
      "from": "D-070",
      "to": "D-080",
      "relation": "CHOOSE",
      "option": "onboard"
    },
    {
      "from": "D-070",
      "to": "D-080",
      "relation": "CHOOSE",
      "option": "ground"
    },
    {
      "from": "D-080",
      "to": "G-001",
      "relation": "AND",
      "option": "site"
    },
    {
      "from": "D-080",
      "to": "G-001",
      "relation": "AND",
      "option": "time"
    },
    {
      "from": "D-080",
      "to": "G-001",
      "relation": "AND",
      "option": "stress"
    }
  ],
  "sources": {},
  "current_candidate": "C-001",
  "candidates": [
    {
      "id": "C-001",
      "title": "영상 시계열 후보",
      "selections": {
        "D-001": [
          "rgb"
        ],
        "D-020": [
          "smoke"
        ],
        "D-021": [
          "temporal"
        ],
        "D-060": [
          "public"
        ],
        "D-070": [
          "onboard"
        ],
        "D-080": [
          "site",
          "time"
        ]
      }
    },
    {
      "id": "C-002",
      "title": "열 이상 후보",
      "selections": {
        "D-001": [
          "thermal"
        ],
        "D-030": [
          "relative"
        ],
        "D-031": [
          "rule"
        ],
        "D-060": [
          "public"
        ],
        "D-070": [
          "onboard"
        ],
        "D-080": [
          "site",
          "stress"
        ]
      }
    },
    {
      "id": "C-003",
      "title": "센서 결합 후보",
      "selections": {
        "D-001": [
          "fusion"
        ],
        "D-040": [
          "calibration"
        ],
        "D-041": [
          "late"
        ],
        "D-060": [
          "public"
        ],
        "D-070": [
          "onboard"
        ],
        "D-080": [
          "site",
          "time",
          "stress"
        ]
      }
    }
  ]
}
```

## History — append only
- Synthetic revision 1: multiple mechanisms and consequential decision stages; no empirical claims or confirmed choices. Gate outcomes require the real project criteria.

- Synthetic revision 2: candidates share public data and onboard processing; complementary validation choices support multiple selections. No real feasibility or acceptance claim.

- Synthetic revision 3: explicit component labels for the option catalog and candidate matrix.
