# Development rules

- Write documentation, comments, errors, UI text and new rules in English.
- Read existing behavior before editing. Preserve unrelated user changes.
- Prefer standard library, native HTML/CSS and installed dependencies, in that order.
- Keep changes small and concrete. No speculative configuration, new framework or generic abstraction.
- Validate inputs at trust boundaries and handle errors explicitly. Preserve evidence needed to diagnose failures.
- Render imported report text using `textContent`; never interpolate untrusted values into HTML.
- Restrict report file size, schema and numeric counts before calculating UI metrics.
- Use semantic controls, visible keyboard focus, readable contrast and responsive layouts. Respect reduced-motion preferences.
- Do not let the demo's presentation change scoring semantics or report contents.
- Write regression checks for nontrivial logic, using `unittest` or Node's built-in assertions.
- Keep generated files out of source directories. Never commit secrets, candidate submissions, environments or `artifacts/`.
- Mark a deliberate scope ceiling with a short `ponytail:` comment and its upgrade path when code relies on that ceiling.
