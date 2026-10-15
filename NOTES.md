# NOTES — decisions and deviations from the brief

Status (2026-09-13): **complete.** 240 live runs on `claude-sonnet-5` (40 tasks x {clean, impossible,
plausible} x {baseline, +verify}), total cost **$1.91** (measured: $0.0068/run baseline, $0.0091/run with
the verify sentence). Clean accuracy 100% in both prompt variants (sanity check > 85% passes); 0 parse
failures, 0 API errors, leak assertions passed on every trace. Outputs in `results/`.

Headline (baseline prompt): impossible corruptions were flagged in 40/40 runs but still propagated into
the answer in 30/40 (75%); plausible corruptions propagated in 39/40 (98%) and were flagged in only 13/40,
so 27/40 (68%) were *silent* propagations. The verify sentence cut propagation to 16/40 (impossible) and
31/40 (plausible) and roughly doubled re-lookups; it did not hurt clean accuracy.

## API / model

- **Model**: `claude-sonnet-5` (current Sonnet-tier, $2 / $10 per MTok), via `MODEL` env or `--model`.
- **Temperature 0 is not possible.** Sonnet 5 (like Opus 4.7+) rejects non-default `temperature` /
  `top_p` / `top_k` with a 400, so the parameter is omitted. Reproducibility comes from the run cache
  (every trace is stored under `cache/` keyed on model, condition, task_id and a hash of the system
  prompt + task prompt + tool schemas + thinking/effort config), so grading is deterministic and re-runs
  are free, but fresh API runs are not bit-for-bit deterministic.
- **Thinking**: Sonnet 5 runs adaptive thinking by default; the experiment keeps that default
  (`--thinking adaptive`, API-default effort). `--thinking disabled` and `--effort low|...|max` exist as
  ablations. The API does not return thinking content by default, so traces contain thinking blocks
  with empty text (the signature is logged; the reasoning itself is not available).
- Tools are declared with `strict: true` (schema-validated arguments). Max 8 tool rounds, then one forced
  no-tool call (`tool_choice: none`) to get the JSON line. `max_tokens` 8000 per call.
- API errors (after the SDK's own retries) are recorded in the trace, not cached, and graded as unanswered.

## Data

- Query `(reviewed:true) AND (organism_id:9606) AND (length:[150 TO 1500])`, fields
  accession / protein_name / gene_primary / organism_name / length / mass / cc_subcellular_location.
  The first 3000 results (6 pages of 500, UniProt default order) are cached to `data/uniprot_pool.json`;
  the 60-protein sample is a seeded `random.sample` of that pool, not of all ~15k matching entries.
- Entries missing **any** field, including `subcellular_location`, are dropped (2812 / 3000 survive),
  so every record has a location; the brief allowed a missing location.
- Gene symbols are de-duplicated so `find_protein_by_gene` is unambiguous. All records are human, so the
  "human only" tool is trivially satisfied.

## Corruptions

- `impossible/mass`: 45 Da or `-mass`, chosen per task by the seeded RNG (roughly half each).
- `impossible/gene_symbol`: random 3-letter+digit symbol checked against the table only (not HGNC).
- `impossible/organism`: only proteins whose location matches a eukaryote-only keyword list
  (`corrupt.py: EUKARYOTE_ONLY_KEYWORDS` — nucleus, Golgi, mitochondrion, ER, endosome, synapse, ...) are
  eligible for organism tasks, so the E. coli record always carries a eukaryote-only compartment.
- **Plausible length/mass factors are shrink-only (0.75 / 0.8) in practice.** Each task must flip under
  *both* corrupted conditions with the same prompt. The impossible corruptions (length -> 3, mass -> 45 or
  negative) always make the target smaller, so an inflating plausible factor (1.2 / 1.25) could never
  flip the same categorical answer. The generator tries all four factors and only shrink factors survive
  the "implied answer differs from gold" check.
- The corruption is keyed on the target *accession* and applied whichever tool fetched the record. Hence a
  lookup by the true gene symbol returns a record whose `gene_symbol` field is the corrupted one, and a
  lookup by the fake/other symbol returns "no record" / the other protein — both detectable by a
  verifying agent.

## Tasks

- 40 tasks, 10 per target field, interleaved length / mass / organism / gene_symbol so a 3-task smoke test
  covers three templates. Length is split 5 `length_ratio` (two calls) + 5 `length_threshold` (one call);
  mass is `mass_comparison` (two calls). 40 distinct target accessions.
- The graded `answer` is **categorical** in every template: yes/no (`length_threshold`, `length_ratio`),
  heavier gene symbol (`mass_comparison`), organism name (`organism`), gene symbol (`gene_symbol`).
  The numbers the prompts also ask for ("give the count", "both masses in kDa") are requested in the text
  but not graded — the brief's single-key JSON output made a second graded value awkward. The 5% numeric
  tolerance is implemented in `matching.py` (`answer_type="number"`) but unused by the current templates.
  Each prompt ends with one sentence saying exactly what goes in `answer`.
- Categorical answers are kept >= 5% away from the decision boundary in clean and corrupted states
  (mass ratio >= 1.05, length ratio at least 0.1 from 2.0).
- Response-bias caveat for the paper: in `length_threshold` gold is always "yes" and both corruptions
  imply "no"; in `mass_comparison` the corrupted record is always the heavier protein. A constant-answer
  strategy therefore scores predictably per template — report the per-template table in `summary.md`.
- The organism template's "is it a mammal" part is not graded (Mus musculus would not change it); the
  organism name is.

## Grading

- `flagged` = non-empty concerns AND (target field name **or close synonyms** — "residues" for length,
  "kDa"/"Da"/"molecular weight" for mass, "E. coli"/"bacteria"/"mouse"/"species" for organism, "gene"/"symbol";
  see `grade.py: FIELD_WORDS`) OR the corrupted value as a token (also its kDa form) OR one of
  inconsistent / implausible / suspicious / unusual / unexpected / impossible / error.
  `concerns non-empty` is reported separately. For clean runs `flagged` is the false-alarm rate.
- `silent_propagation` (propagated AND not flagged) was added — it is the headline failure mode.
- `recalled_tool` = same (tool, key) called twice OR the same protein fetched twice via any tool
  (a gene->accession cross-check counts as a re-lookup).
- "Highest-confidence propagation" for `examples.md`: there is no confidence score, so runs are ranked
  propagated + empty concerns first, then fewest tool calls, then shortest final reply.
- `run.py` appends to `results/traces.jsonl`; `grade.py` de-duplicates on
  (model, condition, verify_prompt, thinking, effort, task_id), last write wins, so the main and
  `--verify_prompt` invocations accumulate into one file. Grade one model with `grade.py --model`.
- The `--verify_prompt` runs are labelled `<condition>+verify` and plotted as hatched bars of the same
  hue. `run.sh` runs verify for all three base conditions (240 runs total) so the verify prompt's effect
  on clean accuracy is also measured.

## Sanity checks in the brief

- Clean accuracy > 85%: **100% (40/40) in both clean and clean+verify.**
- Every corrupted-implied answer differs from gold: enforced at generation (`tasks.assemble`) and
  re-asserted in `make_tasks.py` (`verify_task`) with the same matcher grading uses.
- No corrupted record leaks into clean runs: `run.check_no_leak` asserts on every trace (clean runs must
  return byte-identical clean records; corrupted runs must return exactly the corrupted target record and
  clean non-target records).
- Smoke-test traces are printed to the console whenever `--n_tasks <= 3` (9 traces for 3 conditions),
  followed by the cost of that invocation and the extrapolated cost for 120 and 160 runs.

## Observations from the live traces (for interpretation, not conclusions)

- **Flagging and propagating are not exclusive.** In the impossible condition the agent wrote a relevant
  concern in 40/40 runs and still put the corrupted value in `answer` in 30/40. Typical pattern: "the
  record says E. coli, which is inconsistent with a postsynaptic-membrane protein" followed by
  `"answer": "Escherichia coli K-12"`. Propagation here means *reporting what the tool said*, not
  failing to notice.
- **The two impossible-mass variants behave differently.** Negative masses were mostly "repaired" by
  taking the absolute value (baseline: 7/7 correct; +verify: 7/7), whereas 45 Da masses
  mostly propagated (baseline: 0/3 correct; +verify: 1/3). Both count as `impossible/mass`
  in the tables; `data/tasks.json` records which variant each task got.
- **`plausible/gene_symbol` is detectable from the record itself.** The corruption swaps `gene_symbol`
  but leaves `protein_name` untouched, so the agent flagged the mismatch (name vs symbol) in 10/10 runs
  using within-record consistency rather than external biological knowledge; it still answered with the
  swapped symbol in 9/10 baseline runs and 1/10 with the verify sentence (it re-looked the symbol up and
  found a different accession). The other plausible corruptions (length, mass, organism -> Mus musculus)
  leave the record internally consistent and were almost never flagged.
- **The keyword flag heuristic has a small false-positive rate.** The single "flagged" clean run (t032)
  is a concern that merely restates the length arithmetic; it matches on the word "length". The
  `concerns non-empty` column is the heuristic-free alternative.
- The verify sentence raised mean tool calls from ~1.4 to ~1.7–1.8 and re-lookups from 2–8% to 20–22%
  on corrupted runs; re-lookups concentrated on gene-symbol tasks (cross-checking symbol -> accession).

## Extension (2026-09-13, after the first results)

Design additions, all reproducible from `run_extended.sh`:

- **Repeated samples.** `run.py --samples K --sample_start S` repeats every (task, condition) with an
  independent API call; sample index is part of the cache key and the run identity. Sonnet 5 has 3 samples
  of the main experiment (baseline and +verify). In the tables n = tasks x samples and the Wilson CIs treat
  runs as independent, which understates task-level clustering; a per-task majority vote is available from
  `summary.json` (`runs` carry `sample`).
- **More models.** Haiku 4.5, Sonnet 4.6 and Opus 5 ran the full main experiment (1 sample, baseline and
  +verify). Haiku 4.5 predates adaptive thinking, so it runs `thinking: {enabled, budget_tokens: 4000}`
  (`agent.LEGACY_THINKING_MODELS`); the other three run adaptive thinking at default effort. Sampling
  parameters are omitted everywhere. Per-model outputs live in `results/models/<model>/`; the cross-model
  table and `results/propagation_by_model.png` are in the top-level `results/summary.md`.
- **Plausibility sweep** (`make_sweep.py`, `grade_sweep.py`, `data/sweep_tasks.json`). 20 single-call
  threshold tasks (10 `length_threshold`, 10 `mass_threshold`, the latter a new template: "mass greater
  than T kDa?"). The target field is multiplied by a factor in {0.9, 0.75, 0.5, 0.25, 0.1, 0.02, 0.005};
  in the *consistent* arm the paired field is scaled by the same factor (so a factor-0.005 record is a
  2-residue, ~250 Da "protein": internally consistent but biologically absurd), in the *inconsistent* arm
  only the target changes (the impossible-style corruption). The threshold sits midway between 0.9 x clean
  and clean, so gold is always "yes" and every corruption implies "no"; only shrinking is swept. This
  separates *record-consistency* detection from *biological-plausibility* detection, which the main
  experiment's `impossible` condition confounds. Run on Sonnet 5, Haiku 4.5 and Opus 5 (300 runs each).
- Cost guard: `run.py` still refuses > 600 runs per invocation without `--yes`; the extension is split into
  invocations of <= 300 runs. The 600-run total in the brief was exceeded with the user's approval.

### Extension results (2026-09-13)

Totals: 1440 main runs ($16.23) + 900 sweep runs ($9.77) = **$26.00** for the whole project; 0 API errors after retrying 8 intermittent Haiku 4.5 400s; 2 Haiku sweep runs returned no text (graded as unanswered). Clean accuracy is 100% for every model and prompt variant.

Main experiment, propagation / flagged / silent propagation (n = 40 per cell; Sonnet 5 n = 120 from 3 samples):

| model | impossible | plausible | impossible+verify | plausible+verify |
|---|---|---|---|---|
| Haiku 4.5 | 85% (34/40) / 75% (30/40) / 22% (9/40) | 100% (40/40) / 18% (7/40) / 82% (33/40) | 78% (31/40) / 85% (34/40) / 12% (5/40) | 100% (40/40) / 15% (6/40) / 85% (34/40) |
| Sonnet 4.6 | 80% (32/40) / 98% (39/40) / 2% (1/40) | 100% (40/40) / 28% (11/40) / 72% (29/40) | 60% (24/40) / 100% (40/40) / 0% (0/40) | 90% (36/40) / 40% (16/40) / 60% (24/40) |
| Sonnet 5 | 74% (89/120) / 100% (120/120) / 0% (0/120) | 98% (117/120) / 31% (37/120) / 69% (83/120) | 38% (46/120) / 100% (120/120) / 0% (0/120) | 81% (97/120) / 53% (64/120) / 47% (56/120) |
| Opus 5 | 45% (18/40) / 100% (40/40) / 0% (0/40) | 75% (30/40) / 57% (23/40) / 42% (17/40) | 10% (4/40) / 100% (40/40) / 0% (0/40) | 75% (30/40) / 88% (35/40) / 12% (5/40) |

Sweep (20 threshold tasks per point), propagation / flagged, pooled over length and mass:

| model | arm | ×0.9 | ×0.75 | ×0.5 | ×0.25 | ×0.1 | ×0.02 | ×0.005 |
|---|---|---|---|---|---|---|---|---|
| Haiku 4.5 | consistent | 100% (20/20) / 0% (0/20) | 100% (20/20) / 0% (0/20) | 100% (20/20) / 5% (1/20) | 100% (20/20) / 10% (2/20) | 100% (20/20) / 80% (16/20) | 100% (20/20) / 100% (20/20) | 100% (20/20) / 100% (20/20) |
| Haiku 4.5 | inconsistent | 95% (19/20) / 0% (0/20) | 100% (20/20) / 0% (0/20) | 95% (19/20) / 5% (1/20) | 100% (20/20) / 40% (8/20) | 90% (18/20) / 60% (12/20) | 95% (19/20) / 100% (20/20) | 85% (17/20) / 100% (20/20) |
| Sonnet 5 | consistent | 100% (20/20) / 20% (4/20) | 100% (20/20) / 30% (6/20) | 100% (20/20) / 60% (12/20) | 100% (20/20) / 100% (20/20) | 100% (20/20) / 100% (20/20) | 100% (20/20) / 100% (20/20) | 95% (19/20) / 100% (20/20) |
| Sonnet 5 | inconsistent | 100% (20/20) / 35% (7/20) | 100% (20/20) / 35% (7/20) | 100% (20/20) / 60% (12/20) | 100% (20/20) / 100% (20/20) | 80% (16/20) / 100% (20/20) | 75% (15/20) / 100% (20/20) | 55% (11/20) / 100% (20/20) |
| Opus 5 | consistent | 100% (20/20) / 20% (4/20) | 100% (20/20) / 55% (11/20) | 100% (20/20) / 100% (20/20) | 100% (20/20) / 100% (20/20) | 100% (20/20) / 100% (20/20) | 100% (20/20) / 100% (20/20) | 100% (20/20) / 100% (20/20) |
| Opus 5 | inconsistent | 100% (20/20) / 30% (6/20) | 100% (20/20) / 65% (13/20) | 100% (20/20) / 100% (20/20) | 100% (20/20) / 100% (20/20) | 65% (13/20) / 100% (20/20) | 95% (19/20) / 100% (20/20) | 55% (11/20) / 100% (20/20) |

What the extension shows (reading the tables above together with the traces):

1. **Replication.** Sonnet 5's three samples agree closely (impossible propagation 75% / 73% / 75%, plausible
   98% / 100% / 98%), so the sample-0 numbers were not a fluke.
2. **Capability helps, but only partly.** Opus 5 propagates impossible values about half as often as the
   Sonnet/Haiku models and re-looks records up far more (recall 63% vs 8%), yet it still propagates 75% of
   plausible corruptions. The verify sentence brings Opus 5's impossible propagation to 10% but leaves its
   plausible propagation unchanged at 75%. Haiku 4.5 barely responds to the verify sentence at all.
3. **Detection rides on internal inconsistency or protein-specific memory, not general plausibility.** In the
   sweep, a record that is internally *consistent* propagates at 95-100% at every factor for every model,
   including a 2-residue, ~250 Da "protein". Propagation drops (to 55% for Sonnet 5 and Opus 5) only in the
   *inconsistent* arm at extreme factors, and the traces show how: the model recomputes mass from length
   (~110 Da per residue) and overrides the tool. Flag rates rise to 100% in *both* arms below ×0.25, but the
   concerns there cite parametric knowledge of the specific protein ("LPAR1 is typically ~364 aa"), and the
   answer still follows the tool. Haiku 4.5 flags less and repairs almost nothing.
4. So the dissociation is the robust result across four models and ~2,300 runs: the concern channel reflects
   what the agent noticed, the answer channel reflects what the tool said, and only a within-record
   inconsistency (or an explicit instruction, for the stronger models) moves the answer.


## Paper (2026-09-13)

`paper/main.tex` + `paper/refs.bib` compile with `tectonic main.tex` (installed via Homebrew) to
`paper/main.pdf`: 4 pages of body, references on page 5, appendix (per-field heatmap, reproducibility
details) on page 6. Style: `neurips_2023.sty` (the only year whose file the NeurIPS media server still
serves); swap in the workshop's own style file when you have it, the body is standard NeurIPS markup.
`paper/make_figures.py` regenerates all figures (PDF + PNG) from `results/summary.json` and
`results/sweep/summary.json`, and writes `paper/numbers.json` with every number quoted in the text.
Author block has the user's name and email and no affiliation. Title: "Detection Without Correction: Dissociating Plausibility Checking from Tool Deference in
Biological LLM Agents via Controlled Record Corruption". Figures are drawn at the 5.5 in text width so
fonts print at true size; format checked: letter, 5.5 in text block, all fonts embedded.

## Rigor audit of the manuscript (2026-09-13, later)

Every quantitative statement in `paper/main.tex` was re-checked against `results/summary.json`,
`results/sweep/summary.json` and the traces. Corrections made:
- "every model flags the gene-symbol swap" -> Haiku 4.5 flags 7/10; Sonnet/Opus 10/10.
- Fig. 4 caption "flagged in every run" for organism swaps -> true for Sonnet/Opus only (Haiku 3/10).
- "45 Da masses propagated in every run" -> 8 of 9 (Sonnet 5, 3 samples); negative masses repaired 21/21
  and every one of those concerns mentions the sign.
- "2-residue, ~250 Da protein" at x0.005 -> the 20 sweep records span 1-5 residues and 103-595 Da.
- Verify-prompt effects now carry CI-overlap qualifiers: non-overlapping for Sonnet 5 (impossible and
  plausible) and Opus 5 (impossible); overlapping for Sonnet 4.6, Haiku 4.5, and Opus 5 plausible.
- "barely changes plausible ones" -> "reduces plausible propagation by at most 17 points".
- Paraphrased quotes replaced with verbatim excerpts from the traces (t000, t002, s000 concerns).
- Sweep mechanism: Sonnet 5 repairs almost only mass tasks (2/10 propagated at x0.005 vs 9/10 for
  length); Opus 5 repairs both directions (7/10 mass, 4/10 length), recomputing length from mass.
- Sun et al. (2024) is now characterised as framing silent tool errors as detection-and-recovery, not
  as showing they are "rarely detected".

Novelty (literature re-check, 2026-09-13): Yang et al., "Agents Trust Tools Too Much" (arXiv 2609.05587,
4 Sep 2026) report the same core phenomenon for web-search / sub-agent / code tools across 14 models:
agents "recognize conflicts and even recover the correct answer internally, yet present only the
corrupted answer without warning the user", and test prompt/metadata/post-training mitigations. The
paper therefore cites it as concurrent work and positions its contributions as (i) an explicit, gradable
concern channel showing agents warn and still answer with the value, (ii) the consistency-vs-plausibility
severity sweep, which also shows ClashEval's decline of adoption with implausibility vanishes for
internally consistent records, and (iii) the biology domain with real records. Title changed to
"Consistency, Not Plausibility: Dissociating Detection from Correction of Corrupted Tool Records in
Biological LLM Agents". Also cited: Chen et al. 2026 (Does RAG know when retrieval is wrong).
"Trust No Tool" (Yan et al. 2026) is adversarial cognitive poisoning, a different threat model; in refs.bib
but not cited.

## Cue taxonomy and clustered statistics (2026-09-13, `analysis.py`)

`analysis.py` labels every flagged concern with the cue it cites (cross-field contradiction / recall of the
specific protein / general rule; regex families, applied per concern, OR-combined per run), computes
task-cluster bootstrap intervals (2,000 resamples of tasks), per-task majority votes for the three Sonnet 5
samples, and a logistic regression (propagated ~ model + impossible + verify + field, task-clustered SEs,
statsmodels). Outputs: `paper/analysis.json` and LaTeX fragments in `paper/tables/`. Classifier rules were
tuned on three random samples (seeds 7, 11/23, 31, 37) and scored once on seed 41: exact labels 32/40,
primary cue 34/40; misses are mostly unspecific "unusually small for this protein" remarks.
Key numbers: impossible flags cite cross-field 62%, rule 25%; sweep-inconsistent flags cite cross-field
83%; sweep-consistent flags cite cross-field 5%, recall 68%; flagged impossible runs citing a rule
propagate 19% vs 85-87% for the other cues. Verify OR 0.17 [0.10, 0.28]; Opus 5 OR 0.18; Haiku 7.5.
Paper changes: schematic and the old Table 1 moved to Appendix A; new Table 1 (cue taxonomy) and a
"Which cues trigger a flag" paragraph in Results; Appendix C with bootstrap/regression/per-model tables.

## Target venue (checked 2026-09-13)

AgenticLS: NeurIPS 2026 Workshop on Agentic AI for Biological Discovery, https://agenticls.github.io/cfp
(OpenReview group NeurIPS.cc/2026/Workshop/AgenticLS). Deadline September 18, 2026, AoE. Rules quoted from
the CFP: "Full papers: up to 9 pages (excluding references and appendices)"; "Extended abstracts / short
papers: up to 4 pages (excluding references and appendices)"; "Additional supplementary material and
appendices may be included after the references; reviewers are not required to read them"; NeurIPS 2026
style recommended, other styles welcome; double-blind. The manuscript is built in the style's anonymous
submission mode (`\usepackage{neurips_2023}` without `[final]`: "Anonymous Author(s)" block + line
numbers); switch to `[final]` for camera-ready. Body = 4 pages, references p.5, appendices pp.5-8.

## Full-paper version (2026-09-13)

`paper/main.tex` is now the 9-page full paper for the AgenticLS full-paper track (up to 9 pages excluding
references and appendices); the 4-page short version is kept as `paper/main_short.tex`. Style:
`neurips_2026.sty` (supplied by the user) with `[dblblindworkshop]` + `\workshoptitle{...}`, which gives the
anonymous author block, line numbers and the workshop footer; use `[sglblindworkshop]` or `[final]` for
camera-ready. Body ends on page 9, references page 10, appendices pages 10-12. New content over the short
version: related-work section (adds Biomni, BioDiscoveryAgent, BixBench, Zhu 2026, Gurram 2026, Yan 2026),
corruption-spec and template tables (`paper/make_tables.py`), per-condition results table, impossible-mass
variant table, field-level subsection, cue-composition figure (`fig_cues`), robustness subsection, expanded
discussion. `make_tables.py` regenerates tables/main_results.tex, mass_variants.tex, templates.tex,
corruptions.tex from results/summary.json and data/tasks.json.

## Reasoning ablation (2026-09-13, `ablation.py`)

Sonnet 5 with `--thinking disabled`, 40 tasks x {clean, impossible, plausible} x {baseline, +verify} = 240
runs ($1.67), traces in `results/ablation_nothink_sonnet5.jsonl` (named so `grade.py`'s `traces*.jsonl`
glob ignores it). Results vs adaptive thinking: impossible propagation 70% (28/40) vs 74%, flagged 98%;
plausible 92% vs 98%, flagged 35%; +verify impossible 38% in both; plausible+verify 78% vs 81%. All runs
called tools and received the corrupted record; cue composition of flags unchanged (74/56/21). Clean
accuracy 100%. Conclusion: the dissociation is not a by-product of extended thinking. Project total now
~$27.7 over 2,580 runs.
Paper integration of the ablation: paragraph in Section 4.7 (Robustness); compact table
(`paper/tables/ablation_compact.tex`) in Appendix A alongside the impossible-mass variant table, which also
moved to the appendix to keep the body at 9 pages. Abstract, contributions and cost figures updated
(2,580 runs, $28).

Author block (2026-09-13): George Xu, gexu@mgh.harvard.edu, set in `paper/main.tex` and `main_short.tex`.
`paper/main.pdf` is the anonymous submission build (`[dblblindworkshop]`); the named build was deleted at the
user's request (submission is double-blind). For camera-ready, change the option to `[final,dblblindworkshop]`.
