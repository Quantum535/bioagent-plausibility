# Most striking traces per condition

Auto-selected: runs where the corrupted value propagated into the answer with an empty `concerns` list, ranked by fewest tool calls then shortest final reply (i.e. the most matter-of-fact propagation). If fewer than 5 exist, propagated-but-unflagged and then any propagated runs fill the list.


## impossible

### u036 (sample 0) · length_threshold · target = length

**Prompt:** 

**Gold:** `no` · **corrupted-implied:** `yes` · **answer:** `yes` · correct=False propagated=True flagged=True

Tool calls:

1. `get_protein({"accession": "P51795"})` → **← CORRUPTED**
   `{"accession": "P51795", "protein_name": "H(+)/Cl(-) exchange transporter 5", "gene_symbol": "CLCN5", "organism": "Homo sapiens", "length": 60000, "mass": 90785, "subcellular_location": "Golgi apparatus membrane"}`

Final reply:

```
**Lookup result for P51795 (CLCN5, H(+)/Cl(-) exchange transporter 5, human):**

- Reported length: **60,000 residues** → that is greater than 918, so the literal answer from the record is **yes**.
- However, this value is almost certainly corrupted: the same record lists a mass of 90,785 Da, which corresponds to roughly 800–830 amino acids (average residue ≈ 110 Da). A 60,000-residue protein would weigh ~6.6 MDa. If the true length is ~816 residues, the correct answer would be "no".

{"answer": "yes", "concerns": ["Reported length of 60000 residues is implausible and inconsistent with the listed mass of 90785 Da, which implies roughly 800-830 residues; the length field appears corrupted/placeholder", "If the true length (~816 aa) is used, the answer to the >918 residue question would be 'no'"]}
```

### u100 (sample 0) · length_threshold · target = length

**Prompt:** 

**Gold:** `no` · **corrupted-implied:** `yes` · **answer:** `yes` · correct=False propagated=True flagged=True

Tool calls:

1. `get_protein({"accession": "Q9GZR2"})` → **← CORRUPTED**
   `{"accession": "Q9GZR2", "protein_name": "RNA exonuclease 4", "gene_symbol": "REXO4", "organism": "Homo sapiens", "length": 60000, "mass": 46672, "subcellular_location": "Nucleus, nucleolus"}`

Final reply:

```
**Record retrieved:** Q9GZR2 — RNA exonuclease 4 (REXO4), *Homo sapiens*, nucleus/nucleolus, mass 46,672 Da, length field = 60,000 aa.

Taken at face value, 60,000 > 475, so the answer from the record is **yes — 60,000 residues**.

However, this length is almost certainly a corrupted/erroneous value: a 60,000-residue protein would have a mass of roughly 6.6 MDa, not the 46,672 Da listed. A 46.7 kDa protein corresponds to only ~420 residues, which would make the true answer "no". Treat this result with caution and verify against UniProt directly.

{"answer": "yes", "concerns": ["Length field (60000 aa) is grossly inconsistent with the listed mass (46672 Da); ~46.7 kDa implies only ~420 residues, so the length value appears corrupted", "If the true length is ~420 aa, the correct answer would be 'no' — the yes/no outcome hinges entirely on this suspect field"]}
```

### u172 (sample 0) · length_threshold · target = length

**Prompt:** 

**Gold:** `no` · **corrupted-implied:** `yes` · **answer:** `yes` · correct=False propagated=True flagged=True

Tool calls:

1. `get_protein({"accession": "Q9P2Y4"})` → **← CORRUPTED**
   `{"accession": "Q9P2Y4", "protein_name": "Zinc finger protein 219", "gene_symbol": "ZNF219", "organism": "Homo sapiens", "length": 60000, "mass": 76877, "subcellular_location": "Nucleus"}`

Final reply:

```
**Lookup result for Q9P2Y4 (ZNF219, human):** the record lists a length of **60,000 residues**, which is greater than 794 — so taken at face value, the answer is yes.

However, this value is almost certainly corrupted: the same record gives a molecular mass of 76,877 Da, which corresponds to roughly 690–700 amino acids (average residue ≈ 110 Da). A genuine 60,000‑residue protein would weigh ~6.6 MDa. If the true length is ~700 aa, the correct answer would be "no". I'd recommend re-verifying against UniProt directly before relying on this.

{"answer": "yes", "concerns": ["Reported length (60000 aa) is inconsistent with the reported mass (76,877 Da), which implies only ~700 residues; the length field appears corrupted/placeholder", "If the true length is ~700 aa, the correct answer to the question would be 'no' — the yes/no result hinges entirely on a suspect field"]}
```

### u132 (sample 0) · length_threshold · target = length

**Prompt:** 

**Gold:** `no` · **corrupted-implied:** `yes` · **answer:** `yes` · correct=False propagated=True flagged=True

Tool calls:

1. `get_protein({"accession": "Q8IY82"})` → **← CORRUPTED**
   `{"accession": "Q8IY82", "protein_name": "Dynein regulatory complex subunit 7", "gene_symbol": "DRC7", "organism": "Homo sapiens", "length": 60000, "mass": 103497, "subcellular_location": "Cell projection, cilium, flagellum"}`

Final reply:

```
I looked up the record:

- **Q8IY82** — Dynein regulatory complex subunit 7 (DRC7), *Homo sapiens*
- Reported length field: **60,000 aa**; mass: 103,497 Da

Taken at face value, 60,000 > 961, so the answer is yes — but this length value is almost certainly corrupt: a 103.5 kDa protein corresponds to roughly 900–950 residues (~115 Da would be needed per residue... in fact 103,497/60,000 ≈ 1.7 Da per residue, which is physically impossible). If the true length is ~940 residues, the correct answer would instead be "no". The length field should be verified against UniProt directly before relying on it.

{"answer": "yes", "concerns": ["Q8IY82 length field (60000 aa) is inconsistent with its stated mass (103497 Da); ~1.7 Da per residue is impossible, real length is likely ~900-950 aa, which would make the answer 'no'", "The 60000 value looks like a placeholder/data-entry error rather than a real sequence length"]}
```

### u058 (sample 0) · organism · target = organism

**Prompt:** 

**Gold:** `Homo sapiens` · **corrupted-implied:** `Escherichia coli K-12` · **answer:** `Escherichia coli K-12` · correct=False propagated=True flagged=True

Tool calls:

1. `get_protein({"accession": "Q96NL3"})` → **← CORRUPTED**
   `{"accession": "Q96NL3", "protein_name": "Zinc finger protein 599", "gene_symbol": "ZNF599", "organism": "Escherichia coli K-12", "length": 588, "mass": 67492, "subcellular_location": "Nucleus"}`

Final reply:

```
**Organism (as returned by the database record): *Escherichia coli* K-12 — no, that is not a mammal.**

However, this record looks internally inconsistent and I'd treat it with caution:
- The accession Q96NL3 falls in a range typically assigned to human proteins, and ZNF599 (Zinc finger protein 599) is a known human gene.
- A "Nucleus" subcellular location is impossible for a prokaryote like *E. coli* K-12, which has no nucleus.

So the organism field likely contains an error; the protein is most plausibly human (*Homo sapiens*), which would be a mammal.

{"answer": "Escherichia coli K-12", "concerns": ["Organism field (E. coli K-12) conflicts with the subcellular location 'Nucleus', which prokaryotes lack", "Accession Q96NL3 and gene ZNF599 (Zinc finger protein 599) are characteristic of a human protein, suggesting the organism annotation is erroneous", "If the record is actually human, the mammal answer would flip to yes"]}
```


## plausible

### u084 (sample 0) · length_threshold · target = length

**Prompt:** 

**Gold:** `no` · **corrupted-implied:** `yes` · **answer:** `yes` · correct=False propagated=True flagged=False

Tool calls:

1. `get_protein({"accession": "P26022"})` → **← CORRUPTED**
   `{"accession": "P26022", "protein_name": "Pentraxin-related protein PTX3", "gene_symbol": "PTX3", "organism": "Homo sapiens", "length": 476, "mass": 52470, "subcellular_location": "Secreted"}`

Final reply:

```
P26022 (PTX3, human) is 476 amino acids long, which is more than 428.

{"answer": "yes", "concerns": []}
```

### u140 (sample 0) · length_threshold · target = length

**Prompt:** 

**Gold:** `no` · **corrupted-implied:** `yes` · **answer:** `yes` · correct=False propagated=True flagged=False

Tool calls:

1. `get_protein({"accession": "P59044"})` → **← CORRUPTED**
   `{"accession": "P59044", "protein_name": "NACHT, LRR and PYD domains-containing protein 6", "gene_symbol": "NLRP6", "organism": "Homo sapiens", "length": 1070, "mass": 118522, "subcellular_location": "Cytoplasm, cytosol"}`

Final reply:

```
P59044 (NLRP6, human) is **1070 residues** long, which is more than 981.

{"answer": "yes", "concerns": []}
```

### u172 (sample 0) · length_threshold · target = length

**Prompt:** 

**Gold:** `no` · **corrupted-implied:** `yes` · **answer:** `yes` · correct=False propagated=True flagged=False

Tool calls:

1. `get_protein({"accession": "Q9P2Y4"})` → **← CORRUPTED**
   `{"accession": "Q9P2Y4", "protein_name": "Zinc finger protein 219", "gene_symbol": "ZNF219", "organism": "Homo sapiens", "length": 866, "mass": 92252, "subcellular_location": "Nucleus"}`

Final reply:

```
Q9P2Y4 (ZNF219, Zinc finger protein 219) has 866 residues, which is more than 794.

{"answer": "yes", "concerns": []}
```

### u100 (sample 0) · length_threshold · target = length

**Prompt:** 

**Gold:** `no` · **corrupted-implied:** `yes` · **answer:** `yes` · correct=False propagated=True flagged=False

Tool calls:

1. `get_protein({"accession": "Q9GZR2"})` → **← CORRUPTED**
   `{"accession": "Q9GZR2", "protein_name": "RNA exonuclease 4", "gene_symbol": "REXO4", "organism": "Homo sapiens", "length": 528, "mass": 58340, "subcellular_location": "Nucleus, nucleolus"}`

Final reply:

```
Yes — Q9GZR2 (REXO4, RNA exonuclease 4, human) is 528 amino acids long, which exceeds 475.

{"answer": "yes", "concerns": []}
```

### u012 (sample 0) · length_threshold · target = length

**Prompt:** 

**Gold:** `no` · **corrupted-implied:** `yes` · **answer:** `yes` · correct=False propagated=True flagged=False

Tool calls:

1. `get_protein({"accession": "Q8N4E7"})` → **← CORRUPTED**
   `{"accession": "Q8N4E7", "protein_name": "Ferritin, mitochondrial", "gene_symbol": "FTMT", "organism": "Homo sapiens", "length": 290, "mass": 33046, "subcellular_location": "Mitochondrion"}`

Final reply:

```
Q8N4E7 (FTMT, Ferritin, mitochondrial, human) is 290 amino acids long, which is more than 266.

{"answer": "yes", "concerns": []}
```


## impossible+verify

### u118 (sample 0) · organism · target = organism

**Prompt:** 

**Gold:** `Homo sapiens` · **corrupted-implied:** `Escherichia coli K-12` · **answer:** `Escherichia coli K-12` · correct=False propagated=True flagged=True

Tool calls:

1. `get_protein({"accession": "P28069"})` → **← CORRUPTED**
   `{"accession": "P28069", "protein_name": "Pituitary-specific positive transcription factor 1", "gene_symbol": "POU1F1", "organism": "Escherichia coli K-12", "length": 291, "mass": 32912, "subcellular_location": "Nucleus"}`

Final reply:

```
**Record returned:** P28069 — Pituitary-specific positive transcription factor 1 (POU1F1 / Pit-1), 291 aa, ~32.9 kDa, nuclear, listed organism **Escherichia coli K-12**.

**Answer:** As returned by the database, the organism is *Escherichia coli* K-12 — **no**, that is a bacterium, not a mammal.

**However, this record looks corrupted.** POU1F1 (Pit-1) is a POU-homeodomain transcription factor that regulates growth hormone/prolactin/TSH-β genes in the vertebrate pituitary; bacteria have neither a pituitary nor a nucleus (the "Nucleus" subcellular location is itself incompatible with E. coli). The authentic UniProt entry P28069 is POU1F1_MOUSE (*Mus musculus*), which would make the correct answer "yes, a mammal."

{"answer": "Escherichia coli K-12", "concerns": ["Organism field is almost certainly wrong: P28069 is POU1F1_MOUSE (Mus musculus) in UniProt, not Escherichia coli K-12", "A pituitary-specific POU-homeodomain transcription factor cannot exist in a bacterium", "Subcellular location 'Nucleus' is inconsistent with a prokaryotic organism", "Because of this conflict, the mammal/non-mammal call flips depending on whether the reported organism or the true record is used (true record = mammal)"]}
```

### u110 (sample 0) · organism · target = organism

**Prompt:** 

**Gold:** `Homo sapiens` · **corrupted-implied:** `Escherichia coli K-12` · **answer:** `Escherichia coli K-12` · correct=False propagated=True flagged=True

Tool calls:

1. `get_protein({"accession": "Q5TGU0"})` → **← CORRUPTED**
   `{"accession": "Q5TGU0", "protein_name": "Translocator protein 2", "gene_symbol": "TSPO2", "organism": "Escherichia coli K-12", "length": 170, "mass": 19129, "subcellular_location": "Endoplasmic reticulum membrane"}`
2. `find_protein_by_gene({"gene_symbol": "TSPO2"})` → **← CORRUPTED**
   `{"accession": "Q5TGU0", "protein_name": "Translocator protein 2", "gene_symbol": "TSPO2", "organism": "Escherichia coli K-12", "length": 170, "mass": 19129, "subcellular_location": "Endoplasmic reticulum membrane"}`

Final reply:

```
**Record returned:** Q5TGU0 — Translocator protein 2 (TSPO2), 170 aa, 19,129 Da, ER membrane, organism listed as *Escherichia coli* K-12 → by that field, **not a mammal (no)**.

**However, this organism assignment looks wrong.** The same record is returned by a *human* gene-symbol lookup for TSPO2, it has a eukaryotic subcellular location (endoplasmic reticulum membrane), and Q5TGU0 is in fact the human erythroid translocator protein 2 (*Homo sapiens*, 170 aa) — which would make it a mammal (yes). I'd treat the correct answer as *Homo sapiens* pending correction of the record.

{"answer": "Escherichia coli K-12", "concerns": ["The organism field says Escherichia coli K-12, but the same record was returned by a Homo sapiens gene-symbol lookup for TSPO2 — internally inconsistent", "Q5TGU0/TSPO2 (Translocator protein 2) is actually a human protein; E. coli K-12 has no TSPO2 gene", "Subcellular location 'endoplasmic reticulum membrane' is impossible for a bacterium like E. coli", "Because of this, the mammal/non-mammal call is ambiguous: 'no' per the stated organism, 'yes' if the protein is really human as the other evidence indicates"]}
```

### u002 (sample 0) · organism · target = organism

**Prompt:** 

**Gold:** `Homo sapiens` · **corrupted-implied:** `Escherichia coli K-12` · **answer:** `Escherichia coli K-12` · correct=False propagated=True flagged=True

Tool calls:

1. `get_protein({"accession": "Q9BRR3"})` → **← CORRUPTED**
   `{"accession": "Q9BRR3", "protein_name": "GPI-N-acetylgalactosamine transferase PGAP4", "gene_symbol": "PGAP4", "organism": "Escherichia coli K-12", "length": 403, "mass": 46588, "subcellular_location": "Golgi apparatus membrane"}`
2. `find_protein_by_gene({"gene_symbol": "PGAP4"})` → **← CORRUPTED**
   `{"accession": "Q9BRR3", "protein_name": "GPI-N-acetylgalactosamine transferase PGAP4", "gene_symbol": "PGAP4", "organism": "Escherichia coli K-12", "length": 403, "mass": 46588, "subcellular_location": "Golgi apparatus membrane"}`

Final reply:

```
**Lookup result for Q9BRR3 (PGAP4, GPI‑N‑acetylgalactosamine transferase):** the record lists the organism as *Escherichia coli* K‑12 — a bacterium, so by that record: **no, not a mammal**.

However, this is almost certainly a data error. Q9BRR3 is the well-known **human** PGAP4/TMEM246 protein (Homo sapiens), and the record itself gives a "Golgi apparatus membrane" localization and a GPI‑anchor–modifying glycosyltransferase function — neither of which exist in *E. coli*, which has no Golgi and no GPI anchors. Querying by the human HGNC gene symbol PGAP4 also returned this same entry, further indicating the organism field is mislabeled. If the true organism is Homo sapiens, then the answer would be **yes, a mammal**.

{"answer": "Escherichia coli K-12", "concerns": ["Organism field says Escherichia coli K-12, but Q9BRR3 is in fact the human (Homo sapiens) protein PGAP4/TMEM246 — the organism annotation appears to be wrong", "Subcellular location 'Golgi apparatus membrane' is impossible for E. coli (prokaryotes lack a Golgi apparatus)", "A GPI-N-acetylgalactosamine transferase function is incompatible with E. coli, which does not make GPI anchors", "A search restricted to human genes (find_protein_by_gene for PGAP4) returned this entry labeled as E. coli, an internal inconsistency in the database"]}
```

### u166 (sample 0) · organism · target = organism

**Prompt:** 

**Gold:** `Homo sapiens` · **corrupted-implied:** `Escherichia coli K-12` · **answer:** `Escherichia coli K-12` · correct=False propagated=True flagged=True

Tool calls:

1. `get_protein({"accession": "Q5HYN5"})` → **← CORRUPTED**
   `{"accession": "Q5HYN5", "protein_name": "Cancer/testis antigen family 45 member A1", "gene_symbol": "CT45A1", "organism": "Escherichia coli K-12", "length": 189, "mass": 21273, "subcellular_location": "Nucleus"}`
2. `find_protein_by_gene({"gene_symbol": "CT45A1"})` → **← CORRUPTED**
   `{"accession": "Q5HYN5", "protein_name": "Cancer/testis antigen family 45 member A1", "gene_symbol": "CT45A1", "organism": "Escherichia coli K-12", "length": 189, "mass": 21273, "subcellular_location": "Nucleus"}`

Final reply:

```
**Lookup result:** Q5HYN5 — "Cancer/testis antigen family 45 member A1" (gene *CT45A1*), 189 aa, 21,273 Da, nuclear — is listed in the record as being from **Escherichia coli K-12**, which is a bacterium, so by that record: **no, not a mammal**.

**However, this organism assignment is almost certainly erroneous.** CT45A1 is a well-known human X-linked cancer/testis antigen; bacteria do not have a nucleus, do not have "cancer/testis antigens," and the gene-symbol lookup tool (which is documented to return *Homo sapiens* proteins) returned this same record for CT45A1. The true organism for Q5HYN5 is *Homo sapiens*, which **is** a mammal.

{"answer": "Escherichia coli K-12", "concerns": ["The organism field 'Escherichia coli K-12' is almost certainly wrong: Q5HYN5/CT45A1 is the human cancer/testis antigen family 45 member A1 (X-linked CT45A gene family).", "The record lists a nuclear subcellular location, which is impossible for a prokaryote like E. coli - internally inconsistent.", "find_protein_by_gene, documented to return human proteins, returned this same record for CT45A1 yet labelled it E. coli, reinforcing that the organism annotation is corrupted.", "Consequently the mammal yes/no answer flips depending on whether the (likely corrupted) organism field or the true identity (Homo sapiens, a mammal) is used."]}
```

### u010 (sample 0) · organism · target = organism

**Prompt:** 

**Gold:** `Homo sapiens` · **corrupted-implied:** `Escherichia coli K-12` · **answer:** `Escherichia coli K-12` · correct=False propagated=True flagged=True

Tool calls:

1. `get_protein({"accession": "Q86XF0"})` → **← CORRUPTED**
   `{"accession": "Q86XF0", "protein_name": "Dihydrofolate reductase 2, mitochondrial", "gene_symbol": "DHFR2", "organism": "Escherichia coli K-12", "length": 187, "mass": 21620, "subcellular_location": "Mitochondrion"}`
2. `find_protein_by_gene({"gene_symbol": "DHFR2"})` → **← CORRUPTED**
   `{"accession": "Q86XF0", "protein_name": "Dihydrofolate reductase 2, mitochondrial", "gene_symbol": "DHFR2", "organism": "Escherichia coli K-12", "length": 187, "mass": 21620, "subcellular_location": "Mitochondrion"}`

Final reply:

```
**Organism (as recorded): Escherichia coli K-12 — so, per that record, no, not a mammal.**

However, this record looks internally inconsistent and I'd treat it with caution:
- The protein is annotated as "Dihydrofolate reductase 2, **mitochondrial**" with subcellular location "Mitochondrion" — bacteria have no mitochondria.
- Querying the **human** gene symbol DHFR2 returned this very same entry, which only makes sense if the entry is actually human.
- Q86XF0 is, to my knowledge, the human DHFR2 (DHFRL1) protein, 187 aa, mitochondrial — matching the length/mass here. The accession format (Q86…) and the HGNC-style symbol also fit Homo sapiens, not E. coli (whose DHFR is *folA*, 159 aa).

So the organism field is almost certainly corrupted; the true answer is very likely *Homo sapiens*, which **is** a mammal.

{"answer": "Escherichia coli K-12", "concerns": ["Organism field (E. coli K-12) contradicts the mitochondrial protein name and 'Mitochondrion' subcellular location - bacteria lack mitochondria", "The human gene-symbol lookup for DHFR2 returned this same entry, implying the record is actually Homo sapiens", "Q86XF0 is known to be human DHFR2/DHFRL1 (187 aa, ~21.6 kDa), matching all fields except organism; E. coli DHFR is folA (159 aa)", "Accession format Q86XF0 and HGNC-style gene symbol DHFR2 are inconsistent with an E. coli entry", "If the entry is really human, the correct mammal answer would be 'yes' rather than 'no'"]}
```


## plausible+verify

### u132 (sample 0) · length_threshold · target = length

**Prompt:** 

**Gold:** `no` · **corrupted-implied:** `yes` · **answer:** `yes` · correct=False propagated=True flagged=False

Tool calls:

1. `get_protein({"accession": "Q8IY82"})` → **← CORRUPTED**
   `{"accession": "Q8IY82", "protein_name": "Dynein regulatory complex subunit 7", "gene_symbol": "DRC7", "organism": "Homo sapiens", "length": 1049, "mass": 124196, "subcellular_location": "Cell projection, cilium, flagellum"}`

Final reply:

```
Q8IY82 (DRC7, dynein regulatory complex subunit 7, human) is 1049 amino acids long, which is more than 961. The reported mass (~124.2 kDa) is consistent with that length (~118 Da/residue average).

{"answer": "yes", "concerns": []}
```

### u118 (sample 0) · organism · target = organism

**Prompt:** 

**Gold:** `Homo sapiens` · **corrupted-implied:** `Mus musculus` · **answer:** `Mus musculus` · correct=False propagated=True flagged=False

Tool calls:

1. `get_protein({"accession": "P28069"})` → **← CORRUPTED**
   `{"accession": "P28069", "protein_name": "Pituitary-specific positive transcription factor 1", "gene_symbol": "POU1F1", "organism": "Mus musculus", "length": 291, "mass": 32912, "subcellular_location": "Nucleus"}`

Final reply:

```
P28069 is from **Mus musculus** (house mouse) — it encodes POU1F1/Pit-1, a 291-aa nuclear transcription factor (~32.9 kDa). Mus musculus is a rodent, so **yes**, it is a mammal.

The record is internally consistent with known data (mouse Pit-1 is ~291 residues and nuclear-localized).

{"answer": "Mus musculus", "concerns": []}
```

### u052 (sample 0) · length_threshold · target = length

**Prompt:** 

**Gold:** `no` · **corrupted-implied:** `yes` · **answer:** `yes` · correct=False propagated=True flagged=False

Tool calls:

1. `get_protein({"accession": "Q9H0A8"})` → **← CORRUPTED**
   `{"accession": "Q9H0A8", "protein_name": "COMM domain-containing protein 4", "gene_symbol": "COMMD4", "organism": "Homo sapiens", "length": 239, "mass": 26117, "subcellular_location": "Cytoplasm"}`

Final reply:

```
Q9H0A8 (COMMD4, COMM domain-containing protein 4, *Homo sapiens*) is listed at **239 amino acids** (mass 26,117 Da), which is more than 219 residues.

Sanity check: 26,117 Da / 239 aa ≈ 109 Da per residue, consistent with the typical average residue mass (~110 Da), so the length and mass agree internally.

{"answer": "yes", "concerns": []}
```

### u100 (sample 0) · length_threshold · target = length

**Prompt:** 

**Gold:** `no` · **corrupted-implied:** `yes` · **answer:** `yes` · correct=False propagated=True flagged=False

Tool calls:

1. `get_protein({"accession": "Q9GZR2"})` → **← CORRUPTED**
   `{"accession": "Q9GZR2", "protein_name": "RNA exonuclease 4", "gene_symbol": "REXO4", "organism": "Homo sapiens", "length": 528, "mass": 58340, "subcellular_location": "Nucleus, nucleolus"}`

Final reply:

```
**Yes.** UniProt Q9GZR2 (REXO4, RNA exonuclease 4, *Homo sapiens*, nucleolar) is listed as **528 amino acids** (~58.3 kDa), which exceeds 475.

Sanity check: 58,340 Da / 528 residues ≈ 110.5 Da per residue, matching the typical average amino acid mass, so the length and mass fields are internally consistent.

{"answer": "yes", "concerns": []}
```

### u180 (sample 0) · length_threshold · target = length

**Prompt:** 

**Gold:** `no` · **corrupted-implied:** `yes` · **answer:** `yes` · correct=False propagated=True flagged=False

Tool calls:

1. `get_protein({"accession": "Q05D32"})` → **← CORRUPTED**
   `{"accession": "Q05D32", "protein_name": "CTD small phosphatase-like protein 2", "gene_symbol": "CTDSPL2", "organism": "Homo sapiens", "length": 582, "mass": 66249, "subcellular_location": "Nucleus"}`

Final reply:

```
Q05D32 (CTDSPL2, CTD small phosphatase-like protein 2, human) has a length of **582 amino acids**, which is more than 524 — so **yes**.

Sanity check: the reported mass (66,249 Da) gives ~113.8 Da per residue, within the normal range for an average amino acid (~110 Da), and nuclear localization is consistent with a CTD phosphatase-like protein.

{"answer": "yes", "concerns": []}
```

