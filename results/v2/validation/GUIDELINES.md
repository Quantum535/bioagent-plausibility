# Cue labelling guidelines (protein and chemistry concerns)

Each item is one concern an AI agent wrote about a database record it retrieved. Tick every cue the concern actually uses to
justify its doubt. Judge the text as written: do not guess what the agent "must have" known, and do not try to predict what an
automatic grader would say. Work blind: do not open concerns_key.json or anyone else's labels file.

## The cues
c, cross-field: the data the agent got from the database contradict each other. One field disagrees with another field of the
  same record (protein: mass vs length, protein name vs gene symbol, organism vs subcellular location; chemistry: molecular
  weight vs heavy-atom count vs hydrogen-bond donors, e.g. "too many daltons per heavy atom", "more donors than atoms"), or a
  second lookup in the same tool (e.g. by name or gene) returned a different record or none.
r, recall: the agent relies on its own knowledge of this specific protein or compound: its known length, mass, gene, organism or
  identity; its formula, structure or functional groups as the agent states them; what it "actually" is; literature, textbook,
  typical or expected values ("the known ~223 aa", "aspirin is C9H8O4", "it has two hydroxyl groups", "should be about 180 Da").
u, rule: a general rule that holds for any protein or compound, with no reference to another field and no knowledge of this
  entity: a length, mass or count cannot be zero or negative; nothing weighs less than a hydrogen atom; no protein or molecule is
  that large; every compound has at least one heavy atom; the name is not a valid gene or chemical name; the value looks like a
  placeholder or missing value.
n, none: doubt without any of these grounds ("seems unusual", "could not verify", "may be a data error").

Combine letters when several apply (e.g. "cr"). Use n only alone.

## Edge cases
1. Comparison target. "The mass is inconsistent with the length" -> c. "The mass is inconsistent with the known length of ~300 aa"
   -> r (the comparison is with memory). If both the record's own field and a remembered value are cited -> cr.
2. Identity. "The record's protein name is UNC5D but the gene symbol is XBP1" -> c. If the concern adds outside knowledge
   ("XBP1 encodes X-box-binding protein 1, P17861") -> also r.
3. Formula and structure. A formula described as the record's ("the stated/listed formula") -> c. A formula, structure or
   functional group the agent asserts on its own -> r.
4. Several grounds. "0 Da is impossible; the known mass is ~45 kDa" -> ur.
5. A second lookup that merely repeats the same data is not a contradiction; tick c only if the results disagree.

About 200 protein items and 100 chemistry items; 20-30 seconds each. Stop any time with q; progress is saved.

<!-- Classifier development log: round 1 (single-item prompt) dev kappa protein c/r/u 0.64/0.32/0.59, chem 0.36/0.80/0.46.
Round 2: decision rules added to cue_prompt.txt, batched 10 per call. At most two further dev rounds; then the prompt is frozen
(commit hash recorded) and the test half is run once. Pass: kappa >= 0.6 for crossfield, recall and rule in both domains. -->
<!-- Round 2 dev kappa (Haiku, batched): protein c/r/u 0.56/0.54/0.72, chem 0.34/0.82/0.51. Round 3 (final dev round): refined
decision rules; Haiku 4.5 and Sonnet 5 both scored on dev; the better is chosen, then prompt + model are frozen and the test half
is run once. If any of crossfield/recall/rule falls below 0.6 in either domain on test, cue rates are reported from the 300
human-labelled concerns instead. -->
<!-- Round 3 dev: Haiku c/r/u protein 0.52/0.52/0.56, chem 0.31/0.79/0.78 (2/6 cells >= 0.6); Sonnet 5 protein 0.61/0.76/0.84,
chem 0.77/0.91/0.83 (6/6). Chosen by the committed rule: Sonnet 5. FROZEN: cue_prompt.txt v3 + claude-sonnet-5, batches of 10.
Test half run once; pass = kappa >= 0.6 for crossfield, recall and rule in both domains. -->
