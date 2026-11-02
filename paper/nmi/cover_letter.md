Dear Editors,

Please consider the enclosed manuscript, "Consistency, not plausibility: why tool-using science agents relay database errors they detect", as an Article in Nature Machine Intelligence.

Language-model agents such as ChemCrow and Biomni now query scientific databases and compute on what they retrieve. Those databases contain errors: of the 300 reviewed human proteins in our benchmark, 167 have a superseded sequence in UniProt's archive. We asked when an agent relays a wrong database value into its answer, and what changes the outcome. The study spans a live deployment of Biomni against the UniProt and PubChem APIs with errors injected in transit, a controlled benchmark of ten models from five developers, and 79 protein-sequence errors that UniProt itself later corrected.

Three findings should interest the journal's readership across machine learning and the sciences:

1. Agents detect errors and relay them anyway. Impossible values were flagged in 75-100% of runs yet relayed in 32-93%. The answer field carried the database's value while the correct value, when the agent had computed it from the record's own formula, sat in a remark.

2. What decides override is agreement, not plausibility. Adding one field consistent with a wrong value raised relay from 63% to 91% for one model; making a record disagree with itself lowered relay with the wrong value unchanged. Real, historically corrected errors are internally consistent, and every model relayed them in 90-100% of runs regardless of the size of the revision.

3. Correcting the record works; showing the conflict does not. An independent second source applied silently removed relay entirely (0 of 702 runs), whereas showing the agent both values let it restore the original, in one model 41% of the time. This cuts against a transparency-toward-the-model instinct and has direct design consequences for agent systems on scientific data.

The closest prior work studies knowledge conflicts in retrieved text (ClashEval; Xie et al., ICLR 2024) and, concurrently, agents' overreliance on corrupted tool returns (Yang et al., 2026). Our contribution is to carry these questions into structured scientific records, where a value sits among fields that can confirm or contradict it, to identify agreement among fields as the deciding variable, to test errors that actually occurred in a production database, and to compare corrections by what they change in the agent's answer. Predictions were fixed in dated commits before each experiment and the deployment hypotheses were registered on OSF; several predictions failed and the paper reports each. All code, run traces and labels are public (GitHub release v1.0-nmi; Zenodo 10.5281/zenodo.23869455).

A preliminary account of the benchmark results alone was presented at the AgenticLS workshop at ICML 2026. The deployment, override-boundary, coherent-corruption, new-field, historical-error, harness and presentation experiments, which carry the paper's conclusions, are new. The manuscript is not under consideration elsewhere, and a preprint will be posted to arXiv at submission. I am the sole author and declare no competing interests.

Suggested reviewers (authors of the closest work): Kevin Wu or James Zou (Stanford; ClashEval); Yu Su (Ohio State; knowledge conflicts); Yohan Jo (Seoul National University; tool overreliance); Philippe Schwaller (EPFL; ChemCrow). I would ask that the Biomni authors not review, since the paper evaluates their system.

Thank you for your consideration.

George Xu
Harvard Medical School and Massachusetts General Hospital
gexu@mgh.harvard.edu | ORCID 0009-0003-1926-2262
