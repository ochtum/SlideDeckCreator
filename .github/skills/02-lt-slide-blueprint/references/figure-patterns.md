# Figure patterns

| Content shape | Pattern | Preferred visual |
|---|---|---|
| Definition plus example | definition | short definition, one example, one boundary |
| Cause to effect | causal | labeled causal flow, not an unlabeled arrow |
| A vs B | comparison | split cards plus connector |
| Several options on shared criteria | comparison-table | HTML table with shared axes |
| Before to After | transformation | two states plus arrow |
| Step 1..4 | process | horizontal or vertical flow |
| Ordered interaction | sequence | lanes or ordered nodes with messages |
| Three methods | options | three icon cards |
| Percentage or count | metric | large number plus one supporting mark |
| Whole system | architecture | boxes and arrows |
| Parent and children | hierarchy | tree or layer diagram |
| Conditional choice | decision | decision table or flowchart |
| Two axes | matrix | 2x2 matrix with one highlighted quadrant |
| Pros and cons | balance | two columns with neutral center |
| Timeline | timeline | line plus 3 to 5 milestones |
| Numeric trend | chart | HTML/SVG line, bar, or dot chart with labeled axes |
| Real-world application | case-study | situation, action, observation, decision |
| Exact exception or condition | caution | short prose or callout, not a forced diagram |
| One strong claim | statement | typography only or one symbolic image |

Use `generated-image` for a memorable metaphor, conceptual transformation, or custom illustration. Use `inline-svg` or `css-component` for exact flows, matrices, charts, and comparisons. Generated images must not contain essential labels; HTML owns all readable text.

Record `representation_reason`, the source `knowledge_unit_ids`, and any `accuracy_constraints`. Prefer existing `flow` with `variant: process|causal|sequence|decision` and `comparison` with `variant: split|table|matrix` before inventing a new renderer. Use `hierarchy`, `timeline`, `chart`, or `case-study` only when their data shape is materially different.
