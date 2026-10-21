---
name: teach-me
description: Explain a real computation, algorithm, formula, or code path so a non-specialist can reproduce a worked example by hand. Use when the user explicitly asks to learn how a calculation works step by step, not for a short definition or routine code summary.
---

# Teach Me

Teach the computation used by the actual project. The reader should be able to follow its inputs, repeat the example arithmetic, and check the program's result. This skill is explicit-only; use it when the user invokes `$teach-me` or clearly asks for this teaching workflow.

## Before writing

1. Read the real code path, schema, data, or formula. Record exact input and output contracts, including units, coordinate frames, axis order, sign conventions, and iteration limits.
2. Choose one example whose answer can be checked. Prefer a small real case or a deterministic fixture. You may construct a synthetic example backwards from a known answer, but label it synthetic.
3. Run the smallest relevant real code path on that example when it is safe and practical. Do not launch a large or costly production run merely to make an example. If execution is not possible, show the hand calculation and state that the program was not run.
4. List the prerequisite ideas in dependency order. Use the reader's terms, then introduce the exact technical names used in code or data.
5. Choose the medium. Use Markdown for a short lesson. For an HTML page, follow the bundled `archify` skill's standalone explainer workflow and retain the worked-example structure below. Use self-contained inline SVG for any custom illustration; do not depend on remote assets or fonts.

## Lesson structure

1. **How to read this** — audience, needed tools, and the result the reader will reproduce.
2. **The example scene** — list each input, value, unit, source, and plain-language meaning. State the known answer and why it is checkable.
3. **Prerequisites (`0.1`, `0.2`, …)** — order concepts so each one uses earlier concepts. Each concept has exactly these four parts:
   - **What it is** — an everyday analogy, then the definition and formula.
   - **Why it is needed here** — name the computation step that uses it.
   - **With the example's numbers** — show every product, sum, unit, and intermediate value. Add one sanity check.
   - **Try it yourself** — one small exercise. Hide the answer in a `<details>` disclosure on HTML pages; put the answer below a clear divider in Markdown.

   End each prerequisite with a symbols table: symbol, meaning, unit, and where it appears in the project's data. Give each concept at least one diagram that shows the relevant mechanism.
4. **The method (`1`, `2`, …)** — follow the actual execution order. For each step, show the problem, why the implemented approach is used, the formula or operation, the example's numbers, and the prerequisite concepts it uses. Give each computation step a diagram or a clearly linked figure.
5. **End-to-end worked table** — show every operation on the example in order and reproduce the known answer in the final row.
6. **Cross-check** — compare the hand result, actual program output, and known answer. Explain any residual from rounding or iteration limits. Do not present a stubbed or partial run as a scientific result.
7. **Common mistakes and self-checks** — cover sign, units, angle mode, coordinate-frame mix-ups, rounding, and one independent check for each main step.

## Diagrams and interaction

- Draw the mechanism: which values enter, how they change, and which output they produce. Label arrows with project-specific values and units.
- Use the bundled `archify` skill for native diagrams in requested HTML explainers. When a diagram needs detail that the native form cannot express, use accessible inline SVG with `viewBox`, `role="img"`, an `aria-label`, and a caption.
- Use a small local calculator only when changing one input makes the lesson clearer. Keep the default value tied to the example, show units, and check that the displayed output matches the hand calculation.
- A diagram supports the explanation; prose and tables must still state the frame, units, assumptions, and result.

## Accuracy and scope

- Every number must come from the inspected code/data or arithmetic shown in the document. Cite repository files near claims that depend on them.
- Name fields with their declared axis contract. Do not infer the meaning of `x/y/z`; distinguish position frame from orientation frame.
- Introduce each symbol before using it. Restate its meaning when it reappears after a long gap.
- State what the example verifies and what it does not. A case-count example does not validate an optimizer; a geometry example does not validate a downstream transform.
- Preserve failure and missing-data outcomes. Do not select only successful results to make the example agree.
- Keep sentences short and explain why before how. Never use “obviously” or “simply.”

## Output

For a page, lead with a link to the HTML. Say what the reader can reproduce, which part of the real computation the page covers, and what example was used. State any important execution limit, such as a hand-checked case where the numerical solver was not run. Offer to teach the next computation step when useful.
