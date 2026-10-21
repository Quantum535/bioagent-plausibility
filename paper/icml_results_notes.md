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
