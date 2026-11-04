# Round 2 (registered before running, 4 November 2026): identity-stripped records, thinking, concerns field, familiar duplicate

## IS: identity-stripped records
Objection addressed: override of protein length/mass with the full record may be memory acting on the protein's identity, not derivation from the sequence (benchmark agents had no code tool; models hold the current length for 61-67% of historical proteins).
Design: record format `anonymous`: the question refers to the protein as ENTRY-n, the gene-symbol tool is removed, and the record returned is only organism, length, mass and sequence (reduced from the full record after any corruption, including coherent patches). Cells: (a) historical set, 79 superseded records, no second source, one sample; (b) benchmark length-threshold tasks (25; the accession-based numeric tasks), clean, impossible and plausible (paired fields scaled, sequence contradicts), three samples. Models: Opus 5, Gemini 4 Argon, DeepSeek V4.1 Flash. Comparison: the same cells with identity (results/phase5 full record; results/v2_full plausible on the same 25 tasks).
Predictions. IS1: on (a), relay >= 90% for every model (consistency suffices; identity and memory are not needed for relay). IS2: on (b) plausible, relay for Opus 5 and Argon is within 15 points of the with-identity value on the same tasks (override is derivation-driven); a rise of >= 30 points means it was memory-driven. IS3: on (b) impossible, relay <= 20% for Opus 5 and Argon. IS4: clean accuracy on (b) >= 90% for every model (the reduced record is usable).
Tests: McNemar paired by task and sample (two-sided) for IS2; Wilson intervals otherwise.

## TH: thinking on/off
Objection addressed: reasoning configuration is an unreported moderator. Only the Anthropic provider exposes the setting, so the ablation uses Anthropic models.
Design: (a) Opus 5 with thinking disabled on the full-record protein cell (first 100 benchmark tasks, impossible and plausible), compared with the existing adaptive-thinking runs (results/v2_full); (b) Sonnet 5 with thinking disabled on the summary-record benchmark (200 protein and 100 chemistry tasks, impossible and plausible), compared with Fig. 2.
Predictions. TH1: on contradicted cells (full record, and impossible values from the summary record), relay is higher without thinking by >= 10 points (override needs reasoning). TH2: on plausible summary-record values (consistent), relay changes by < 10 points.
Tests: McNemar paired by task, one-sided for TH1, two-sided for TH2.

## NC: a prompt that does not solicit concerns
Objection addressed: the `concerns` field solicits flags (inflating detection) and "use the provided tools" instructs relay.
Design: variant `no_concerns`: "You are a bioinformatics assistant. Use the provided tools to answer. End your reply with exactly one line of JSON: {\"answer\": ...}." Cells: benchmark summary record, protein (first 100 tasks) and chemistry (100 tasks), impossible and plausible; models Opus 5, Argon, DeepSeek. Unsolicited flags are scored from the free text before the JSON line by a fixed keyword list (inconsisten, discrepan, mismatch, suspicious, implausible, incorrect, erroneous, wrong, surprising, does not match, cannot be, unusual) checked by hand on a 50-run sample.
Predictions. NC1: relay under `no_concerns` is within 10 points of the default prompt on every cell (the concerns field does not change relay). NC2: unsolicited flag rates are below half of the solicited flag rates in the same cells (the field is a demand characteristic for detection).
Tests: McNemar paired by task, two-sided.

## FD: a familiar duplicate field
Objection addressed: the verbatim repeat in R1 lived in a non-standard field (molecular_weight_reported), which may itself raise suspicion.
Design: the repetition arms rebuilt with the repeat under `average_mass` (by definition the molecular weight, a standard chemistry quantity): F1, weight and average_mass scaled together (a familiar repeat agrees); F2, only the weight scaled (a familiar repeat disagrees). Same 60 compounds, full record, one sample; models Opus 5, Argon, Flash, DeepSeek; F1 also run clean for false overrides. Comparison: R0, R1, R2 (results/repetition).
Predictions. FD1: F1 relay exceeds R1 relay by >= 10 points pooled (the odd field name accounted for part of R1's drop). FD2: F1 relay does not exceed R0 by >= 10 points pooled (repetition is still not agreement). FD3: F2 relay is below R0 (a disagreeing repeat lowers relay, as in R2).
Tests: McNemar paired by compound (first sample of R0/R1/R2 against F1/F2), one-sided in the stated directions.

## Exclusions and sensitivity
Runs without a parseable answer are excluded and counted; every rate is also reported with unparsed runs counted as failures (neither correct nor relayed). Runs that fail at the API are retried.
