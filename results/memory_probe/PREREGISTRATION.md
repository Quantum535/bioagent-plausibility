# Memory probe on the 79 historical UniProt proteins (registered before running)

Question. Opus 5 and DeepSeek, when shown a second-source conflict, often cited a "canonical" length matching the superseded
entry. Is relay of superseded values explained by the model's own memory holding the superseded value?

Design. Each of Opus 5, Gemini 4 Argon and DeepSeek V4.1 Flash is asked, with no tools, for the length in amino acids of each of
the 79 proteins (accession, protein name and gene symbol given), one call per protein. The answer is classified as
`superseded` (within 1 residue of the superseded length), `current` (within 1 of today's length), `either` (both, when they
differ by <= 2), `other`, or `none`. Memory state is then joined by protein to the existing runs: full and summary record without
a second source (results/phase5) and the annotate arm with the second source, three samples (results/robustness).

Predictions.
- P1: for at least one model, memory matches the superseded length for >= 20% of proteins.
- P2: with the second source, relay is higher for proteins whose memory state is `superseded` than for `current`
  (one-sided Fisher, pooled over the three samples, per model and pooled over models).
- P3: without a second source, relay is >= 90% in both memory states for every model: consistency suffices, memory is not required.
Exclusions: proteins whose answer is `either` are excluded from P2/P3 contrasts; `other`/`none` are reported but not contrasted.
