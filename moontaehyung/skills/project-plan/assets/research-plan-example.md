# 합성 연구 지도 예시

실제 조사 결과나 확정된 연구 계획이 아닙니다. 초기화 시 프로젝트의 관리 메타데이터를 유지하세요.

```project-plan
{
  "schema_version": 1,
  "plan_id": "example-wildfire",
  "revision": 1,
  "goal": "예시: 작은 산불 발견 방법의 검증",
  "current_node": "D-001",
  "nodes": [
    {
      "id": "O-001",
      "kind": "outcome",
      "title": "작은 산불 발견",
      "status": "provisional",
      "success_criteria": "실제 프로젝트에서 탐지 크기·시간과 오경보 기준을 합의할 것"
    },
    {
      "id": "D-001",
      "kind": "decision",
      "title": "관측 수단을 선택할까?",
      "status": "provisional",
      "revisit_when": "데이터 확보 또는 비교 결과가 가정을 반박할 때",
      "options": [
        {
          "id": "rgb",
          "title": "일반 카메라",
          "forecast": "기존 관측 수단 활용 가능성",
          "conditions": "적합한 영상 데이터 확보",
          "resources": "카메라·라벨링 데이터",
          "risk": "야간 성능 불확실",
          "uncertainty": "합성 예시이며 성능 근거 없음",
          "verification": "동일 조건의 데이터로 비교 평가",
          "evidence": []
        },
        {
          "id": "fusion",
          "title": "센서 결합",
          "forecast": "상호 보완 정보 활용 가능성",
          "conditions": "시간·위치가 맞는 두 영상 확보",
          "resources": "두 센서·정합 데이터",
          "risk": "정합 오차와 추가 비용",
          "uncertainty": "합성 예시이며 성능 근거 없음",
          "verification": "동일 조건의 데이터로 비교 평가",
          "evidence": []
        }
      ]
    },
    {
      "id": "D-002",
      "kind": "decision",
      "title": "어떻게 검증할까?",
      "status": "unexplored",
      "options": [
        {
          "id": "public",
          "title": "공개 데이터",
          "forecast": "추가 조사 필요",
          "conditions": "자료 확인 필요",
          "resources": "미확인",
          "risk": "현장 대표성 불확실",
          "uncertainty": "미조사",
          "verification": "실현 가능성 조사",
          "evidence": []
        },
        {
          "id": "flight",
          "title": "비행 수집",
          "forecast": "추가 조사 필요",
          "conditions": "자료 확인 필요",
          "resources": "미확인",
          "risk": "현장 대표성 불확실",
          "uncertainty": "미조사",
          "verification": "실현 가능성 조사",
          "evidence": []
        }
      ]
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
      "to": "D-002",
      "relation": "CHOOSE",
      "option": "rgb"
    },
    {
      "from": "D-001",
      "to": "D-002",
      "relation": "CHOOSE",
      "option": "fusion"
    }
  ],
  "sources": {}
}
```

## History — append only

- Example revision 1: synthetic alternatives, no selection or empirical claim.
