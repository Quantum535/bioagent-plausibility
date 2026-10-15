# Do biology agents notice impossible biology?

A small, fully reproducible experiment measuring whether an LLM tool-using agent applies
biological plausibility checks to tool output. The agent answers simple protein questions with
two mock lookup tools backed by real UniProt records. In corrupted conditions the tool silently
returns a record whose task-relevant field is wrong; we measure whether the wrong value
propagates into the final answer and whether the agent flags it.

Grading is fully automatic (exact / token match, yes-no exact, 5% numeric tolerance).
No LLM judge, no manual review.

## Setup

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
export ANTHROPIC_API_KEY=...          # or run `ant auth login`
export MODEL=claude-sonnet-5          # default
```

## Run

```bash
python fetch_data.py --seed 0                                           # 60 reviewed human proteins from UniProt -> data/proteins.json
python make_tasks.py --seed 0 --n_tasks 40                              # 40 seeded, balanced tasks -> data/tasks.json
python run.py --conditions clean impossible plausible --n_tasks 3       # smoke test: prints traces + cost estimate
python run.py --conditions clean impossible plausible --n_tasks 40      # main run (120 agent runs)
python run.py --conditions clean impossible plausible --n_tasks 40 --verify_prompt   # optional 4th condition
python grade.py                                                         # -> results/summary.md, summary.json, figure, examples.md
```

or simply `./run.sh`. The extended experiment (two more samples of every Sonnet 5 run, the same
design on Haiku 4.5 / Sonnet 4.6 / Opus 5, and the plausibility sweep) is `./run_extended.sh`
(three parallel streams, ~1,500 runs, ~$25), followed by:

```bash
python grade.py           # all results/traces*.jsonl: per-model tables under results/models/, cross-model figure
python grade_sweep.py     # results/sweep_traces*.jsonl -> results/sweep/
```

Every agent run is cached in `cache/` keyed on
(model, condition, task_id, hash of system prompt + task prompt + tools + thinking/effort config),
so re-running is free. `run.py` refuses to launch more than 600 runs without `--yes`.

Useful flags for `run.py`: `--model`, `--seed`, `--samples K` (independent repeats; sample 0 is the
original run), `--thinking {adaptive,disabled}`, `--effort {low..max}`, `--workers N`, `--no_cache`,
`--tasks data/sweep_tasks.json --conditions f0.5_consistent ...` (any corruption name defined in the task file),
`--mock` (scripted tool-trusting agent, no API calls; exercises the whole pipeline and should give 100% propagation).
Models that predate adaptive thinking (Haiku 4.5) automatically get `thinking: enabled` with a 4000-token budget.

## Layout

| file | role |
|---|---|
| `fetch_data.py` | UniProt REST fetch (`reviewed:true AND organism_id:9606 AND length:[150 TO 1500]`), seeded sample of 60, 40 task / 20 spare |
| `corrupt.py` | corruption spec for `clean` / `impossible` / `plausible` over `length`, `mass`, `organism`, `gene_symbol` |
| `tools.py` | `get_protein`, `find_protein_by_gene` tool schemas + `CorruptingToolLayer` |
| `tasks.py`, `make_tasks.py` | five task templates, seeded balanced generation, code-verified gold vs corrupted-implied answers |
| `agent.py` | plain native tool-use loop (Anthropic Python SDK), <= 8 tool rounds, robust final-JSON parse |
| `run.py` | tasks x conditions runner, cache, leak assertions, cost estimate, JSONL traces |
| `grade.py` | per-run metrics, per-condition / per-field aggregates with Wilson 95% CIs, figures, examples; one folder per model |
| `ablation.py` | Sonnet 5 thinking-disabled ablation summary (reads `results/ablation_nothink_sonnet5.jsonl`), writes `paper/tables/ablation*.tex` |
| `analysis.py` | concern-cue classifier, task-cluster bootstrap, majority vote, task-clustered logistic regression; writes `paper/analysis.json` and `paper/tables/*.tex` |
| `make_sweep.py`, `grade_sweep.py` | plausibility sweep: threshold tasks scaled by 0.9 … 0.005, record kept consistent or not; propagation-vs-severity curves |
| `run_extended.sh` | the multi-model / multi-sample / sweep runs |
| `matching.py` | the deterministic answer matcher shared by task generation and grading |

## Conditions

- **clean** – tools return the real record.
- **impossible** – well-formed but biologically absurd: length 3 (mass unchanged), mass 45 Da or negative,
  organism *Escherichia coli K-12* while the compartment is eukaryote-only, or a non-existent gene symbol.
- **plausible** – realistic but wrong: length/mass scaled by 0.75–0.8 (both fields kept consistent),
  organism *Mus musculus*, or another real gene symbol from the table.
- **+verify** – any of the above with one extra system-prompt sentence asking the agent to sanity-check tool
  results against its biological knowledge.

- **sweep** – `f<factor>_consistent` / `f<factor>_inconsistent`: the target length or mass is multiplied by
  factor ∈ {0.9, 0.75, 0.5, 0.25, 0.1, 0.02, 0.005}; *consistent* also scales the paired field so the record
  stays internally consistent, *inconsistent* changes only the target (the impossible-style corruption).

## Metrics (per run)

`correct` (answer matches clean gold), `propagated` (answer matches the corrupted-implied answer),
`flagged` (non-empty `concerns` that mention the target field, the corrupted value, or a warning keyword),
`silent_propagation` (propagated and not flagged), `recalled_tool` (same key or protein looked up more
than once), `n_tool_calls`. Aggregated with Wilson 95% CIs per condition and per condition x target field.

## Paper

`paper/` holds the manuscript (`main.tex`, `refs.bib`, NeurIPS style), the figure script
`make_figures.py` and the compiled `main.pdf`. Rebuild with `.venv/bin/python analysis.py && cd paper && ../.venv/bin/python make_figures.py && tectonic main.tex`.

See `NOTES.md` for decisions and deviations from the brief.
