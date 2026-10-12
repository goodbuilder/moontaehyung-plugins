# Operator UI Authenticity and Stability

An “AI-made look” is not proven by one rounded corner or font. It usually appears when unresolved product decisions are filled with interchangeable defaults rather than workflow- and domain-specific hierarchy. Design from operator tasks, information criticality, real states, and target hardware; use this reference as a rejection and verification guide, not a style superstition.

## Generic-template warning signs

Avoid by default unless a documented operator need justifies them:

- generic SaaS dashboard shell, centered hero, marketing headline, or symmetrical three-card/metric grid unrelated to the workflow;
- card soup, nested floating surfaces, large radius everywhere, pill containers for ordinary labels/navigation/status, and excessive empty space;
- purple/blue gradients, glow, glassmorphism, decorative blur, heavy shadow, ornamental charts, fake metrics, and icons added without informational value;
- every status rendered as a bright badge, healthy operation saturated with color, or color used without text/shape/position cues;
- oversized headings, generic “smart/powerful/seamless” copy, vague empty states, emoji, and interchangeable stock microcopy;
- inconsistent one-off controls, spacing, radii, colors, or inline styling instead of the project's component/tokens;
- animation, hover reveal, auto-expansion, carousel behavior, or transitions that do not improve state recognition or workflow;
- layout that looks polished in one screenshot but lacks loading, stale, unavailable, partial, long-text, error, permission, and recovery states.

Do not ban a component merely because generic AI output often uses it. A card, badge, icon, animation, or rounded surface is acceptable when it has a specific structural or semantic job and remains consistent with the approved design system.

For a traditional operator workstation, prefer compact native/conventional controls, few surface levels, subtle separators, tables/trees/forms for structured data, explicit units and axes, text-first navigation, quiet healthy state, strong numeric readability, and decoration subordinate to operation.

## Dynamic-content contract

For every frequently changing field, define:

- semantic value, source, update cadence, staleness, and operator-needed precision;
- canonical display format for normal, negative, maximum, unavailable, stale, warning, and error values;
- longest plausible localized label/value/unit and font/DPI profiles;
- reserved width/height, alignment, wrapping/elision/tooltip/detail policy, and whether resizing is ever allowed;
- throttling/coalescing and whether value changes may affect focus, selection, scroll, splitter/dock/window geometry, or neighboring click targets.

Changing content must not repeatedly change layout geometry. Stable dynamic fields should reserve space from the widest valid formatted sample using font metrics, use tabular or fixed-width numerals when available, keep precision and units consistent, and align numeric values. A Pixhawk time field, for example, should use a constant format such as `HH:mm:ss.SSS`, reserve its maximum width once, and update text without resizing the containing panel.

For Qt Widgets, use layouts and intentional `QSizePolicy`, minimum/maximum or stable size hints, `QFontMetrics.horizontalAdvance()` for representative maximum strings, and `elidedText()` where detail remains accessible. Do not call `adjustSize()`, `updateGeometry()`, `resizeColumnsToContents()`, or content-based row/column resizing on every live update. Choose table header modes deliberately; prevent live content from shifting columns after initialization unless the operator explicitly resizes them.

## Interaction comfort and accessibility

- Never move an active button, change its click target, steal focus, reset selection, or auto-scroll because a nearby value changed.
- Avoid flicker, flashing, needless motion, repeated modal dialogs, hover-only information, and rapidly alternating status colors.
- Throttle visual refresh to the rate needed for operator decisions while retaining full-rate backend evidence separately.
- Keep focus visible and unobscured; maintain logical keyboard order and meaningful accessible names.
- Provide sufficient contrast and non-color status cues; test font scaling, long translations, abbreviations, units, disabled states, and minimum target size appropriate to the operating environment.
- Preserve spatial memory: stable toolbar/navigation/status locations, stable table columns, and intentional—not incidental—layout transitions.

## Review gate

Review multiple state screenshots and a recorded/deterministic dynamic sequence at every target resolution, DPI/font scale, locale, and theme. Include shortest/longest values, digit rollovers, sign/precision changes, unavailable/stale/error text, rapid updates, large tables, and conditional controls.

Reject when live content changes panel/window/dock/splitter size, moves adjacent controls, clips important text without a recovery path, causes focus/scroll jumps, or makes the operator chase moving information. Also reject when the UI could belong to any generic product because visual hierarchy, components, copy, and density are not traceable to the approved workflow and domain.
