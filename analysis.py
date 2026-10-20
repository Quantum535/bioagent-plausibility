#!/usr/bin/env python3
"""Concern-cue taxonomy and task-clustered statistics for the paper.

Cue classifier (deterministic regexes over the concern text; a concern may cite several cues):
  crossfield : the record contradicts itself (mass vs length, protein name vs gene symbol, organism vs compartment)
  recall     : memory of the specific protein's known value or identity
  rule       : a general biological/physical rule with no reference to another field of the record
Writes paper/analysis.json and LaTeX table fragments under paper/tables/.
"""
import json
import random
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

from grade import load_runs, score, model_label, MODEL_ORDER, sort_models

ROOT = Path(__file__).parent
OUT = ROOT / "paper"
(OUT / "tables").mkdir(parents=True, exist_ok=True)

LINK = r"(inconsisten|incompatible|mismatch|does not match|do not match|not match|conflict|contradict|cannot|would (typically |normally |usually |roughly |be expected to |ordinarily )?(be|weigh|correspond|imply|require|give)|should (typically |normally |usually |roughly )?(be|weigh|correspond|imply)|implies|implied|suggests|indicates|points to|corresponds? to|expected (mass|length) (for|from|based)|off by|missing (a )?digit|dropped digit)"
ML_LINK = re.compile(rf"(((?<!full-)(?<!full )length|residues?|\baa\b|amino[- ]acids?)[^.;|]{{0,120}}{LINK}[^.;|]{{0,120}}(mass|\bda\b|kda|dalton))|((mass|\bda\b|kda|dalton)[^.;|]{{0,120}}{LINK}[^.;|]{{0,120}}((?<!full-)(?<!full )length|residues?|\baa\b|amino[- ]acids?))|(per residue|per amino acid|residue[- ]to[- ]mass|\bda/aa\b|da/residue|da per|average residue|residue (weight|mass))|((implausible|impossible|unrealistic|too (low|high|small|large|short|long)|\blow\b|\bhigh\b|small|large)[^.;|]{{0,12}} for (a|an|its|the) (\d[\d,]*[- ]?(residue|aa\b|amino)|(reported |stated |listed |given )?(length|mass)))|(given (its|the) (reported |stated |listed )?(length|mass))|((mass|length)[/ -](length|mass) (inconsisten|mismatch|discrepan|ratio))", re.S)
ML_OK = re.compile(r"(internally|mutually) consistent|are consistent with each other|is consistent with (its|the) (reported |listed |stated )?(mass|length)", re.S)
NAME_SYMBOL = re.compile(r"(?=.*(protein[_ ]name|protein name|\bname\b|encod|is the gene for|standard (gene )?symbol for|symbol for))(?=.*(gene[_ ]symbol|gene symbol|\bsymbol\b|\bgene\b))(?=.*(mismatch|does not match|do not match|not match|inconsisten|conflict|contradict|not the gene|not encod|is encoded by|is normally encoded|corresponds to|actually|wrong|incorrect|mislabel|erroneous|error|but (its|the) protein|annotation is|does not correspond|should be|instead of|rather than))", re.S)
ORG_CROSS = re.compile(r"(?=.*(organism|e\. ?coli|escherichia|prokaryot|bacteri|mammal|human|eukaryot|mus musculus|mouse))(?=.*(subcellular|localiz|location|compartment|membrane|nucle|synap|golgi|mitochond|endoplasmic|endosom|lysosom|cytoskelet|postsynaptic|secreted|accession (format|prefix|is a human)|human (uniprot )?accession|human[- ]gene[- ]symbol lookup|find_protein_by_gene|human-only|lookup (of|for) (the )?human|gene lookup))(?=.*(inconsisten|mismatch|does not|do not|conflict|contradict|implausible|impossible|not (consistent|compatible|plausible)|incompatible|cannot|lack|no (nucleus|membrane-bound)|would not|wouldn't|does not have|don't have|erroneous|error|yet reports|but (the|its|it) ))", re.S)
RECALL_CS = re.compile(r"\b(typically|usually|normally|classically|commonly|generally|conventionally) [A-Z][A-Z0-9]{2,}\b")
RECALL = re.compile(r"\b(classically|conventionally|(typically|usually|normally|classically|commonly|generally) (encoded|annotated|associated|reported|listed|cited|corresponds|cytoplasmic|nuclear|membrane|secreted|mitochondrial|found|localized|localised|expressed|considered|described|known|has|contains|spans|is|a (\d|[a-z]+ (protein|enzyme|receptor|gene|kinase|channel)))|canonical|well[- ]characteri[sz]ed|well[- ]known|known (to be|as|human|mammalian|length|mass|size)|is known|a known (human|mammalian)|in uniprot|according to uniprot|uniprot (lists|entry|reports|annotat|typically|record|gives|shows|values?|data)|published|commonly (cited|reported|listed|annotated)|literature|reference (length|mass|value|sequence)|actual (length|mass|size|value|protein|gene)|true (length|mass|size|value)|real (length|mass|size)|(typically|usually|normally|generally|commonly) (~|about|around|approximately|roughly|a |an |lists|associated|encoded|reported|listed|corresponds|annotated|\d)|expected [^.;|]{0,40}for (human|full[- ]length|canonical|the (full|canonical|human|native))|the expected (length|mass|size|value) (is|would be|should be)|(typically|usually|normally|generally) (much|far|considerably|substantially) (longer|larger|shorter|smaller|heavier|lighter|bigger)|known uniprot|actual known|should be (about|around|approximately|roughly|~|close to|\d)|is (a|an) (\d[\d,]*[- ]?(aa|amino|residue)|well|known|human|mammalian|\d)|human [A-Za-z0-9-]+ is (~|about|around|approximately|roughly|\d)|~\s?\d[\d,]*\s?(aa|amino[- ]acids?|residues?|kda)\s?(protein|long|in length|enzyme|receptor|gpcr|for)|\d[\d,]*[- ](aa|residue|amino[- ]acid)[- ]?(protein|long|receptor|enzyme|gpcr|channel)|my (knowledge|understanding)|based on (my|known|the known)|i (would )?expect|is a (7[- ]transmembrane|gpcr|g protein|receptor|kinase|enzyme|channel|transcription)|standard accession for|is the (standard|human) accession|is human [A-Z])", re.I | re.S)
RULE = re.compile(r"\b(negative (mass|value|number|molecular)|not physically|physically (meaningless|impossible|invalid)|no protein|not a (real|valid|plausible|genuine) protein|smaller than (a|one|the) (single )?(amino|residue)|single amino acid|smallest (known )?protein|too (small|short) to be a (protein|full)|cannot exist|no (organism|species) (named|called)|not a (known|real|valid) (organism|species)|non[- ]existent|does not exist|fictitious|placeholder|not (a |an )?(valid |official |real |known |recogni[sz]ed |standard |approved )?(hgnc|approved|recogni[sz]ed|standard|official|valid|known|real) (gene )?symbol|unrecogni[sz]ed (gene )?symbol|(unusually|extremely|very|too|implausibly|impossibly|remarkably) (short|small|low|tiny) for (a|any) (named |real |full |functional |typical |complete |genuine )?(protein|polypeptide|enzyme|transporter|translocase|receptor|channel|gene product)|peptide (fragment|rather|not a)|is a peptide|di[- ]?peptide|tripeptide|not (biologically |physically )?(possible|meaningful)|below the mass of|less than (a|one) (single )?(amino|residue)|prokaryotes? (lack|do not have|have no)|bacteria (lack|do not have|have no)|not found in (bacteria|prokaryotes)|(nucleus|golgi|mitochondri|endoplasmic|lysosom|synaps)[^.;|]{0,60}(eukaryot|not (present|found) in (bacteria|prokaryot)|absent (in|from) (bacteria|prokaryot)))\b", re.I | re.S)


def _classify_one(text):
    low = text.lower()
    ml = bool(ML_LINK.search(low)) and not (ML_OK.search(low) and "inconsisten" not in low)
    if ml:  # a link whose target is outside knowledge ("inconsistent with the known ~223 aa") is recall, not cross-field
        to_known = re.search(LINK + r"[^.;|]{0,6}(with|to) (the |its |a )?(known|canonical|published|literature|uniprot|full[- ]length|typical|expected (size|length|mass|value)|commonly)", low)
        to_field = re.search(LINK + r"[^.;|]{0,6}(with|to|given|from)? ?(its|the|a) (reported|returned|listed|stated|given|record'?s?|tool'?s?)? ?(mass|length|\d[\d,]*[- ]?(residue|aa\b|amino))", low)
        if to_known and not to_field and not re.search(r"(per residue|per amino acid|da/residue|da/aa|average residue|residue (weight|mass))", low):
            ml = False
    cross = ml or bool(NAME_SYMBOL.search(low)) or bool(ORG_CROSS.search(low))
    return {"crossfield": cross, "recall": bool(RECALL.search(text)) or bool(RECALL_CS.search(text)), "rule": bool(RULE.search(text))}


def classify(concerns):
    """Classify each concern separately and combine by OR, so a remark about a second record cannot mask the first."""
    out = {"crossfield": False, "recall": False, "rule": False}
    for c in (concerns or []):
        if str(c).strip():
            for k, v in _classify_one(str(c)).items():
                out[k] = out[k] or v
    return out


CUES = ["crossfield", "recall", "rule"]


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (min(p, max(0.0, c - h)), max(p, min(1.0, c + h)))


def cluster_bootstrap(rows, key, reps=2000, seed=0):
    """Percentile CI for the mean of `key`, resampling tasks (clusters) with replacement."""
    rng = random.Random(seed)
    by_task = defaultdict(list)
    for r in rows:
        if r[key] is not None:
            by_task[r["task_id"]].append(1.0 if r[key] else 0.0)
    tasks = list(by_task)
    if not tasks:
        return (float("nan"), float("nan"))
    stats = []
    for _ in range(reps):
        sample = [by_task[rng.choice(tasks)] for _ in tasks]
        vals = [v for s in sample for v in s]
        stats.append(sum(vals) / len(vals))
    return (float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5)))


def main():
    import argparse
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--traces", nargs="+", default=[str(ROOT / "results" / "traces*.jsonl")])
    ap.add_argument("--sweep", nargs="+", default=[str(ROOT / "results" / "sweep_traces*.jsonl")])
    ap.add_argument("--out_dir", default=str(OUT))
    args = ap.parse_args()
    OUT = Path(args.out_dir)
    (OUT / "tables").mkdir(parents=True, exist_ok=True)
    main_rows = [score(r) for r in load_runs(args.traces)]
    sweep_rows = [score(r) for r in load_runs(args.sweep)]
    for r in main_rows + sweep_rows:
        r.update({f"cue_{k}": v for k, v in classify(r["concerns"]).items()})
    for r in sweep_rows:
        r["group"] = "sweep " + ("consistent" if r["base_condition"].endswith("_consistent") else "inconsistent") if r["base_condition"] != "clean" else "clean"
    models = sort_models({r["model"] for r in main_rows})

    # ---------------- taxonomy: among flagged corrupted runs, share citing each cue
    groups = [("impossible", lambda r: r["condition"] == "impossible"),
              ("plausible", lambda r: r["condition"] == "plausible"),
              ("sweep consistent", lambda r: r.get("group") == "sweep consistent"),
              ("sweep inconsistent", lambda r: r.get("group") == "sweep inconsistent")]
    tax = {}
    for gname, sel in groups:
        pool = [r for r in (main_rows if gname in ("impossible", "plausible") else sweep_rows) if sel(r) and r["flagged"]]
        for m in ["all"] + models:
            sub = pool if m == "all" else [r for r in pool if r["model"] == m]
            n = len(sub)
            tax[f"{gname}|{m}"] = {"n_flagged": n, **{c: (sum(r[f"cue_{c}"] for r in sub) / n if n else None) for c in CUES},
                                   "none": (sum(not any(r[f"cue_{c}"] for c in CUES) for r in sub) / n if n else None)}
    # ---------------- per-cue propagation: among flagged corrupted runs, does the cited cue predict propagation?
    cue_prop = {}
    for gname, sel in groups[:2]:
        pool = [r for r in main_rows if sel(r) and r["flagged"]]
        for c in CUES:
            sub = [r for r in pool if r[f"cue_{c}"]]
            cue_prop[f"{gname}|{c}"] = {"n": len(sub), "propagated": (sum(bool(r["propagated"]) for r in sub) / len(sub) if sub else None)}

    # ---------------- cluster bootstrap + majority vote
    boot = {}
    for m in models:
        for cond in sorted({r["condition"] for r in main_rows}):
            sub = [r for r in main_rows if r["model"] == m and r["condition"] == cond]
            if not sub or cond.startswith("clean"):
                continue
            k = sum(bool(r["propagated"]) for r in sub); n = len(sub)
            boot[f"{m}|{cond}"] = {"n": n, "rate": k / n, "wilson": wilson(k, n), "cluster_boot": cluster_bootstrap(sub, "propagated"),
                                   "flag_rate": sum(r["flagged"] for r in sub) / n, "flag_boot": cluster_bootstrap(sub, "flagged")}
    majority = {}
    s5 = [r for r in main_rows if r["model"] == "claude-sonnet-5"]
    for cond in sorted({r["condition"] for r in s5}):
        if cond.startswith("clean"):
            continue
        by_task = defaultdict(list)
        for r in s5:
            if r["condition"] == cond:
                by_task[r["task_id"]].append(bool(r["propagated"]))
        votes = [sum(v) >= 2 for v in by_task.values()]
        unanimous = [len(set(v)) == 1 for v in by_task.values()]
        majority[cond] = {"n_tasks": len(by_task), "majority_rate": sum(votes) / len(votes), "unanimous": sum(unanimous) / len(unanimous),
                          "majority_wilson": wilson(sum(votes), len(votes))}

    # ---------------- logistic regression with task-clustered SEs (corrupted main runs)
    import pandas as pd
    import statsmodels.formula.api as smf
    df = pd.DataFrame([{"propagated": int(bool(r["propagated"])), "model": model_label(r["model"]), "impossible": int(r["base_condition"] == "impossible"),
                        "verify": int(r["verify_prompt"]), "field": r["target_field"], "task": r["task_id"], "two_call": int(r["n_tool_calls"] >= 2)}
                       for r in main_rows if r["base_condition"] != "clean"])
    df["model"] = pd.Categorical(df["model"], categories=[model_label(m) for m in models])
    df["model"] = df["model"].cat.reorder_categories([model_label("claude-sonnet-5")] + [model_label(m) for m in models if m != "claude-sonnet-5"])
    fit = smf.logit("propagated ~ C(model) + impossible + verify + C(field)", data=df).fit(disp=0, cov_type="cluster", cov_kwds={"groups": df["task"]})
    reg = {}
    for name in fit.params.index:
        ci = fit.conf_int().loc[name]
        reg[name] = {"or": float(np.exp(fit.params[name])), "ci": [float(np.exp(ci[0])), float(np.exp(ci[1]))], "p": float(fit.pvalues[name])}

    out = {"taxonomy": tax, "cue_propagation": cue_prop, "bootstrap": boot, "majority_sonnet5": majority, "regression": reg,
           "n_main": len(main_rows), "n_sweep": len(sweep_rows)}
    (OUT / "analysis.json").write_text(json.dumps(out, indent=1))

    # ---------------- LaTeX fragments
    def pct(v): return "–" if v is None else f"{100 * v:.0f}"
    L = ["\\begin{tabular}{lrrrrr}", "\\toprule",
         "flagged runs & $n$ & cross-field & recall & rule & none \\\\", "\\midrule"]
    for gname, _ in groups:
        t = tax[f"{gname}|all"]
        L.append(f"{gname} & {t['n_flagged']} & {pct(t['crossfield'])} & {pct(t['recall'])} & {pct(t['rule'])} & {pct(t['none'])} \\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "tables" / "taxonomy.tex").write_text("\n".join(L) + "\n")
    L = ["\\begin{tabular}{llrrrrr}", "\\toprule", "group & model & $n$ & cross-field & recall & rule & none \\\\", "\\midrule"]
    for gname, _ in groups:
        for m in models:
            t = tax.get(f"{gname}|{m}")
            if t and t["n_flagged"]:
                L.append(f"{gname} & {model_label(m)} & {t['n_flagged']} & {pct(t['crossfield'])} & {pct(t['recall'])} & {pct(t['rule'])} & {pct(t['none'])} \\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "tables" / "taxonomy_by_model.tex").write_text("\n".join(L) + "\n")
    L = ["\\begin{tabular}{llrrr}", "\\toprule", "model & condition & propagation & Wilson 95\\% & task-cluster bootstrap 95\\% \\\\", "\\midrule"]
    for m in models:
        for cond in ["impossible", "plausible", "impossible+verify", "plausible+verify"]:
            b = boot.get(f"{m}|{cond}")
            if b:
                L.append(f"{model_label(m)} & {cond} & {100*b['rate']:.0f}\\% & [{100*b['wilson'][0]:.0f}, {100*b['wilson'][1]:.0f}] & [{100*b['cluster_boot'][0]:.0f}, {100*b['cluster_boot'][1]:.0f}] \\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "tables" / "bootstrap.tex").write_text("\n".join(L) + "\n")
    pretty = {"Intercept": "intercept (Sonnet 5, plausible, baseline, gene symbol)", "impossible": "impossible (vs plausible)", "verify": "+verify (plausible)",
              "impossible:verify": "impossible $\\times$ +verify"}
    L = ["\\begin{tabular}{lrrr}", "\\toprule", "term & odds ratio & 95\\% CI & $p$ \\\\", "\\midrule"]
    for name, v in reg.items():
        label = pretty.get(name, name.replace("C(model)[T.", "model: ").replace("C(field)[T.", "field: ").replace("]", "").replace("_", " "))
        L.append(f"{label} & {v['or']:.2f} & [{v['ci'][0]:.2f}, {v['ci'][1]:.2f}] & {v['p']:.3g} \\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "tables" / "regression.tex").write_text("\n".join(L) + "\n")

    # ---------------- console summary
    print("== taxonomy (share of flagged runs citing each cue), pooled over models")
    for gname, _ in groups:
        t = tax[f"{gname}|all"]; print(f"  {gname:20s} n={t['n_flagged']:4d} crossfield={pct(t['crossfield'])}% recall={pct(t['recall'])}% rule={pct(t['rule'])}% none={pct(t['none'])}%")
    print("== per model")
    for gname, _ in groups:
        for m in models:
            t = tax.get(f"{gname}|{m}")
            if t and t["n_flagged"]:
                print(f"  {gname:20s} {model_label(m):11s} n={t['n_flagged']:3d} crossfield={pct(t['crossfield'])}% recall={pct(t['recall'])}% rule={pct(t['rule'])}% none={pct(t['none'])}%")
    print("== propagation among flagged runs by cited cue")
    for k, v in cue_prop.items(): print(f"  {k:28s} n={v['n']:3d} propagated={pct(v['propagated'])}%")
    print("== cluster bootstrap vs Wilson (propagation)")
    for k, b in boot.items(): print(f"  {k:40s} {100*b['rate']:.0f}%  wilson [{100*b['wilson'][0]:.0f},{100*b['wilson'][1]:.0f}]  boot [{100*b['cluster_boot'][0]:.0f},{100*b['cluster_boot'][1]:.0f}]")
    print("== Sonnet 5 per-task majority vote")
    for k, v in majority.items(): print(f"  {k:20s} majority={100*v['majority_rate']:.0f}% [{100*v['majority_wilson'][0]:.0f},{100*v['majority_wilson'][1]:.0f}] unanimous={100*v['unanimous']:.0f}% (tasks={v['n_tasks']})")
    print("== logistic regression (task-clustered SEs), odds ratios")
    for k, v in reg.items(): print(f"  {k:32s} OR={v['or']:.2f} [{v['ci'][0]:.2f},{v['ci'][1]:.2f}] p={v['p']:.3g}")
    # sample for spot check
    rng = random.Random(41)
    flagged = [r for r in main_rows + sweep_rows if r["flagged"]]
    print("== spot-check sample (40 flagged concerns with labels)")
    for r in rng.sample(flagged, 40):
        labs = [c for c in CUES if r[f"cue_{c}"]] or ["none"]
        print(f"  [{','.join(labs)}] ({r['model'].replace('claude-','')}, {r['condition']}, {r['target_field']}) {' | '.join(r['concerns'])[:230]}")


if __name__ == "__main__":
    main()
