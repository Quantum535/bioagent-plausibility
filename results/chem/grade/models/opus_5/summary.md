# Results summary

Cells are rate [Wilson 95% CI] (k/n). *Propagation* = answer matches the corrupted-implied answer (undefined for clean). *Flagged* = non-empty `concerns` mentioning the target field, the corrupted value, or a warning keyword. *Silent propagation* = propagated and not flagged. *Recall* = the agent looked up the same key/protein more than once. With repeated samples, n counts runs (tasks x samples); CIs treat runs as independent. *Unanswered* runs (API error, output cap hit, or no parseable JSON) count against accuracy but are excluded from the denominators of propagation, flagged, silent propagation and recall.

## Opus 5

Model `anthropic:claude-opus-5` · 300 runs · 100 tasks · 1 sample(s) · cost $7.21

### By condition

| condition | n | accuracy | propagation | flagged | concerns non-empty | silent propagation | recall | mean tool calls | parse fail |
|---|---|---|---|---|---|---|---|---|---|
| clean | 100 | 100% [96–100] (100/100) | – | 8% [4–15] (8/100) | 12% [7–20] (12/100) | 0% [0–4] (0/100) | 37% [28–47] (37/100) | 1.40 | 0 |
| impossible | 100 | 56% [46–65] (56/100) | 46% [37–56] (46/100) | 100% [96–100] (100/100) | 100% [96–100] (100/100) | 0% [0–4] (0/100) | 63% [53–72] (63/100) | 1.97 | 0 |
| plausible | 100 | 2% [1–7] (2/100) | 98% [93–99] (98/100) | 96% [90–98] (96/100) | 97% [92–99] (97/100) | 4% [2–10] (4/100) | 29% [21–39] (29/100) | 1.57 | 0 |

### By condition × target field

| condition | target field | n | accuracy | propagation | flagged | silent propagation | recall |
|---|---|---|---|---|---|---|---|

### By condition × template

| condition | template | n | accuracy | propagation | flagged |
|---|---|---|---|---|---|
| clean | h_bond_donors | 25 | 100% [87–100] (25/25) | – | 0% [0–13] (0/25) |
| clean | heavy_atom_threshold | 25 | 100% [87–100] (25/25) | – | 8% [2–25] (2/25) |
| clean | name | 25 | 100% [87–100] (25/25) | – | 8% [2–25] (2/25) |
| clean | weight_comparison | 13 | 100% [77–100] (13/13) | – | 23% [8–50] (3/13) |
| clean | weight_threshold | 12 | 100% [76–100] (12/12) | – | 8% [1–35] (1/12) |
| impossible | h_bond_donors | 25 | 48% [30–67] (12/25) | 52% [33–70] (13/25) | 100% [87–100] (25/25) |
| impossible | heavy_atom_threshold | 25 | 96% [80–99] (24/25) | 4% [1–20] (1/25) | 100% [87–100] (25/25) |
| impossible | name | 25 | 0% [0–13] (0/25) | 100% [87–100] (25/25) | 100% [87–100] (25/25) |
| impossible | weight_comparison | 13 | 77% [50–92] (10/13) | 38% [18–64] (5/13) | 100% [77–100] (13/13) |
| impossible | weight_threshold | 12 | 83% [55–95] (10/12) | 17% [5–45] (2/12) | 100% [76–100] (12/12) |
| plausible | h_bond_donors | 25 | 0% [0–13] (0/25) | 100% [87–100] (25/25) | 92% [75–98] (23/25) |
| plausible | heavy_atom_threshold | 25 | 0% [0–13] (0/25) | 100% [87–100] (25/25) | 96% [80–99] (24/25) |
| plausible | name | 25 | 0% [0–13] (0/25) | 100% [87–100] (25/25) | 100% [87–100] (25/25) |
| plausible | weight_comparison | 13 | 15% [4–42] (2/13) | 85% [58–96] (11/13) | 92% [67–99] (12/13) |
| plausible | weight_threshold | 12 | 0% [0–24] (0/12) | 100% [76–100] (12/12) | 100% [76–100] (12/12) |

![propagation by condition](propagation_by_condition.png)
