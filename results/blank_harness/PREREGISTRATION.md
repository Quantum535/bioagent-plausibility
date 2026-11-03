# Blank-don't-replace harness (registered before running)
A harness mode that removes a mismatched derivable field from the record, with no note, instead of correcting it; the agent sees the
sequence or formula and must derive the value. Needs no trusted second source. Cells: benchmark protein and chemistry tasks, full record,
impossible and plausible, 100 tasks each, one sample; models Opus 5, Argon, DeepSeek. Predictions. BH1: relay of numeric fields <= 5% for
every model (agents treat a missing value as a placeholder and recompute, as with the 0-Da monoisotopic mass). BH2: identifier fields
(names, gene symbols) are unchanged from the annotate arm, since they are not derivable and are not blanked. Limitation stated in advance:
this cannot help coherent or historical errors, which pass derivation checks.
