---
ris_id: "findings-831f6434-0ba6-4970-9552-105e00a1ccc5-R02"
project_id: "831f6434-0ba6-4970-9552-105e00a1ccc5"
kind: "finding"
status: "governed"
created: "ledger-v1"
---

# Research knowledge

<!-- ris:findings -->
```json
{
  "schema_version": 1,
  "project_id": "831f6434-0ba6-4970-9552-105e00a1ccc5",
  "question_id": "R02",
  "revision": 8,
  "proposals": [
    {
      "finding": {
        "id": "F1",
        "statement": "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
        "status": "CONFIRMED",
        "conditions": {
          "dataset": "frozen source only"
        },
        "axes": {
          "topic": "R02",
          "origin": "calculation",
          "validation": "development arithmetic check",
          "audit": "not independently audited"
        },
        "relations": [],
        "provenance": [
          {
            "source": "file:R02-earthquakes.geojson",
            "locator": "features[*].properties.time and metadata.generated",
            "revision": "sha256:3e0c8275811091dd6bccf8a90edafe02c92f385159b4aa61d2b2b6c35122dad5",
            "limitations": [
              "The feed was generated at 2026-11-25T00:51:05.000+00:00. Event-origin endpoints describe observed events in this packet and do not measure catalogue completeness."
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
        "transcript_sha256": "f949e868ecc08268b55ddb3b83a2c2584aee53852a0e55128cc067225d6923b8",
        "verified_passages": [
          "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
          "The feed was generated at 2026-11-25T00:51:05.000+00:00. Event-origin endpoints describe observed events in this packet and do not measure catalogue completeness.",
          "Conditions: dataset=frozen source only."
        ]
      },
      "return_finding_sha256": "f8a0934f3388fc954ce10c6a3adb7685a80c955c342a0ff31a6ed2829bc303af",
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
      "question": "What is the observed event-origin interval?",
      "expected_scope": {
        "topic": "R02"
      },
      "finding_ids": [
        "F1"
      ],
      "text": "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
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
            "question": "What is the observed event-origin interval?",
            "expected_scope": {
              "topic": "R02"
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
              "statement": "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R02",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R02-earthquakes.geojson",
                  "locator": "features[*].properties.time and metadata.generated",
                  "revision": "sha256:3e0c8275811091dd6bccf8a90edafe02c92f385159b4aa61d2b2b6c35122dad5",
                  "limitations": [
                    "The feed was generated at 2026-11-25T00:51:05.000+00:00. Event-origin endpoints describe observed events in this packet and do not measure catalogue completeness."
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
              "statement": "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R02",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R02-earthquakes.geojson",
                  "locator": "features[*].properties.time and metadata.generated",
                  "revision": "sha256:3e0c8275811091dd6bccf8a90edafe02c92f385159b4aa61d2b2b6c35122dad5",
                  "limitations": [
                    "The feed was generated at 2026-11-25T00:51:05.000+00:00. Event-origin endpoints describe observed events in this packet and do not measure catalogue completeness."
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
              "statement": "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R02",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R02-earthquakes.geojson",
                  "locator": "features[*].properties.time and metadata.generated",
                  "revision": "sha256:3e0c8275811091dd6bccf8a90edafe02c92f385159b4aa61d2b2b6c35122dad5",
                  "limitations": [
                    "The feed was generated at 2026-11-25T00:51:05.000+00:00. Event-origin endpoints describe observed events in this packet and do not measure catalogue completeness."
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
              "statement": "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R02",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R02-earthquakes.geojson",
                  "locator": "features[*].properties.time and metadata.generated",
                  "revision": "sha256:3e0c8275811091dd6bccf8a90edafe02c92f385159b4aa61d2b2b6c35122dad5",
                  "limitations": [
                    "The feed was generated at 2026-11-25T00:51:05.000+00:00. Event-origin endpoints describe observed events in this packet and do not measure catalogue completeness."
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
              "statement": "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R02",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R02-earthquakes.geojson",
                  "locator": "features[*].properties.time and metadata.generated",
                  "revision": "sha256:3e0c8275811091dd6bccf8a90edafe02c92f385159b4aa61d2b2b6c35122dad5",
                  "limitations": [
                    "The feed was generated at 2026-11-25T00:51:05.000+00:00. Event-origin endpoints describe observed events in this packet and do not measure catalogue completeness."
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
              "transcript_sha256": "f949e868ecc08268b55ddb3b83a2c2584aee53852a0e55128cc067225d6923b8",
              "verified_passages": [
                "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
                "The feed was generated at 2026-11-25T00:51:05.000+00:00. Event-origin endpoints describe observed events in this packet and do not measure catalogue completeness.",
                "Conditions: dataset=frozen source only."
              ]
            },
            "return_finding_sha256": "f8a0934f3388fc954ce10c6a3adb7685a80c955c342a0ff31a6ed2829bc303af",
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
              "statement": "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R02",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R02-earthquakes.geojson",
                  "locator": "features[*].properties.time and metadata.generated",
                  "revision": "sha256:3e0c8275811091dd6bccf8a90edafe02c92f385159b4aa61d2b2b6c35122dad5",
                  "limitations": [
                    "The feed was generated at 2026-11-25T00:51:05.000+00:00. Event-origin endpoints describe observed events in this packet and do not measure catalogue completeness."
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
              "transcript_sha256": "f949e868ecc08268b55ddb3b83a2c2584aee53852a0e55128cc067225d6923b8",
              "verified_passages": [
                "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
                "The feed was generated at 2026-11-25T00:51:05.000+00:00. Event-origin endpoints describe observed events in this packet and do not measure catalogue completeness.",
                "Conditions: dataset=frozen source only."
              ]
            },
            "return_finding_sha256": "f8a0934f3388fc954ce10c6a3adb7685a80c955c342a0ff31a6ed2829bc303af",
            "return_note": "Development fixture, scoped to the frozen source."
          },
          "after": {
            "finding": {
              "id": "F1",
              "statement": "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R02",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R02-earthquakes.geojson",
                  "locator": "features[*].properties.time and metadata.generated",
                  "revision": "sha256:3e0c8275811091dd6bccf8a90edafe02c92f385159b4aa61d2b2b6c35122dad5",
                  "limitations": [
                    "The feed was generated at 2026-11-25T00:51:05.000+00:00. Event-origin endpoints describe observed events in this packet and do not measure catalogue completeness."
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
              "transcript_sha256": "f949e868ecc08268b55ddb3b83a2c2584aee53852a0e55128cc067225d6923b8",
              "verified_passages": [
                "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
                "The feed was generated at 2026-11-25T00:51:05.000+00:00. Event-origin endpoints describe observed events in this packet and do not measure catalogue completeness.",
                "Conditions: dataset=frozen source only."
              ]
            },
            "return_finding_sha256": "f8a0934f3388fc954ce10c6a3adb7685a80c955c342a0ff31a6ed2829bc303af",
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
            "question": "What is the observed event-origin interval?",
            "expected_scope": {
              "topic": "R02"
            },
            "finding_ids": [],
            "text": "",
            "state": "OPEN"
          },
          "after": {
            "id": "scope",
            "specified_by": "regression-oracle",
            "question": "What is the observed event-origin interval?",
            "expected_scope": {
              "topic": "R02"
            },
            "finding_ids": [
              "F1"
            ],
            "text": "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
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
              "statement": "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R02",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R02-earthquakes.geojson",
                  "locator": "features[*].properties.time and metadata.generated",
                  "revision": "sha256:3e0c8275811091dd6bccf8a90edafe02c92f385159b4aa61d2b2b6c35122dad5",
                  "limitations": [
                    "The feed was generated at 2026-11-25T00:51:05.000+00:00. Event-origin endpoints describe observed events in this packet and do not measure catalogue completeness."
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
              "transcript_sha256": "f949e868ecc08268b55ddb3b83a2c2584aee53852a0e55128cc067225d6923b8",
              "verified_passages": [
                "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
                "The feed was generated at 2026-11-25T00:51:05.000+00:00. Event-origin endpoints describe observed events in this packet and do not measure catalogue completeness.",
                "Conditions: dataset=frozen source only."
              ]
            },
            "return_finding_sha256": "f8a0934f3388fc954ce10c6a3adb7685a80c955c342a0ff31a6ed2829bc303af",
            "return_note": "Development fixture, scoped to the frozen source.",
            "integrate_note": "Development fixture, scoped to the frozen source."
          },
          "after": {
            "finding": {
              "id": "F1",
              "statement": "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
              "status": "CONFIRMED",
              "conditions": {
                "dataset": "frozen source only"
              },
              "axes": {
                "topic": "R02",
                "origin": "calculation",
                "validation": "development arithmetic check",
                "audit": "not independently audited"
              },
              "relations": [],
              "provenance": [
                {
                  "source": "file:R02-earthquakes.geojson",
                  "locator": "features[*].properties.time and metadata.generated",
                  "revision": "sha256:3e0c8275811091dd6bccf8a90edafe02c92f385159b4aa61d2b2b6c35122dad5",
                  "limitations": [
                    "The feed was generated at 2026-11-25T00:51:05.000+00:00. Event-origin endpoints describe observed events in this packet and do not measure catalogue completeness."
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
              "transcript_sha256": "f949e868ecc08268b55ddb3b83a2c2584aee53852a0e55128cc067225d6923b8",
              "verified_passages": [
                "The 55 event origins in the frozen packet run from 2026-11-24T01:32:42.417+00:00 to 2026-11-24T23:29:55.097+00:00.",
                "The feed was generated at 2026-11-25T00:51:05.000+00:00. Event-origin endpoints describe observed events in this packet and do not measure catalogue completeness.",
                "Conditions: dataset=frozen source only."
              ]
            },
            "return_finding_sha256": "f8a0934f3388fc954ce10c6a3adb7685a80c955c342a0ff31a6ed2829bc303af",
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
            "sha256": "40c1d8c9d83871148f596f00bd42f9b4448c3369dcee0753f98624575c6bd617",
            "scope": "Exact transport; no semantic/scientific validation",
            "revision": 8
          }
        }
      ],
      "affected": []
    }
  ],
  "operations": {
    "op-1": "6f705be19475a8b25894d0297b785c1d05190b5d6f01da2f3c0b93611218a3f3",
    "op-2": "68bf9d7409bc6755e86b1e5c1f5333594210c72b710c520d499a9c6b19eb0aab",
    "op-3": "dee281421a9dbe95ea1d81892c5b7dc16fcf7bb4924a5678fa8b97286a64743e",
    "op-5": "1b5feb93f1995ca7434ce19eddf9e812d91b6a985bc71bba9388c5bf428fdf29",
    "op-6": "de20dc57bf015465fff51ee8e7b257e577224d2226541aabed99479dd4a20f14",
    "op-7": "9d5a59091ff6b09bd6f11e05f0551c594758f6582965c7bfb8e7087236addd3e",
    "op-8": "54906b3108a0ba0c9de9b82f4f2ddbd0fa28b173db460d2bcdd0f1848268a34e",
    "op-10": "1f8d333b43d971157a842451c800f90d9daf578dfc23c62b5d8e5b6044ad5d17"
  },
  "narrative_sha256": "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b",
  "content_sha256": "1709b32cf9feb7b68041de92a5fe9707818c81dba50a3c37bed3c27c13d50283",
  "delivery": {
    "draft": "corrected-passage.md",
    "sha256": "40c1d8c9d83871148f596f00bd42f9b4448c3369dcee0753f98624575c6bd617",
    "scope": "Exact transport; no semantic/scientific validation",
    "revision": 8
  }
}
```
<!-- /ris:findings -->
