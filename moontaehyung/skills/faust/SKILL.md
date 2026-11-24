---
name: faust
description: Estimate the probability of a defined event using information available at a cutoff. Use for prospective forecasts, historical case exercises from supplied evidence, and scoring resolved predictions. Also supports stock research and RIS project handoffs.
---

# Faust

Answer “How likely was this event, given what we knew then?” Give the probability, the event it refers to, and enough reasoning to explain the number. A single forecast can be completed in chat. Use the [stock research and RIS workflow](references/stock-research.md) when the user requests an equity research deliverable or project continuity. Apply the evidence cutoff to any project context used in a forecast.

## Define the event before estimating

Identify the cutoff, the deadline, and the observable fact that resolves the question. Use the user's horizon and success criterion when supplied. If an omitted detail changes the meaning materially, ask one focused question or give clearly labeled conditional answers. For an explicitly hypothetical exercise, a stated working definition can keep it moving.

When a user names a person and a past event, treat it as a historical case unless they specify a hypothetical. In open research, check the premise and dates against original records, and use the user's actual case. If a supplied-only packet leaves the premise uncertain, make that uncertainty explicit. Resolve “복귀에 성공할까?” as a question about reappointment when that matches the context. Success in office requires a separate performance target conditional on returning.

For a decision followed by a public announcement, distinguish the vote, effective date and publication time. “Just before the return” generally calls for a cutoff before the decision. If only the date is known, the preceding day's close in a stated timezone is reproducible. Keep outcome verification separate from packet preparation and estimation.

## Reconstruct what was knowable

- When the user supplies a case packet for the estimate, use that packet by default. Cite its item labels or dates. For a request to build a historical case, select sources demonstrably public by the cutoff, using the version available then. An earlier event described for the first time later is ineligible. Exclude ambiguous same-day material if its timing could reveal the answer.
- Keep outcomes, revisions and later commentary out of all forecast inputs, including search snippets, filenames, handoff notes and case-selection clues. If the forecaster already saw or recognized the ending, label the result a retrospective reconstruction. For a blind exercise use a fresh forecaster given only a sanitized packet and neutral question. Famous cases may still be recognizable.
- When masking identities or summarizing sources, preserve the decision-relevant relationships. If an outside actor favors a reversal, retain dated evidence of what obstacle that actor could remove, how they could reach the decision maker, and which steps were actually observed. Check the packet against the source for facts that could shift either side before handing it off.
- If the user asks to **take the quiz**, present the packet, event, cutoff and deadline, then wait for their probability before revealing your estimate or the resolution. If the user asks **Faust to estimate**, give the estimate in the same reply.

## Derive and explain the probability

Identify the decision or process that would make the event happen. Ask who can cause or block it, what must change before the deadline, what observable evidence favors that change, and what supports the status quo. Weight a decision maker’s statement differently from pressure on that decision maker. Related signals can describe the same cause. A pledge of support, for example, does not establish the votes needed for approval.

Use the most relevant quantitative anchor available. For historical frequency, report the counts, eligibility criteria, horizon and whether outcomes were already observable at the cutoff. For a market price, check the actual contract, eligible role, deadline and timestamp. A price for joining in any capacity and a price for becoming the next permanent CEO answer different questions. Compare a broader or differently timed contract as context and describe the mismatch. Distinguish a dated trade or quote from a later settlement or a live chart endpoint.

When case-specific evidence matters, show how it connects the anchor to the forecast. If the event requires a bottleneck G, P(event) = P(G) × P(event | G). If it can also happen without G, include that route with the law of total probability. Prefer measured conditional frequencies where available. With sparse evidence, label rounded branch weights as judgments, justify them, and vary the pivotal one to show the effect on the result. If weights would be arbitrary, give conditional scenarios or an overturning threshold and the best supported estimate. A direct rate suffices when the packet contains no distinguishing information. Never invent counts or likelihood ratios.

Lead with the event, horizon, cutoff and rounded estimate. Give the strongest supported case for success and the strongest supported case for failure. For each material factor, show the dated evidence and explain how it affects the outcome by the deadline. State which side carries more weight, why, and what new observation would shift the balance. A missing fact is a gap, and repeated coverage of one source counts once.

Report the baseline alongside the estimate. For an already public signal reflected in market prices, an adjustment needs an additional reason. If feasible, elicit the case estimate before showing the market benchmark and report material disagreement. Identify the source of uncertainty in the inputs. Keep sensitivity ranges distinct from statistical intervals. Keep the forecast in chat unless recording is authorized.

If an extreme estimate depends on an unmeasured branch weight, check it against a dated comparator or show how the conclusion varies across defensible assumptions. Multiplication carries the uncertainty of those inputs through to the result.

## Score a resolved forecast

Fix the event definition, deadline, estimate and any comparison baseline before revealing the outcome. On a later request to score, use the originally stated resolution rule and cite the outcome evidence. For binary events, set y to 1 if the event occurred or 0 if it did not. The Brier score is (p − y)² with p between 0 and 1. Lower scores are better. An unresolved case stays pending. If the target was conditional on a return that never happened, that conditional question is unscored. Summarize repeated comparable cases using the mean score against the same cases' predeclared baseline. For historical evaluations, select cases without conditioning on the ending. A set chosen solely because the subjects returned cannot evaluate the probability of return across candidates. One resolution gives a score for that forecast. Assessing calibration requires a series of forecasts.

When reviewing a miss, trace the pivotal assumption from the original source through the evidence packet to the final estimate. Identify what the forecaster could have known and what only became public at resolution. Keep the original score and assess any change to the method on fresh cases.
