Dear Editors,

Please consider the enclosed manuscript, "Internal consistency, not plausibility, decides whether AI agents relay database errors", as an Article in Nature Machine Intelligence.

Agents such as Coscientist, ChemCrow and Biomni now query scientific databases and compute on what they retrieve, and some verify their own output against curated databases, which presumes that the databases are right. They are not always right: 167 of the 300 reviewed human proteins in our benchmark have a superseded sequence in UniProt's archive. We asked what decides whether an agent overrides a wrong value in a database record, in a live deployment of Biomni with errors injected into UniProt and PubChem responses, in a benchmark of ten models from five developers, and on 79 sequences that UniProt has since superseded.

A methodological finding of general interest comes first. The usual way to measure whether agents notice bad data, asking them to list concerns, inflates detection: asked, agents flagged most errors and still relayed many; not asked, they rarely questioned plausible values, and relayed more. Benchmarks that solicit concerns overstate detection and understate relay.

The substantive finding is that internal consistency, not plausibility, decides override. A record that agreed with itself carried an error of any size: the superseded sequences were relayed in 90-100% of runs, as often for the 13 traced to documented errors as for the rest, and as often with the protein's identity removed. A contradiction inside the record made override possible, to a degree set by its size, the model and what the model knew; registered controls separate the record's role from the model's identity knowledge, reasoning and memory.

The design consequence is to resolve conflicts before the model sees them. Instructions removed relay only where the record contradicted the value. Withholding fields that failed a derivation check, or silently correcting records from a current copy, left nothing to relay without lowering accuracy, whereas showing the agent both values let it restore the original.

The closest work is Yang et al. (2026; ref. 31), on agents' overreliance on unreliable tools, and ClashEval (Wu et al., 2024), on conflicts between retrieved text and a model's prior. Neither has three things this paper has: the internal consistency of a structured record identified as the deciding variable; real superseded records from a production database, with an audit of why each was revised; and remedies compared by what they change in the agent's answer, with accuracy reported alongside relay.

All 48 predictions were fixed in dated repository commits or on OSF before the runs they concern and are listed with their outcomes in a supplementary table, including the 17 that failed. The first deployment run exposed the study's name to the agent through a directory path; an audit found this, the run was repeated in an isolated environment, and both are reported. Code, run traces, labels and registrations are public (GitHub release v1.3-nmi; Zenodo 10.5281/zenodo.23968145).

A preliminary account of the benchmark alone was presented at the AgenticLS workshop at ICML 2026 and appears here as Extended Data Fig. 1; every other experiment is new. The manuscript is not under consideration elsewhere, and a preprint will be posted to arXiv at submission. I am the sole author and declare no competing interests. AI tools (Claude, Anthropic) assisted with analysis scripts, analysis and drafting, as stated in the manuscript.

Suggested reviewers (authors of the closest work): Kevin Wu or James Zou (Stanford; ClashEval); Yu Su (Ohio State; knowledge conflicts); Yohan Jo (Seoul National University; tool overreliance); Philippe Schwaller (EPFL; ChemCrow). I would ask that the Biomni authors not review, since the paper evaluates their system.

Thank you for your consideration.

George Xu
Harvard Medical School and Massachusetts General Hospital
gexu@mgh.harvard.edu | ORCID 0009-0003-1926-2262
