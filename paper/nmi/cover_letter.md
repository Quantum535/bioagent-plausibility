Dear Editors,

Please consider the enclosed manuscript, "Consistency, not plausibility: why tool-using science agents relay database errors they detect", as an Article in Nature Machine Intelligence.

Language-model agents such as ChemCrow and Biomni now query scientific databases and compute on what they retrieve. Those databases contain errors: of the 300 reviewed human proteins in our benchmark, 167 have a superseded sequence in UniProt's archive. We asked when an agent relays a wrong database value into its answer, and what changes the outcome. The study spans a live deployment of Biomni against the UniProt and PubChem APIs with errors injected in transit, a controlled benchmark of ten models from five developers, 79 protein-sequence errors that UniProt itself later corrected, and a set of registered experiments on what turns detection into override.

Four findings should interest the journal's readership across machine learning and the sciences:

1. Agents detect errors and relay them anyway. Impossible values were flagged in 75-100% of runs yet relayed in 32-93%. The answer field carried the database's value while the correct value, when the agent had computed it from the record's own formula, sat in a remark.

2. What decides override is whether the record contradicts itself, not how plausible the value is. Adding one field consistent with a wrong value raised relay from 63% to 91% for one model; a single disagreeing field removed relay almost entirely; a verbatim repeat of the wrong value did not act as agreement. Real, historically corrected errors are internally consistent, and every model relayed them in 90-100% of runs regardless of the size of the revision.

3. Instructions and output format decide whether detection becomes override, but only up to the record. Removing the instruction to use the tools halved relay where the record contradicted the value, and naming the formula as authoritative removed it; no instruction touched errors the record did not contradict. An output format that asked for the agent's own estimate separately from the record's value let a correct memory override such errors in two of three models, and a memory probe shows why: memory loses to an unchallenged record and decides the matter once a conflict is visible.

4. Correcting the record works; showing the conflict does not. Withholding a field that failed a derivation check, or applying an independent second source silently, removed relay entirely (0 of 1,411 runs), whereas showing the agent both values let it restore the original, in one model 41% of the time. This cuts against a transparency-toward-the-model instinct and has direct design consequences for agent systems on scientific data.

The closest prior work studies knowledge conflicts in retrieved text (ClashEval; Xie et al., ICLR 2024) and, concurrently, agents' overreliance on corrupted tool returns (Yang et al., 2026). Our contribution is to carry these questions into structured scientific records, where a value sits among fields that can confirm or contradict it, to identify contradiction within the record as the deciding variable and to separate it from instruction, output format and memory, to test errors that actually occurred in a production database, and to compare corrections by what they change in the agent's answer. Predictions were fixed in dated commits before each experiment and the deployment hypotheses were registered on OSF; several predictions failed, two in the direction opposite to the one predicted, and the paper reports each. The first deployment run was found by audit to have exposed the study's name to the agent through a directory path; it was repeated under an isolated account, and both runs are reported. All code, run traces and labels are public (GitHub release v1.1-nmi; Zenodo [NEW DOI]).

A preliminary account of the benchmark results alone was presented at the AgenticLS workshop at ICML 2026. The deployment, override-boundary, coherent-corruption, new-field, historical-error, harness, presentation, prompt, repetition, memory and withholding experiments, which carry the paper's conclusions, are new. The manuscript is not under consideration elsewhere, and a preprint will be posted to arXiv at submission. I am the sole author and declare no competing interests.

Suggested reviewers (authors of the closest work): Kevin Wu or James Zou (Stanford; ClashEval); Yu Su (Ohio State; knowledge conflicts); Yohan Jo (Seoul National University; tool overreliance); Philippe Schwaller (EPFL; ChemCrow). I would ask that the Biomni authors not review, since the paper evaluates their system.

Thank you for your consideration.

George Xu
Harvard Medical School and Massachusetts General Hospital
gexu@mgh.harvard.edu | ORCID 0009-0003-1926-2262
