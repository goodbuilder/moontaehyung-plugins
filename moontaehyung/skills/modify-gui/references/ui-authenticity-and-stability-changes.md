# UI Authenticity and Stability Changes

Preserve the application's intentional visual language and spatial behavior. “AI-made” is not a provenance test based on one rounded corner; it is a useful warning when a change replaces product-specific decisions with interchangeable defaults.

## Baseline before editing

Inspect existing design documents, tokens, components, native conventions, screenshots, runtime states, and code reuse. Capture affected UI at target resolutions, DPI/font scales, locale/theme, and normal/loading/stale/unavailable/warning/error/permission/recovery states.

For every affected dynamic label, status, table column, plot legend, message, or conditional control, record format, precision, unit, update cadence, shortest/longest plausible localized content, overflow behavior, and current geometry/focus/selection/scroll effects. Drive value rollovers such as `9.999` to `10.000`, sign changes, time digit changes, unavailable text, and long error messages. Do not rely on a single static screenshot.

## Reject generic replacement patterns

Do not introduce without a documented operator purpose:

- generic SaaS/dashboard shell, centered hero, symmetrical metric cards, nested card soup, or unrelated decorative charts;
- large radius/pills everywhere, gradient/glow/glassmorphism, heavy shadow, excessive whitespace, oversized headings, emoji, or vague marketing copy;
- bright badges for every state, color-only meaning, invented metrics, inconsistent icons, one-off controls, or new inline styling that bypasses existing tokens/components;
- animation, auto-expansion, hover-only content, repeated modal alerts, or moving controls that do not support the workflow.

A card, badge, icon, animation, or rounded surface is allowed when it has a specific structural/semantic role and matches the approved system. The objective is contextual design, not a blanket stylistic ban.

## Stable dynamic content

Treat geometry and interaction stability as compatibility. Frequently changing content must not resize panels, docks, splitters, windows, table columns, or adjacent click targets; steal focus; reset selection; or jump scroll unless an approved workflow transition requires it.

Use a constant display format and precision, stable units, numeric alignment, and tabular/fixed-width numerals where available. Reserve size once from widest valid representative strings using font metrics. Use intentional size policies/minimum or maximum extents, accessible elision/tooltip/detail views, and bounded wrapping. Throttle/coalesce visible updates to the operator-needed rate.

For Qt, prefer deliberate layouts and `QSizePolicy`, `QFontMetrics.horizontalAdvance()`/`elidedText()`, and fixed/interactive/stretch table header policies chosen at initialization. Avoid `adjustSize()`, `updateGeometry()`, or resize-to-contents on every live update.

A Pixhawk time field should, for example, keep a constant format such as `HH:mm:ss.SSS`, reserve its maximum width, and replace digits without changing surrounding geometry.

## Approval and regression

Show before/after screenshots plus a dynamic-state sequence, explain any intentional layout transition, and include the existing design rationale/component reuse in the impact analysis. A visual cleanup does not authorize unrelated redesign.

Test target resolution/DPI/font scale/locale/theme, longest text, digit/sign/precision rollover, stale/unavailable/error messages, rapid updates, conditional controls, keyboard focus, target size, contrast/non-color cues, and critical workflows. Reject clipping without recovery, moving controls, flicker, focus/scroll jumps, or a new generic template aesthetic unsupported by the product.
