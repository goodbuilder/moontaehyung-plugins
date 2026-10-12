# GUI boundary change handoff

Use [maintain-boundaries](../../maintain-boundaries/SKILL.md) for the actual dependency/ownership
inventory, migration rules and structural regression checks. Use design-boundaries only for a
material new design decision; keep the work in the existing approved change packet.

Map before/after operator actions to visible states and backend postconditions. Identify affected
screens, shared controls, Qt parents/threads, resource budgets and manual/fallback paths. Ask only
unresolved operator outcomes, such as what must remain usable during another capability's failure.

Include material ownership or public-contract changes in the existing impact and approval summary.
If a change exceeds approved scope, follow modify-gui's applicable amendment process rather than
creating a separate architecture approval. Reuse verify-check evidence; add GUI interaction and
preserved-workflow checks appropriate to the affected boundary.
