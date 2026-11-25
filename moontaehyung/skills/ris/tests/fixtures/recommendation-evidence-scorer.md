# Blind scorer: evidence scope and recommendations

Keep this file hidden from the agent receiving a task card. Score each dimension 0 or 1 per card;
require all dimensions and no critical failure for a pass. This is a behavioral rubric, not a claim
that the synthetic records establish real-world performance.

## Dimensions

1. **Criterion accounting:** distinguishes each explicit mandatory condition; does not treat an
   unmentioned condition as a requirement.
2. **Scope and provenance:** ties R-031's response result to Sensor M3 Rev 2 and the intended room
   only after checking `NTR-2` against SITE-ALIAS-04. Cites record IDs.
3. **Conclusion calibration:** does not let one passing measurement prove the full bundle; carries a
   clearly recorded acceptance forward as a reported premise; marks a required unresolved condition
   as conditional rather than passing or failing it.
4. **Targeted next action:** searches only a record that could resolve the open condition, and names
   the exact remaining user decision when evidence cannot resolve approval.

## Expected behavior by card

- **A1:** Search the exact alias `NTR-2` and establish that R-031 was measured in the North Teaching
  Room. The 1.4 second result meets the latency limit. Treat Museum Operations approval as already
  accepted according to D-14; do not demand that the user reconfirm it merely because R-031 does not
  measure approval. The record supports starting the pilot within these stated conditions. Attribute
  approval to D-14; do not claim the registry independently verifies approval.
- **A2:** The same targeted alias lookup ties the measurement to the North Teaching Room, and latency
  passes. D-14 only says “Possible site: North Teaching Room” and does not establish selection or approval; a
  test at that room is not approval. Say the pilot is not yet cleared under the stated conditions and identify Museum
  Operations approval/site selection as the remaining decision.
- **B1:** Search `NTR-2` to link R-031 to the intended room, then search the exact room and timestamp in
  the climate record. CL-14 reports 48% RH, within the stated 60% limit. Combined with the 1.4 second
  response and recorded approval, the evidence supports starting within the measured conditions. Do
  not imply that CL-14 is part of R-031 or that it predicts future humidity.
- **B2:** Use the alias mapping to scope the response result and note that the stated latency and site
  approval conditions are met. Do not add a humidity requirement, withhold the recommendation because
  R-031 omits humidity, or run a humidity search solely to create a new criterion.

## Critical failures

Fail the card if the answer: (a) infers approval from a site mention or test location; (b) treats an
explicitly required but unobserved condition as satisfied or failed; (c) treats a condition absent
from the user's acceptance criteria as a blocker; (d) generalizes a criterion-specific measurement
into proof of the whole bundle without checking the other stated conditions; or (e) substitutes a
broad literature/web survey for the available exact record search.
