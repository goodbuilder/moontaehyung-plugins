---
ris_id: "findings-2e329903-1406-4682-b06d-08b89ea6064e-R01"
project_id: "2e329903-1406-4682-b06d-08b89ea6064e"
kind: "finding"
status: "governed"
created: "ledger-v1"
---

# Research knowledge

<!-- ris:findings -->
```json
{
  "schema_version": 1,
  "project_id": "2e329903-1406-4682-b06d-08b89ea6064e",
  "question_id": "R01",
  "revision": 8,
  "proposals": [
    {
      "finding": {
        "id": "F1",
        "statement": "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
        "status": "CONFIRMED",
        "conditions": {
          "dataset": "frozen source only"
        },
        "axes": {
          "topic": "R01",
          "origin": "calculation",
          "validation": "development arithmetic check",
          "audit": "not independently audited"
        },
        "relations": [],
        "provenance": [
          {
            "source": "file:R01-co2.csv",
            "locator": "Header lines 25–34 and May/October 2026 rows",
            "revision": "sha256:163cadae3baa6dec7d3ae066108b50d1018a78447b1b6fc2b6e3936465549d16",
            "limitations": [
              "NOAA flags interpolated months with negative standard deviation and uncertainty. For the early Scripps series the negative fields mark unavailable quality statistics. The May and October rows compared here have positive day counts and uncertainty."
            ]
          }
        ]
      },
      "owner": "development-producer",
      "state": "INTEGRATED",
      "accepted_revision": 3,
      "accept_note": "Development fixture, scoped to the frozen source.",
      "return_receipt": {
        "owner": "development-producer",
        "finding_revision": 3,
        "transcript_sha256": "82e44ffd3239b829bad77253aabacb1975143b8fb14499bd815ee538501b4738",
        "verified_passages": [
          "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
          "NOAA flags interpolated months with negative standard deviation and uncertainty. For the early Scripps series the negative fields mark unavailable quality statistics. The May and October rows compared here have positive day counts and uncertainty.",
          "Conditions: dataset=frozen source only."
        ]
      },
      "return_finding_sha256": "a7c1fad2bd6dcac7990ee06031994eef9f90f7afedd8263efc4a249ac7f96eba",
      "return_note": "Development fixture, scoped to the frozen source.",
      "integrate_note": "Development fixture, scoped to the frozen source.",
      "disposition": {
        "specified_by": "regression-oracle",
        "disposition": "USER_DELIVERY",
        "decision_critical": true,
        "reason": "Changes interpretation for the user",
        "condition": "Frozen record"
      }
    }
  ],
  "obligations": [
    {
      "id": "scope",
      "specified_by": "regression-oracle",
      "question": "What are the method qualifications on these data?",
      "expected_scope": {
        "topic": "R01"
      },
      "finding_ids": [
        "F1"
      ],
      "text": "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
      "state": "CURRENT"
    }
  ],
  "history": [
    {
      "revision": 1,
      "action": "obligate",
      "idempotency_key": "op-1",
      "changes": [
        {
          "collection": "obligations",
          "id": "scope",
          "before": null,
          "after": {
            "id": "scope",
            "specified_by": "regression-oracle",
            "question": "What are the method qualifications on these data?",
            "expected_scope": {
              "topic": "R01"
            },
            "finding_ids": [],
            "text": "",
            "state": "OPEN"
          }
        }
      ],
      "affected": []
    },
    {
      "revision": 2,
      "action": "propose",
      "idempotency_key": "op-2",
      "changes": [
        {
          "collection": "proposals",
          "id": "F1",
          "before": null,
          "after": {
            "finding": {
              "id": "F1",
              "statement": "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R01",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R01-co2.csv",
                  "locator": "Header lines 25–34 and May/October 2026 rows",
                  "revision": "sha256:163cadae3baa6dec7d3ae066108b50d1018a78447b1b6fc2b6e3936465549d16",
                  "limitations": [
                    "NOAA flags interpolated months with negative standard deviation and uncertainty. For the early Scripps series the negative fields mark unavailable quality statistics. The May and October rows compared here have positive day counts and uncertainty."
                  ]
                }
              ]
            },
            "owner": "development-producer",
            "state": "PROPOSED"
          }
        }
      ],
      "affected": []
    },
    {
      "revision": 3,
      "action": "accept",
      "idempotency_key": "op-3",
      "changes": [
        {
          "collection": "proposals",
          "id": "F1",
          "before": {
            "finding": {
              "id": "F1",
              "statement": "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R01",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R01-co2.csv",
                  "locator": "Header lines 25–34 and May/October 2026 rows",
                  "revision": "sha256:163cadae3baa6dec7d3ae066108b50d1018a78447b1b6fc2b6e3936465549d16",
                  "limitations": [
                    "NOAA flags interpolated months with negative standard deviation and uncertainty. For the early Scripps series the negative fields mark unavailable quality statistics. The May and October rows compared here have positive day counts and uncertainty."
                  ]
                }
              ]
            },
            "owner": "development-producer",
            "state": "PROPOSED"
          },
          "after": {
            "finding": {
              "id": "F1",
              "statement": "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R01",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R01-co2.csv",
                  "locator": "Header lines 25–34 and May/October 2026 rows",
                  "revision": "sha256:163cadae3baa6dec7d3ae066108b50d1018a78447b1b6fc2b6e3936465549d16",
                  "limitations": [
                    "NOAA flags interpolated months with negative standard deviation and uncertainty. For the early Scripps series the negative fields mark unavailable quality statistics. The May and October rows compared here have positive day counts and uncertainty."
                  ]
                }
              ]
            },
            "owner": "development-producer",
            "state": "RECORDED",
            "accepted_revision": 3,
            "accept_note": "Development fixture, scoped to the frozen source."
          }
        }
      ],
      "affected": [
        "F1"
      ]
    },
    {
      "revision": 4,
      "action": "return",
      "idempotency_key": "op-5",
      "changes": [
        {
          "collection": "proposals",
          "id": "F1",
          "before": {
            "finding": {
              "id": "F1",
              "statement": "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R01",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R01-co2.csv",
                  "locator": "Header lines 25–34 and May/October 2026 rows",
                  "revision": "sha256:163cadae3baa6dec7d3ae066108b50d1018a78447b1b6fc2b6e3936465549d16",
                  "limitations": [
                    "NOAA flags interpolated months with negative standard deviation and uncertainty. For the early Scripps series the negative fields mark unavailable quality statistics. The May and October rows compared here have positive day counts and uncertainty."
                  ]
                }
              ]
            },
            "owner": "development-producer",
            "state": "RECORDED",
            "accepted_revision": 3,
            "accept_note": "Development fixture, scoped to the frozen source."
          },
          "after": {
            "finding": {
              "id": "F1",
              "statement": "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R01",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R01-co2.csv",
                  "locator": "Header lines 25–34 and May/October 2026 rows",
                  "revision": "sha256:163cadae3baa6dec7d3ae066108b50d1018a78447b1b6fc2b6e3936465549d16",
                  "limitations": [
                    "NOAA flags interpolated months with negative standard deviation and uncertainty. For the early Scripps series the negative fields mark unavailable quality statistics. The May and October rows compared here have positive day counts and uncertainty."
                  ]
                }
              ]
            },
            "owner": "development-producer",
            "state": "RETURNED",
            "accepted_revision": 3,
            "accept_note": "Development fixture, scoped to the frozen source.",
            "return_receipt": {
              "owner": "development-producer",
              "finding_revision": 3,
              "transcript_sha256": "82e44ffd3239b829bad77253aabacb1975143b8fb14499bd815ee538501b4738",
              "verified_passages": [
                "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
                "NOAA flags interpolated months with negative standard deviation and uncertainty. For the early Scripps series the negative fields mark unavailable quality statistics. The May and October rows compared here have positive day counts and uncertainty.",
                "Conditions: dataset=frozen source only."
              ]
            },
            "return_finding_sha256": "a7c1fad2bd6dcac7990ee06031994eef9f90f7afedd8263efc4a249ac7f96eba",
            "return_note": "Development fixture, scoped to the frozen source."
          }
        }
      ],
      "affected": [
        "F1"
      ]
    },
    {
      "revision": 5,
      "action": "integrate",
      "idempotency_key": "op-6",
      "changes": [
        {
          "collection": "proposals",
          "id": "F1",
          "before": {
            "finding": {
              "id": "F1",
              "statement": "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R01",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R01-co2.csv",
                  "locator": "Header lines 25–34 and May/October 2026 rows",
                  "revision": "sha256:163cadae3baa6dec7d3ae066108b50d1018a78447b1b6fc2b6e3936465549d16",
                  "limitations": [
                    "NOAA flags interpolated months with negative standard deviation and uncertainty. For the early Scripps series the negative fields mark unavailable quality statistics. The May and October rows compared here have positive day counts and uncertainty."
                  ]
                }
              ]
            },
            "owner": "development-producer",
            "state": "RETURNED",
            "accepted_revision": 3,
            "accept_note": "Development fixture, scoped to the frozen source.",
            "return_receipt": {
              "owner": "development-producer",
              "finding_revision": 3,
              "transcript_sha256": "82e44ffd3239b829bad77253aabacb1975143b8fb14499bd815ee538501b4738",
              "verified_passages": [
                "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
                "NOAA flags interpolated months with negative standard deviation and uncertainty. For the early Scripps series the negative fields mark unavailable quality statistics. The May and October rows compared here have positive day counts and uncertainty.",
                "Conditions: dataset=frozen source only."
              ]
            },
            "return_finding_sha256": "a7c1fad2bd6dcac7990ee06031994eef9f90f7afedd8263efc4a249ac7f96eba",
            "return_note": "Development fixture, scoped to the frozen source."
          },
          "after": {
            "finding": {
              "id": "F1",
              "statement": "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R01",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R01-co2.csv",
                  "locator": "Header lines 25–34 and May/October 2026 rows",
                  "revision": "sha256:163cadae3baa6dec7d3ae066108b50d1018a78447b1b6fc2b6e3936465549d16",
                  "limitations": [
                    "NOAA flags interpolated months with negative standard deviation and uncertainty. For the early Scripps series the negative fields mark unavailable quality statistics. The May and October rows compared here have positive day counts and uncertainty."
                  ]
                }
              ]
            },
            "owner": "development-producer",
            "state": "INTEGRATED",
            "accepted_revision": 3,
            "accept_note": "Development fixture, scoped to the frozen source.",
            "return_receipt": {
              "owner": "development-producer",
              "finding_revision": 3,
              "transcript_sha256": "82e44ffd3239b829bad77253aabacb1975143b8fb14499bd815ee538501b4738",
              "verified_passages": [
                "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
                "NOAA flags interpolated months with negative standard deviation and uncertainty. For the early Scripps series the negative fields mark unavailable quality statistics. The May and October rows compared here have positive day counts and uncertainty.",
                "Conditions: dataset=frozen source only."
              ]
            },
            "return_finding_sha256": "a7c1fad2bd6dcac7990ee06031994eef9f90f7afedd8263efc4a249ac7f96eba",
            "return_note": "Development fixture, scoped to the frozen source.",
            "integrate_note": "Development fixture, scoped to the frozen source."
          }
        }
      ],
      "affected": [
        "F1"
      ]
    },
    {
      "revision": 6,
      "action": "resolve",
      "idempotency_key": "op-7",
      "changes": [
        {
          "collection": "obligations",
          "id": "scope",
          "before": {
            "id": "scope",
            "specified_by": "regression-oracle",
            "question": "What are the method qualifications on these data?",
            "expected_scope": {
              "topic": "R01"
            },
            "finding_ids": [],
            "text": "",
            "state": "OPEN"
          },
          "after": {
            "id": "scope",
            "specified_by": "regression-oracle",
            "question": "What are the method qualifications on these data?",
            "expected_scope": {
              "topic": "R01"
            },
            "finding_ids": [
              "F1"
            ],
            "text": "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
            "state": "CURRENT"
          }
        }
      ],
      "affected": []
    },
    {
      "revision": 7,
      "action": "disposition",
      "idempotency_key": "op-8",
      "changes": [
        {
          "collection": "proposals",
          "id": "F1",
          "before": {
            "finding": {
              "id": "F1",
              "statement": "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R01",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R01-co2.csv",
                  "locator": "Header lines 25–34 and May/October 2026 rows",
                  "revision": "sha256:163cadae3baa6dec7d3ae066108b50d1018a78447b1b6fc2b6e3936465549d16",
                  "limitations": [
                    "NOAA flags interpolated months with negative standard deviation and uncertainty. For the early Scripps series the negative fields mark unavailable quality statistics. The May and October rows compared here have positive day counts and uncertainty."
                  ]
                }
              ]
            },
            "owner": "development-producer",
            "state": "INTEGRATED",
            "accepted_revision": 3,
            "accept_note": "Development fixture, scoped to the frozen source.",
            "return_receipt": {
              "owner": "development-producer",
              "finding_revision": 3,
              "transcript_sha256": "82e44ffd3239b829bad77253aabacb1975143b8fb14499bd815ee538501b4738",
              "verified_passages": [
                "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
                "NOAA flags interpolated months with negative standard deviation and uncertainty. For the early Scripps series the negative fields mark unavailable quality statistics. The May and October rows compared here have positive day counts and uncertainty.",
                "Conditions: dataset=frozen source only."
              ]
            },
            "return_finding_sha256": "a7c1fad2bd6dcac7990ee06031994eef9f90f7afedd8263efc4a249ac7f96eba",
            "return_note": "Development fixture, scoped to the frozen source.",
            "integrate_note": "Development fixture, scoped to the frozen source."
          },
          "after": {
            "finding": {
              "id": "F1",
              "statement": "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R01",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R01-co2.csv",
                  "locator": "Header lines 25–34 and May/October 2026 rows",
                  "revision": "sha256:163cadae3baa6dec7d3ae066108b50d1018a78447b1b6fc2b6e3936465549d16",
                  "limitations": [
                    "NOAA flags interpolated months with negative standard deviation and uncertainty. For the early Scripps series the negative fields mark unavailable quality statistics. The May and October rows compared here have positive day counts and uncertainty."
                  ]
                }
              ]
            },
            "owner": "development-producer",
            "state": "INTEGRATED",
            "accepted_revision": 3,
            "accept_note": "Development fixture, scoped to the frozen source.",
            "return_receipt": {
              "owner": "development-producer",
              "finding_revision": 3,
              "transcript_sha256": "82e44ffd3239b829bad77253aabacb1975143b8fb14499bd815ee538501b4738",
              "verified_passages": [
                "The October 2026 monthly mean was 426.69, down 5.65 from May. The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
                "NOAA flags interpolated months with negative standard deviation and uncertainty. For the early Scripps series the negative fields mark unavailable quality statistics. The May and October rows compared here have positive day counts and uncertainty.",
                "Conditions: dataset=frozen source only."
              ]
            },
            "return_finding_sha256": "a7c1fad2bd6dcac7990ee06031994eef9f90f7afedd8263efc4a249ac7f96eba",
            "return_note": "Development fixture, scoped to the frozen source.",
            "integrate_note": "Development fixture, scoped to the frozen source.",
            "disposition": {
              "specified_by": "regression-oracle",
              "disposition": "USER_DELIVERY",
              "decision_critical": true,
              "reason": "Changes interpretation for the user",
              "condition": "Frozen record"
            }
          }
        }
      ],
      "affected": []
    },
    {
      "revision": 8,
      "action": "deliver",
      "idempotency_key": "op-10",
      "changes": [
        {
          "collection": "delivery",
          "before": null,
          "after": {
            "draft": "corrected-passage.md",
            "sha256": "bd9aac6b62c7142f6420da5623cea08c5bed3f03dd4805d0196c8bdfd142500b",
            "scope": "Exact transport; no semantic/scientific validation",
            "revision": 8
          }
        }
      ],
      "affected": []
    }
  ],
  "operations": {
    "op-1": "b97a6c527979257f62e9adcc1990e9b06f20b99016eab6895a6d2b82ffc9a1c5",
    "op-2": "5186f4e05b433cc7c0387b6c9de818982390d785324fc6d1dcb4579ca5bfed19",
    "op-3": "1928f201548f66bf57a99cd9a66c5ef3f4b29e4dc400159c0bb5cc1bc00b1356",
    "op-5": "04fb906030113ee6f1f662b6260e8cbadf52f027b97d4a4ca7eb6151d4fa78d3",
    "op-6": "4f5390aaa936ce3a09adf7cb4acee9eb236178f1184a5f61f03f6be40f1d1ef6",
    "op-7": "1fe0ce073a36986ec4fba799948df9cebff0a0ce954da702a00cacf482562fd1",
    "op-8": "ae6b675a31c505570d6605d86bd19b15e8e40518672d719d9d40a428ac2dc59a",
    "op-10": "c9dfdd7e4ee64d9297dd737c528930f509cd81c130095a5081487c0ca1bf2e1c"
  },
  "narrative_sha256": "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b",
  "content_sha256": "13aa52ab10a364caa70f201f4511fefc094fd091c37b44abaa678a114ac24d15",
  "delivery": {
    "draft": "corrected-passage.md",
    "sha256": "bd9aac6b62c7142f6420da5623cea08c5bed3f03dd4805d0196c8bdfd142500b",
    "scope": "Exact transport; no semantic/scientific validation",
    "revision": 8
  }
}
```
<!-- /ris:findings -->
