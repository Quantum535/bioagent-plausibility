Dear Editors,

Please consider the enclosed manuscript, "Internal consistency, not plausibility, decides whether AI agents relay database errors", as an Article in Nature Machine Intelligence.

Language-model agents such as Coscientist, ChemCrow and Biomni now query scientific databases and compute on what they retrieve, and some verify their own output against curated databases, which presumes that the databases are right. They are not always right: of the 300 reviewed human proteins in our benchmark, 167 have a superseded sequence in UniProt's archive. We asked what decides whether an agent overrides a wrong value in a database record, in a live deployment of Biomni with errors injected into UniProt and PubChem responses, in a benchmark of ten models from five developers, and on 79 sequences that UniProt has since superseded.

Three findings should interest the journal's readership across machine learning and the sciences.

1. Internal consistency decides. A record that agreed with itself carried an error of any size: the superseded UniProt sequences were relayed in 90-100% of runs, as often for the 13 traced to documented errors as for the rest, and as often with the protein's identity removed. A contradiction inside the record made override possible, to a degree set by the size of the contradiction, the model and what the model knew about the entity; controls separating the record from the model's identity knowledge, reasoning and memory show which.

2. Noticing errors is partly an artefact of how agents are asked. Asked to list concerns, agents flagged most errors and still relayed many; without that request they rarely questioned plausible values and relayed more. Benchmarks that solicit concerns overstate detection and understate relay.

3. Only acting on the record before the agent reads it works everywhere. Instructions removed relay only where the record contradicted the value; an output format that asked for the agent's own estimate let a correct memory act on consistent errors. Withholding fields that failed a derivation check, or silently correcting records from a current copy, left nothing to relay without lowering accuracy, whereas showing the agent both values let it restore the original. The design principle is to resolve conflicts before the model sees them and keep the audit trail for people.

The closest work is concurrent: Yang et al. (2026) show that tool-using agents adopt corrupted tool returns and may question a return while passing it on. Their returns are single values or passages. Our study adds the mechanism in structured records, where fields can contradict one another; errors that actually occurred in a production database, with an audit of why each was revised; and a comparison of remedies by what they change in the agent's answer. Related work on knowledge conflicts (ClashEval; Xie et al., 2024) studies retrieved text rather than structured records.

Predictions were fixed in dated repository commits before each experiment, and the deployment hypotheses were registered on OSF; several failed and the paper reports each in one place. The first deployment run exposed the study's name to the agent through a directory path; an audit found this and the run was repeated in an isolated environment, and both are reported. All code, run traces, labels and registrations are public (GitHub release v1.2-nmi; Zenodo [NEW DOI]).

A preliminary account of the benchmark alone was presented at the AgenticLS workshop at ICML 2026; it appears here as Extended Data Fig. 1, and every other experiment is new. The manuscript is not under consideration elsewhere, and a preprint will be posted to arXiv at submission. I am the sole author and declare no competing interests. AI tools (Claude, Anthropic) assisted with analysis scripts, analysis and drafting, as stated in the manuscript.

Suggested reviewers (authors of the closest work): Kevin Wu or James Zou (Stanford; ClashEval); Yu Su (Ohio State; knowledge conflicts); Yohan Jo (Seoul National University; tool overreliance); Philippe Schwaller (EPFL; ChemCrow). I would ask that the Biomni authors not review, since the paper evaluates their system.

Thank you for your consideration.

George Xu
Harvard Medical School and Massachusetts General Hospital
gexu@mgh.harvard.edu | ORCID 0009-0003-1926-2262
