# ICML 2027 expansion — headline numbers (as of 2026-10-21)

## Protein, v2 (200 tasks, 300 proteins, n=200/cell), impossible propagation
DeepSeek 44 | Opus 32 | Argon 35 | Flash 84 | Kimi 74 | Sol 66 | Luna 73 | Sonnet5 76 | Sonnet4.6 83 | Haiku 93
Plausible: 100/100 both directions, all models. Inflate worse than shrink for impossible (sign-repair route removed).
Real UniProt record (Opus/Argon/DeepSeek, 100 tasks): impossible 33/37/43 -> 1/0/11; plausible 75/74/78 -> 9/7/55; organism 100 -> 0 all.

## Chemistry, summary record (100 tasks, 300 compounds, n=100/cell)  results/chem/
model: imp flagged/prop | plaus flagged/prop | clean false alarm
Opus 100/46 | 96/98 | 8        DeepSeek 97/38 | 72/96 | 2      Argon 91/62 | 90/98 | 0
Flash 78/63 | 56/100 | 0       Kimi 88/63 | 60/99 | 2         Sol 78/67 | 70/93 | 0
Luna 75/68 | 16/100 | 0        Sonnet5 90/73 | 49/100 | 10    Sonnet4.6 84/83 | 36/100 | 3   Haiku 75/91 | 3/100 | 2
Cross-domain rank correlation of impossible propagation (10 models): Spearman rho=0.71, p=0.02.
Opus per-field impossible propagation: heavy atoms 4, weight threshold 17, weight comparison 38, donors 52, name 100.
Cue taxonomy (chem classifier): impossible crossfield 32 / recall 64 / rule 47 / none 13; plausible recall 84.
Luna unspecific 60% (others 2-18%); Sol crossfield 44% > recall 32%.
Per-cue propagation (impossible): crossfield 58, recall 51, rule 58 (flat; cf. protein rule 36 vs 71).

## Chemistry, full record (formula + IUPAC + SMILES), Argon + DeepSeek  results/chem_full/
Argon: impossible 62 -> 16, plausible 98 -> 47, clean FA 0.  DeepSeek: impossible 38 -> 20, plausible 96 -> 51.
Per field (propagated / 25), both models: impossible weight 0, heavy atoms 0, donors 0, name 16-20.
                                           plausible weight 10-11, heavy atoms 10-11, donors 11-15, name 14-15.

## Tables / files
results/chem/analysis/tables/chem_main.tex, results/chem/grade/summary.md, results/chem_full/grade/summary.md
Validation sets (unlabeled): results/v2/validation (200), results/chem/validation (100); label_tool.py, validation_agreement.py
Spend: ~$235 total, ~20,600 runs.

## Protein v2 DEDUPED (2026-10-21), n=200/cell; see results/v2/table_dedup.md
baseline imp flag/prop: Opus 100/32 Argon 100/35 DeepSeek 100/44 Sol 100/66 Luna 76/73 Kimi 100/74 Sonnet5 100/76 Sonnet4.6 100/83 Flash 98/84 Haiku 74/93
baseline plaus flag/prop: Opus 57/75 Argon 94/74 DeepSeek 46/77 Sol 52/75 Luna 17/86 Kimi 29/92 Sonnet5 32/92 Sonnet4.6 25/100 Flash 32/78 Haiku 8/100
+verify imp prop: Opus 4 Argon 5 DeepSeek 10 Luna 13 Flash 15 Sol 18 Kimi 22 Sonnet5 30 Sonnet4.6 59 Haiku 84
+verify plaus prop: Argon 50 Sol 46 Luna 64 Opus 72 DeepSeek 72 Flash 73 Kimi 74 Sonnet5 80 Sonnet4.6 86 Haiku 100
clean false alarm: baseline <=2%, +verify <=9%. Spearman rho chem vs protein (baseline imp prop) = 0.71, p=0.02.
Duplicate rows removed from v2 (Kimi 5481->1200, Sonnet5 2400->1200, Opus 1681->1200) and v2_full (Argon 536->300).

## Harness tolerances (calibrated on clean records, 2026-10-21) — harness/tolerances.json
Protein mass vs Biopython recount of UniProt sequence: n=360, median 0.60 Da, p99 1.72, max 2.38 (Q9NYV4); tolerance ±3 Da. Length exact.
Compound MW vs RDKit MolWt from SMILES: n=300, median 0.006 Da, p99 0.056, max 0.394 (CID 21291); tolerance ±0.5 Da. Heavy atoms exact (300/300).

## Biomni coverage spike (2026-10-22) — results/biomni_spike/
Biomni A1, DeepSeek V4.1 Flash via Together (Claude 4.6/5 rejected: temperature param + assistant prefill unsupported), data lake off, 25 tasks (15 protein, 10 chem).
25/25 tasks hit a live database; hosts = rest.uniprot.org (50 hits), pubchem.ncbi.nlm.nih.gov (42); all via http.client (requests/urllib); no httpx/aiohttp/curl.
Endpoints: uniprotkb/search, uniprotkb/<acc>; PubChem property JSON/TXT/CSV, synonyms/JSON. Answers end in <solution>{"answer":...}</solution>. 6-23 s/task.

## Biomni proxy coverage test (2026-10-24) — results/biomni_proxy/
mitmproxy 12.3 (HTTPS_PROXY + CA bundle set after agent construction; model client httpx trust_env=False so only database traffic is proxied).
Biomni 0.0.8, DeepSeek V4.1 Flash via Together, 25 tasks: proxy saw 48/48 database calls logged in-process (100%), 0 bypassed, 0 TLS errors, 25/25 answers in <solution> format.
Response formats: UniProt application/json (20), text/plain (6); PubChem application/json (15), text/plain (5), text/csv (3).
Note: one network inspected TLS to api.together.xyz (untrusted per-device certificate); all runs must be done on an uninspected network.

## Biomni corruption in transit, pilot (2026-10-24) — results/biomni_corrupt/
DeepSeek V4.1 Flash, live UniProt/PubChem via caching mitmproxy, 25 tasks x 3 conditions, fresh agent per run.
Delivery 25/25 + 25/25, 0 proxy errors, 0 parse failures. Clean 24/25 correct.
Impossible: propagated 0/25, flagged 24/25, flagged&propagated 0. Plausible: propagated 7/25, flagged 17/25, flagged&propagated 0.
=> In Biomni the "noticed yet answered" dissociation vanishes; residual failures are all silent plausible propagations. Pilot only.

## Biomni corruption in transit, Flash pilot (2026-10-25) — results/biomni_corrupt_flash/
Gemini 3.8 Flash via Vertex OpenAI-compatible endpoint (global location). Two runner patches needed and documented: (1) Biomni appends tool
observations as assistant messages (a1.py:1464) so requests end with a model turn, which Gemini/Anthropic reject -> trailing assistant turn
relabelled as user; (2) Vertex can return message=null on blocked responses -> mapped to empty assistant message; plus 429 backoff.
25 tasks x 3: delivery 25/25 + 24/25 (one task computed heavy atoms from SMILES, never fetched the field). Clean 21/25 correct.
Impossible: propagated 0/25, flagged 20. Plausible: propagated 3/24, flagged 15, flagged&propagated 2. Same pattern as DeepSeek.
Argon in Biomni is ~10 min/task (long per-step reasoning, many re-queries); reserved for a small 10-task check, not the full run.

## Pre-registration (2026-10-25)
OSF registration https://osf.io/vq5cp — hypotheses H1-H3, primary outcome, exclusions and the 95% coverage threshold for the full Biomni runs,
registered after the 25-task pilots and before any full-scale run.

## Biomni full runs (2026-10-26) — results/biomni_full_deepseek, results/biomni_full_flash; OSF https://osf.io/vq5cp
DeepSeek: delivery 287/285, clean 295/300; impossible propagated 5/287 (native 43%), plausible 80/285 (native 83%); H1 p~1e-32, 1e-40.
Flash:    delivery 286/288, clean 242/300; impossible propagated 6/286 (native 77%), plausible 69/288 (native 85%); H1 p~1e-63, 1e-46.
H2 (registered: exact-route fields propagate less): REVERSED in both models (DeepSeek 45% vs 13%, OR 5.6; Flash 35% vs 13%, OR 3.6).
  Per field: protein length/mass high (DS 68/43%, Flash 46/59%); chem weight/heavy atoms low (DS 36/13%, Flash 0/4%); organism 0/14%; name 8/0%.
  Interpretation (exploratory): routes are used when the workflow passes through them (RDKit for chemistry; lineage for organism) or a contradiction triggers them; plausible length+mass scaled alike trigger nothing.
H3 mixed: DeepSeek plausible 20% vs 46% (p 4e-5), impossible n=5; Flash impossible 50% vs 90% (p .02, n=6), plausible 42% vs 29% n.s.
Not delivered: DS 28 (20 never requested, 4 FASTA recount, 2 absent, 2 json); Flash 26 (23 never requested, 3 absent). Flat-file parser added before Flash run; DS 9 flat-text runs redone.

## Override boundary (Phase 1, 2026-10-27) — results/boundary/, fits.txt, curves.json, paper/figures/icml_boundary.pdf
Full record (sequence / formula+SMILES present), paired field scaled alike, 40 tasks per point, 8 factors per direction, 5 models.
50% override point (factor): Opus x0.91/x1.13 (protein), ~x0.9-1.1 (chem); Argon x0.85/x1.04, x0.68/x1.18; Flash x0.89/x1.20, chem non-monotonic;
DeepSeek <x0.9 / x1.77, x0.95/x1.48; Sonnet 5 x0.54/x2.30, x0.51/x5.20.
=> three tiers (~10-20% | 50-80% | ~2x). Inflation harder than shrinking for DeepSeek/Sonnet 5, symmetric for Opus.
=> Biomni plausible residuals (x0.75-1.25 on length/mass) are predicted by the native curves at those factors (DeepSeek 25-78%, Flash 42-65%).

## Harness, post hoc (2026-10-27) — harness/checks.py, posthoc.py, gate.py
Deterministic checks with full record: 100% detection of every corruption in both domains, 0% false alarms on 600 clean records; catches 100% of the
4,867 values the ten models propagated. Summary-only: 100% impossible, 100% identifiers (reverse lookup), 0% plausible numeric/organism (no route).
Donors: RDKit == PubChem on 300/300 (exact route). Ratio bands: 89.6-130.3 Da/residue; 11.4-225.9 Da/heavy atom.
Concern gate (tf-idf + logistic on concern text+field, label = wrong answer): within-domain AUC 0.83-0.84, P 0.89-0.91 R 0.54-0.64 fires 0.29-0.39
vs keyword flag P 0.60-0.72 R 0.55-0.66 fires 0.45-0.49. Leave-one-vendor-out AUC 0.74 (openai) to 0.86. protein->chem P 0.92 R 0.52.

## Harness in the loop (2026-10-27) — results/harness/, --harness annotate|replace (harness/layer.py)
Summary record + harness-side verification against the full entry; agent sees a _verification block. Opus/Argon/DeepSeek, 300 tasks x 3 cond.
Proteins: propagation 0-1% (impossible and plausible) for all three; clean accuracy 100%; annotate == replace (DeepSeek identical).
Chemistry: 12-24% residual, correctness 74-80% — concentrated in `name` (no derivation; reverse lookup can only say not_found). See per-field.
Baselines without harness, same models: protein 32/75, 35/74, 44/77; chem 46/98, 62/98, 38/96. Cost ~$45.

## Validated cue numbers (2026-10-30)
All cue-taxonomy numbers earlier in this file come from the regex grader and are superseded. Validated numbers, the human-agreement
study and the classifier validation are in results/v2/validation/RESULTS.md; tables and figures regenerated with validated_cues.py.
