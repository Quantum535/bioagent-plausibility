"""Supplementary Tables 14-20 (round 2). Run from the repository root: python paper/make_si_round2.py"""
import json, os, glob, collections
R = "results/round2"; M3 = ("opus5", "argon", "deepseek")
NAME = {"opus5": "Opus 5", "argon": "Gemini 4 Argon", "deepseek": "DeepSeek V4.1 Flash", "flash": "Gemini 3.8 Flash", "sonnet5": "Sonnet 5"}
BENCH = {"opus5": "opus5", "argon": "gemini4argon", "deepseek": "deepseek_v41flash", "sonnet5": "sonnet5", "flash": "gemini38flash"}
def load(p):
    if not os.path.exists(p): return []
    d = {}
    for l in open(p):
        try: r = json.loads(l)
        except Exception: continue
        d[r.get("run_key", len(d))] = r
    return [r for r in d.values() if not (r.get("trace") or {}).get("error")]
def ok(r): return (r.get("trace") or {}).get("parsed_ok", True)
def kn(rs, cond, what="propagated"):
    c = [r for r in rs if ok(r) and r.get("condition") == cond]; return sum(bool(r.get(what)) for r in c), len(c)
def fr(k, n): return f"{k}/{n} ({100 * k / n:.0f}\\%)" if n else "--"
def bench(r): return (r.get("prompt_variant") or "default") == "default" and not r.get("verify_prompt") and r.get("harness") in (None, "none", False) and str(r.get("sample", 0)) == "0" and r.get("record_format") in (None, "summary")
def s0(r): return str(r.get("sample", 0)) == "0"
def esc(s): return str(s).replace("\\", "/").replace("_", "\\_").replace("%", "\\%").replace("&", "\\&").replace("#", "\\#").replace("{", "(").replace("}", ")").replace("$", "")
out = []
def table(caption, header, rows, wide=True):
    tab = "\\begin{tabular}{" + "l" * len(header) + "}\n\\toprule\n" + " & ".join(header) + " \\\\\n\\midrule\n" + "\n".join(" & ".join(r) + " \\\\" for r in rows) + "\n\\bottomrule\n\\end{tabular}"
    out.append("\\begin{table}[p]\n\\centering\\small\n\\caption{" + caption + "}\n" + ("\\resizebox{\\textwidth}{!}{" + tab + "}" if wide else tab) + "\n\\end{table}\n")
rows = []
for m in M3:
    full, mini, anon = load(f"{R}/{m}_IS_identity.jsonl"), load(f"{R}/{m}_IS_minimal.jsonl"), load(f"{R}/{m}_IS_bench.jsonl")
    for cond, what in (("clean", "correct"), ("impossible", "propagated"), ("plausible", "propagated")):
        rows.append([NAME[m], cond + (" (accuracy)" if cond == "clean" else ""), fr(*kn(full, cond, what)), fr(*kn(mini, cond, what)), fr(*kn([r for r in anon if s0(r)], cond, what)), fr(*kn(anon, cond, what))])
    rows.append([NAME[m], "superseded record", fr(*kn(load(f"results/phase5/{m}_full.jsonl"), "superseded")), "--", fr(*kn(load(f"{R}/{m}_IS_hist.jsonl"), "superseded")), "--"])
table("Identity. Relay (relayed/parsed runs) on the 25 length-threshold benchmark tasks with the full record, with identity but no annotation (accession, protein name, gene, organism, length, mass, sequence), and with neither (anonymous; three samples, the first paired with the other formats); clean rows give accuracy. The last row per model gives relay of the 79 superseded sequences without a second source, with the full record and anonymously.",
      ["Model", "Condition", "Full record", "Identity, no annotation", "Neither, sample 1", "Neither, 3 samples"], rows)
rows = []
O_th = load(f"{R}/opus5_TH_full.jsonl"); ot = {r["task_id"] for r in O_th}
O_on = [r for r in load("results/v2_full/traces_opus5.jsonl") if (r.get("prompt_variant") or "default") == "default" and r.get("harness") in (None, "none", False) and r["task_id"] in ot]
for cond in ("impossible", "plausible"): rows.append(["Opus 5", "thinking disabled", "full record, first 50 tasks", cond, fr(*kn(O_on, cond)), fr(*kn(O_th, cond))])
for dom, bp, f in (("proteins", "v2", "protein"), ("chemistry", "chem", "chem")):
    th = load(f"{R}/sonnet5_TH_{f}.jsonl"); tt = {r["task_id"] for r in th}; on = [r for r in load(f"results/{bp}/traces_sonnet5.jsonl") if bench(r) and r["task_id"] in tt]
    for cond in ("impossible", "plausible"): rows.append(["Sonnet 5", "thinking disabled", f"summary record, {dom}", cond, fr(*kn(on, cond)), fr(*kn(th, cond))])
table("Reasoning. Relay with adaptive thinking (the setting used throughout) and with thinking disabled, paired by task.", ["Model", "Cell", "Condition", "Thinking adaptive", "Thinking disabled"], rows, wide=False)
cfg = collections.defaultdict(collections.Counter)
for f in glob.glob("results/v2/traces_*.jsonl") + glob.glob("results/chem/traces_*.jsonl") + glob.glob(f"{R}/*.jsonl"):
    for r in load(f):
        c = (r.get("trace") or {}).get("config")
        c = {k: v for k, v in c.items() if not isinstance(v, (dict, list)) and len(str(v)) < 60} if isinstance(c, dict) else {"config": str(c)[:60]}
        c.update({k: r.get(k) for k in ("thinking", "effort") if r.get(k) is not None and k not in c})
        cfg[str(r.get("model"))][json.dumps(c, sort_keys=True, default=str)] += 1
rows = []
for m, cnt in sorted(cfg.items()):
    for c, n in cnt.most_common(3): rows.append([esc(m), esc("; ".join(f"{k}={v}" for k, v in json.loads(c).items())) or "--", str(n)])
print("request settings:"); [print("  ", r[0], "|", r[1], "|", r[2]) for r in rows]
table("Request settings recorded in the traces, by model as requested (the three most frequent configurations; runs counted over the benchmark and round-2 files). Settings not listed were the provider's defaults.", ["Model", "Settings", "Runs"], rows)
J = json.load(open(f"{R}/nc_judge.json")); rows = []
for m in M3:
    for dom, bp in (("protein", "v2"), ("chem", "chem")):
        nc = load(f"{R}/{m}_NC_{dom}.jsonl"); tasks = {r["task_id"] for r in nc}; base = [r for r in load(f"results/{bp}/traces_{BENCH[m]}.jsonl") if bench(r) and r["task_id"] in tasks]
        for cond in ("impossible", "plausible"):
            d = J[f"{m}_{dom}_{cond}"]
            rows.append([NAME[m], "proteins" if dom == "protein" else "chemistry", cond, fr(*kn(base, cond)), fr(*kn(nc, cond)), fr(*d["solicited"]), fr(*d["judge_default_prose"]), fr(*d["judge_no_concerns"]), fr(*d["keyword_no_concerns"])])
table("Prompt without the concerns field (summary record, first 100 tasks per domain). Relay under the registered prompt and without the concerns field; runs listing a concern under the registered prompt; runs voicing doubt in the reply text with and without the field, by the validated classifier; and the registered keyword detector without the field, a lower bound.",
      ["Model", "Domain", "Condition", "Relay, registered", "Relay, no field", "Concerns listed", "Doubt in reply, registered", "Doubt in reply, no field", "Keyword, no field"], rows)
rows = []
for m in ("opus5", "argon", "flash", "deepseek"):
    A = {a: [r for r in load(f"results/repetition/{m}_{a}.jsonl") if s0(r)] for a in ("R0", "R1", "R2")}; F1, F2 = load(f"{R}/{m}_F1.jsonl"), load(f"{R}/{m}_F2.jsonl")
    rows.append([NAME[m], fr(*kn(A["R0"], "plausible")), fr(*kn(A["R1"], "plausible")), fr(*kn(F1, "plausible")), fr(*kn(A["R2"], "plausible")), fr(*kn(F2, "plausible")), fr(*kn(F1, "clean", "correct"))])
table("Familiar duplicate field. Relay of a wrong molecular weight alone and with a verbatim copy that agrees or disagrees, under an unfamiliar (molecular\\_weight\\_reported) or familiar (average\\_mass) field name; first sample of the earlier arms; 60 compounds.",
      ["Model", "Alone", "Copy agrees, unfamiliar", "Copy agrees, familiar", "Copy disagrees, unfamiliar", "Copy disagrees, familiar", "Clean accuracy, familiar copy"], rows)
AU = {r["task"]: r for r in json.load(open(f"{R}/revision_audit.json"))}
ARMS = [("full record", "results/phase5/{m}_full.jsonl"), ("summary", "results/phase5/{m}_summary.jsonl"), ("second source shown", "results/robustness/{m}_p5_annotate.jsonl"), ("identity removed", R + "/{m}_IS_hist.jsonl")]
rel = collections.defaultdict(lambda: [0, 0])
for a, pat in ARMS:
    for m in M3:
        for r in load(pat.format(m=m)):
            if ok(r) and r.get("condition") == "superseded": x = rel[(AU[r["task_id"]]["class"], a)]; x[0] += bool(r.get("propagated")); x[1] += 1
rows = []
for cls in ("documented error", "flagged discrepancy", "current isoform", "matches a current RefSeq/Ensembl model", "retired, reason not recorded"):
    mem = [r for r in AU.values() if r["class"] == cls]
    rows.append([esc(cls), str(len(mem)), str(sum(r["location"] == "N-terminal" for r in mem))] + [fr(*rel[(cls, a)]) for a, _ in ARMS])
table("Revision audit of the 79 superseded sequences: class, number of proteins, number with the change at the N-terminus, and relay of the superseded value pooled over Opus 5, Gemini 4 Argon and DeepSeek V4.1 Flash in four arms (second source shown: three samples).",
      ["Class", "Proteins", "N-terminal", "Full record", "Summary", "Second source shown", "Identity removed"], rows)
rows = []
SETS = [("benchmark", glob.glob("results/v2/traces_*.jsonl") + glob.glob("results/chem/traces_*.jsonl"), bench), ("full record", glob.glob("results/v2_full/traces_*.jsonl"), None),
        ("prompt variants", glob.glob("results/prompt_ablation/*.jsonl"), None), ("withholding", glob.glob("results/blank_harness/*.jsonl"), None), ("round 2", glob.glob(f"{R}/*.jsonl"), None),
        ("superseded", glob.glob("results/phase5/*.jsonl") + glob.glob("results/robustness/*_p5_*.jsonl"), None)]
for label, files, flt in SETS:
    for f in sorted(files):
        rs = [r for r in load(f) if flt is None or flt(r)]
        for cond in sorted({r.get("condition") for r in rs}):
            c = [r for r in rs if r.get("condition") == cond]; p = [r for r in c if ok(r)]; u = len(c) - len(p)
            if u < 2: continue
            what = "correct" if cond == "clean" else "propagated"; k = sum(bool(r.get(what)) for r in p)
            worst = k + u if what == "propagated" else k
            rows.append([label, esc(os.path.basename(f).replace(".jsonl", "")), str(cond), str(len(p)), str(u), ("accuracy " if what == "correct" else "relay ") + fr(k, len(p)), fr(worst, len(c))])
table("Runs without a parseable answer: every cell with at least two, with the reported rate (unparsed runs excluded) and the rate with unparsed runs counted against the agent (as relayed for relay, as wrong for accuracy).",
      ["Experiment", "File", "Condition", "Parsed", "Unparsed", "Reported", "Counted against the agent"], rows)
open("paper/nmi/si_round2.tex", "w").write("\\clearpage\n\\section*{Supplementary Tables 14--20: experiments added in revision}\n\n" + "\n".join(out)); print("wrote paper/nmi/si_round2.tex,", len(out), "tables")
