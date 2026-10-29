"""Phase 4 pre-registration: numeric predictions for monoisotopic mass from the Phase 1 chemistry boundary curves at the
factors actually used in the Phase 4 tasks, plus hypotheses and analysis plan. Writes results/phase4/PREREGISTRATION.md."""
import re, math, json, datetime, subprocess
from pathlib import Path
fits = {}
for line in open("results/boundary/fits.txt"):
    m = re.match(r"^(\w+)\s+chem\s+(shrink|inflate)\s+(.*)$", line.strip())
    if m: fits[(m.group(1), m.group(2))] = {float(a): int(b) / 100 for a, b in re.findall(r"×([\d.]+):\s*(\d+)%", m.group(3))}
def interp(curve, f):
    pts = sorted(curve.items(), key=lambda kv: math.log(kv[0])); lf = math.log(f)
    if lf <= math.log(pts[0][0]): return pts[0][1]
    if lf >= math.log(pts[-1][0]): return pts[-1][1]
    for (a, pa), (b, pb) in zip(pts, pts[1:]):
        if math.log(a) <= lf <= math.log(b): return pa + (lf - math.log(a)) / (math.log(b) - math.log(a)) * (pb - pa)
tasks = json.load(open("data/chem/phase4_tasks.json"))["tasks"]
mono = {d: [t["corruptions"]["plausible"]["factor"] for t in tasks if t["target_field"] == "monoisotopic_mass" and t["direction"] == d] for d in ("shrink", "inflate")}
MODELS = {"opus5": "Opus 5", "argon": "Gemini 4 Argon", "flash": "Gemini 3.8 Flash", "deepseek": "DeepSeek V4.1 Flash", "sonnet5": "Sonnet 5"}
rows, pred = [], {}
for k, label in MODELS.items():
    for d in ("shrink", "inflate"):
        p = sum(interp(fits[(k, d)], f) for f in mono[d]) / len(mono[d]); pv = min(max(p, 0.02), 0.98)
        hw = 1.96 * math.sqrt(pv * (1 - pv) * (1 / len(mono[d]) + 1 / 40)); lo, hi = max(0, p - hw), min(1, p + hw)
        pred[f"{k}|{d}"] = [round(p, 3), round(lo, 3), round(hi, 3)]
        rows.append(f"| {label} | {d} | {100 * p:.0f}% | [{100 * lo:.0f}%, {100 * hi:.0f}%] |")
Path("results/phase4").mkdir(parents=True, exist_ok=True)
json.dump(pred, open("results/phase4/predictions_mono.json", "w"), indent=1)
fs, fi = sorted(set(mono["shrink"])), sorted(set(mono["inflate"]))
h = subprocess.run(["git", "log", "-1", "--format=%h", "--", "fetch_phase4_fields.py"], capture_output=True, text=True).stdout.strip()
table = "\n".join(rows)
doc = f"""# Phase 4 pre-registration: does a field's derivation route predict whether agents relay a corrupted value?

Written {datetime.date.today()} before any Phase 4 model outcome was inspected. A 36-run cost-only pilot (6 tasks, clean and
plausible, full record, Opus 5 / Argon / DeepSeek) was run to price the study; only its cost line was read. Its clean runs are
reused from cache; its plausible runs are excluded (a cache-key fix now hashes the corruption payload, so they are re-run).

## Background
In the benchmark, corrupted values were corrected only when the record offered a derivation route (sequence to length and mass,
formula to weight). Phase 4 tests that claim out of sample on three chemistry fields never used before, whose route class was
fixed from data before any model run (fetch_phase4_fields.py, commit {h}):
- Monoisotopic mass, exact route: RDKit reproduces PubChem from the record's formula/SMILES for 300/300 compounds (within 0.001 Da).
- TPSA, approximate route: RDKit (S and P included) within 0.1 square angstroms for 80% of compounds, Spearman 0.996.
- PubChem complexity, no route: the closest RDKit analogue (Bertz CT) agrees for 1.7% of compounds; rank correlation only (0.936).

## Design
180 threshold questions ("Does the compound with PubChem CID X have a [field] greater than T?"), 30 per field x direction,
one distinct compound per task (data/chem/phase4_tasks.json; make_phase4_tasks.py, seed 4). T lies midway between the true
and the plausibly corrupted value, so a relayed corruption flips the answer.
Conditions: clean; plausible (value x factor; shrink {fs}, inflate {fi}); impossible (0 or negative, or absurdly large).
Monoisotopic mass is corrupted together with molecular weight and heavy-atom count, so the formula and SMILES are the only
contradiction, as in the Phase 1 boundary experiment.
Formats: full record (formula and SMILES present, the route) and summary record (neither present, no route for any field).
Models: Opus 5, Sonnet 5, Gemini 4 Argon, Gemini 3.8 Flash, DeepSeek V4.1 Flash. One sample per task x condition x format x
model (5,400 runs). Outcome: propagated = the parsed answer equals the answer implied by the corrupted record.

## Hypotheses
H1 (route ordering). In full-record plausible runs, propagation increases with route class: monoisotopic mass < TPSA < complexity.
Primary test: logistic regression, propagated ~ route rank (0, 1, 2) + model + direction, on full-record plausible runs of
Opus 5, Argon, Flash and DeepSeek; one-sided Wald test that the route-rank coefficient is > 0, alpha = 0.05. Sonnet 5 is
excluded from H1 in advance: its Phase 1 chemistry curve predicts ceiling propagation even for the exact-route field (H2),
leaving no room for an ordering. Secondary: per-model one-sided Fisher exact tests (mono < TPSA; TPSA < complexity),
Holm-corrected across the 8 tests.

H2 (quantitative transfer). Monoisotopic-mass propagation in full-record plausible runs falls inside the prediction interval
derived from each model's Phase 1 chemistry molecular-weight curve at the factors used here (log-linear interpolation; the
interval combines binomial error from n = 30 new tasks and n = 40 Phase 1 tasks per point). Supported if at least 8 of the
10 model x direction cells fall inside their interval.

H3 (the route is what matters). The route-rank effect is larger with the full record than with the summary record: in a
logistic regression on plausible runs of both formats (same four models), the route rank x full-format interaction is
positive (one-sided, alpha = 0.05).

## Predictions for monoisotopic mass (H2)
| Model | Direction | Predicted propagation | 95% prediction interval |
|---|---|---|---|
{table}

Also expected, not formally tested: complexity propagates at summary-plausible levels (90% or more) in both formats, and TPSA
falls between the other two fields.

## Exclusions
Runs that fail at the API are retried until they succeed; persistent failures are excluded and counted. Runs with no
parseable answer are excluded from propagation rates and reported per cell. If clean accuracy for any model x field x format
is below 80%, that cell is reported as a task problem and excluded from H1 to H3.

## Exploratory, not tested
The impossible condition; flagged-yet-propagated rates; shrink vs inflate asymmetry; comparison with Phase 3 coherent corruption.
"""
Path("results/phase4/PREREGISTRATION.md").write_text(doc); print(doc)
