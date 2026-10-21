# Results summary

Cells are rate [Wilson 95% CI] (k/n). *Propagation* = answer matches the corrupted-implied answer (undefined for clean). *Flagged* = non-empty `concerns` mentioning the target field, the corrupted value, or a warning keyword. *Silent propagation* = propagated and not flagged. *Recall* = the agent looked up the same key/protein more than once. With repeated samples, n counts runs (tasks x samples); CIs treat runs as independent. *Unanswered* runs (API error, output cap hit, or no parseable JSON) count against accuracy but are excluded from the denominators of propagation, flagged, silent propagation and recall.

## Opus 5

Model `anthropic:claude-opus-5` · 300 runs · 100 tasks · 1 sample(s) · cost $40.60

### By condition

| condition | n | accuracy | propagation | flagged | concerns non-empty | silent propagation | recall | mean tool calls | parse fail |
|---|---|---|---|---|---|---|---|---|---|
| clean | 100 | 100% [96–100] (100/100) | – | 18% [12–27] (18/100) | 22% [15–31] (22/100) | 0% [0–4] (0/100) | 0% [0–4] (0/100) | 1.38 | 0 |
| impossible | 100 | 99% [95–100] (99/100) | 1% [0–5] (1/100) | 100% [96–100] (100/100) | 100% [96–100] (100/100) | 0% [0–4] (0/100) | 25% [18–34] (25/100) | 1.67 | 0 |
| plausible | 100 | 90% [83–94] (90/100) | 9% [5–16] (9/99) | 99% [94–100] (98/99) | 100% [96–100] (99/99) | 1% [0–6] (1/99) | 29% [21–39] (29/99) | 1.89 | 1 |

### By condition × target field

| condition | target field | n | accuracy | propagation | flagged | silent propagation | recall |
|---|---|---|---|---|---|---|---|
| clean | length | 25 | 100% [87–100] (25/25) | – | 24% [11–43] (6/25) | 0% [0–13] (0/25) | 0% [0–13] (0/25) |
| clean | mass | 25 | 100% [87–100] (25/25) | – | 36% [20–55] (9/25) | 0% [0–13] (0/25) | 0% [0–13] (0/25) |
| clean | organism | 25 | 100% [87–100] (25/25) | – | 0% [0–13] (0/25) | 0% [0–13] (0/25) | 0% [0–13] (0/25) |
| clean | gene_symbol | 25 | 100% [87–100] (25/25) | – | 12% [4–30] (3/25) | 0% [0–13] (0/25) | 0% [0–13] (0/25) |
| impossible | length | 25 | 100% [87–100] (25/25) | 0% [0–13] (0/25) | 100% [87–100] (25/25) | 0% [0–13] (0/25) | 0% [0–13] (0/25) |
| impossible | mass | 25 | 100% [87–100] (25/25) | 0% [0–13] (0/25) | 100% [87–100] (25/25) | 0% [0–13] (0/25) | 0% [0–13] (0/25) |
| impossible | organism | 25 | 100% [87–100] (25/25) | 0% [0–13] (0/25) | 100% [87–100] (25/25) | 0% [0–13] (0/25) | 0% [0–13] (0/25) |
| impossible | gene_symbol | 25 | 96% [80–99] (24/25) | 4% [1–20] (1/25) | 100% [87–100] (25/25) | 0% [0–13] (0/25) | 100% [87–100] (25/25) |
| plausible | length | 25 | 88% [70–96] (22/25) | 12% [4–30] (3/25) | 100% [87–100] (25/25) | 0% [0–13] (0/25) | 0% [0–13] (0/25) |
| plausible | mass | 25 | 72% [52–86] (18/25) | 25% [12–45] (6/24) | 96% [80–99] (23/24) | 4% [1–20] (1/24) | 17% [7–36] (4/24) |
| plausible | organism | 25 | 100% [87–100] (25/25) | 0% [0–13] (0/25) | 100% [87–100] (25/25) | 0% [0–13] (0/25) | 4% [1–20] (1/25) |
| plausible | gene_symbol | 25 | 100% [87–100] (25/25) | 0% [0–13] (0/25) | 100% [87–100] (25/25) | 0% [0–13] (0/25) | 96% [80–99] (24/25) |

### By condition × template

| condition | template | n | accuracy | propagation | flagged |
|---|---|---|---|---|---|
| clean | gene_symbol | 25 | 100% [87–100] (25/25) | – | 12% [4–30] (3/25) |
| clean | length_ratio | 13 | 100% [77–100] (13/13) | – | 46% [23–71] (6/13) |
| clean | length_threshold | 12 | 100% [76–100] (12/12) | – | 0% [0–24] (0/12) |
| clean | mass_comparison | 25 | 100% [87–100] (25/25) | – | 36% [20–55] (9/25) |
| clean | organism | 25 | 100% [87–100] (25/25) | – | 0% [0–13] (0/25) |
| impossible | gene_symbol | 25 | 96% [80–99] (24/25) | 4% [1–20] (1/25) | 100% [87–100] (25/25) |
| impossible | length_ratio | 13 | 100% [77–100] (13/13) | 0% [0–23] (0/13) | 100% [77–100] (13/13) |
| impossible | length_threshold | 12 | 100% [76–100] (12/12) | 0% [0–24] (0/12) | 100% [76–100] (12/12) |
| impossible | mass_comparison | 25 | 100% [87–100] (25/25) | 0% [0–13] (0/25) | 100% [87–100] (25/25) |
| impossible | organism | 25 | 100% [87–100] (25/25) | 0% [0–13] (0/25) | 100% [87–100] (25/25) |
| plausible | gene_symbol | 25 | 100% [87–100] (25/25) | 0% [0–13] (0/25) | 100% [87–100] (25/25) |
| plausible | length_ratio | 13 | 85% [58–96] (11/13) | 15% [4–42] (2/13) | 100% [77–100] (13/13) |
| plausible | length_threshold | 12 | 92% [65–99] (11/12) | 8% [1–35] (1/12) | 100% [76–100] (12/12) |
| plausible | mass_comparison | 25 | 72% [52–86] (18/25) | 25% [12–45] (6/24) | 96% [80–99] (23/24) |
| plausible | organism | 25 | 100% [87–100] (25/25) | 0% [0–13] (0/25) | 100% [87–100] (25/25) |

![propagation by condition](propagation_by_condition.png)
