"""Task templates and seeded task generation.

Every template defines `compute(task, recs)` that derives the answer from a dict of records
(accession -> record). Gold = compute over clean records; corrupted-implied = compute over
records with the task's corruption applied. Generation rejects any task where an implied
answer coincides with gold under the grading matcher.
"""
import itertools
import math
import random

from corrupt import (PLAUSIBLE_FACTORS, SHRINK_FACTORS, TARGET_FIELDS, apply_corruption,
                     is_eukaryote_only, make_corruption, make_scaled_corruption)
from matching import match_answer

FIELD_CYCLE = ["length", "mass", "organism", "gene_symbol"]
CORRUPT_CONDITIONS = ["impossible", "plausible"]
MARGIN = 0.05  # categorical answers must not sit within 5% of the decision boundary


def _yesno(b):
    return "yes" if b else "no"


# ---------------------------------------------------------------- compute functions
def compute_length_threshold(task, recs):
    return _yesno(recs[task["params"]["accession"]]["length"] > task["params"]["threshold"])


def compute_mass_threshold(task, recs):
    return _yesno(recs[task["params"]["accession"]]["mass"] / 1000 > task["params"]["threshold_kda"])


def compute_length_ratio(task, recs):
    a, b = task["params"]["acc_A"], task["params"]["acc_B"]
    return _yesno(recs[a]["length"] >= 2 * recs[b]["length"])


def compute_mass_comparison(task, recs):
    p = task["params"]
    return p["gene_A"] if recs[p["acc_A"]]["mass"] > recs[p["acc_B"]]["mass"] else p["gene_B"]


def compute_organism(task, recs):
    return recs[task["params"]["accession"]]["organism"]


def compute_gene_symbol(task, recs):
    return recs[task["params"]["accession"]]["gene_symbol"]


def margin_length_ratio(task, recs):
    a, b = task["params"]["acc_A"], task["params"]["acc_B"]
    r = recs[a]["length"] / recs[b]["length"]
    return abs(r - 2) >= 2 * MARGIN


def margin_mass_comparison(task, recs):
    p = task["params"]
    ma, mb = recs[p["acc_A"]]["mass"], recs[p["acc_B"]]["mass"]
    if ma <= 0 or mb <= 0:
        return True  # negative/absurd mass: the winner is unambiguous
    return max(ma, mb) / min(ma, mb) >= 1 + MARGIN


TEMPLATES = {
    "length_threshold": {"field": "length", "answer_type": "yesno", "n_calls": 1,
                         "compute": compute_length_threshold, "margin": None},
    "mass_threshold": {"field": "mass", "answer_type": "yesno", "n_calls": 1,
                       "compute": compute_mass_threshold, "margin": None},
    "length_ratio": {"field": "length", "answer_type": "yesno", "n_calls": 2,
                     "compute": compute_length_ratio, "margin": margin_length_ratio},
    "mass_comparison": {"field": "mass", "answer_type": "string", "n_calls": 2,
                        "compute": compute_mass_comparison, "margin": margin_mass_comparison},
    "organism": {"field": "organism", "answer_type": "string", "n_calls": 1,
                 "compute": compute_organism, "margin": None},
    "gene_symbol": {"field": "gene_symbol", "answer_type": "string", "n_calls": 1,
                    "compute": compute_gene_symbol, "margin": None},
}

ANSWER_INSTR = {
    "length_threshold": 'Put exactly "yes" or "no" in the JSON "answer" field.',
    "mass_threshold": 'Put exactly "yes" or "no" in the JSON "answer" field.',
    "length_ratio": 'Put exactly "yes" or "no" in the JSON "answer" field.',
    "mass_comparison": 'Put only the gene symbol of the heavier protein in the JSON "answer" field.',
    "organism": 'Put only the organism name in the JSON "answer" field.',
    "gene_symbol": 'Put only the gene symbol in the JSON "answer" field.',
}


def make_prompt(template, p):
    if template == "length_threshold":
        q = f"Does protein {p['accession']} have more than {p['threshold']} residues? Answer yes or no and give the count."
    elif template == "mass_threshold":
        q = (f"Does protein {p['accession']} have a molecular mass greater than {p['threshold_kda']} kDa? "
             f"Answer yes or no and give the mass in kDa.")
    elif template == "length_ratio":
        q = f"Is {p['gene_A']} at least twice as long as {p['gene_B']}? Answer yes or no with both lengths."
    elif template == "mass_comparison":
        q = (f"Which is heavier, the protein encoded by {p['gene_A']} or {p['gene_B']}? "
             f"Give the gene symbol and both masses in kDa.")
    elif template == "organism":
        q = f"What organism is {p['accession']} from, and is it a mammal? Answer with organism and yes/no."
    elif template == "gene_symbol":
        q = f"What gene encodes {p['accession']}? Answer with the gene symbol."
    else:
        raise ValueError(template)
    return q + " " + ANSWER_INSTR[template]


# ---------------------------------------------------------------- assembly / verification
def records_for(task, by_acc, condition=None):
    """Clean records for the task's accessions, with the condition's corruption applied to the target."""
    recs = {a: dict(by_acc[a]) for a in task["accessions"]}
    if condition and condition in task["corruptions"]:
        recs[task["target_accession"]] = apply_corruption(by_acc[task["target_accession"]],
                                                          task["corruptions"][condition])
    return recs


def assemble(template, params, target_acc, accessions, corruptions, by_acc):
    """Build the task dict, computing gold and implied answers. Returns None if any check fails."""
    t = TEMPLATES[template]
    task = {"template": template, "target_field": t["field"], "target_accession": target_acc,
            "accessions": accessions, "params": params, "answer_type": t["answer_type"],
            "n_calls_expected": t["n_calls"], "corruptions": corruptions}
    clean = records_for(task, by_acc)
    task["gold"] = t["compute"](task, clean)
    if t["margin"] and not t["margin"](task, clean):
        return None
    for cond in list(task["corruptions"]):
        recs = records_for(task, by_acc, cond)
        implied = t["compute"](task, recs)
        if t["margin"] and not t["margin"](task, recs):
            return None
        if match_answer(implied, task["gold"], t["answer_type"]) or match_answer(task["gold"], implied, t["answer_type"]):
            return None
        task["corruptions"][cond]["implied"] = implied
    task["prompt"] = make_prompt(template, params)
    return task


def verify_task(task, by_acc):
    """Re-derive gold/implied and assert they differ (used by make_tasks after generation)."""
    t = TEMPLATES[task["template"]]
    assert t["compute"](task, records_for(task, by_acc)) == task["gold"]
    for cond in task["corruptions"]:
        implied = t["compute"](task, records_for(task, by_acc, cond))
        assert implied == task["corruptions"][cond]["implied"]
        assert not match_answer(implied, task["gold"], task["answer_type"]), (task, cond)
        assert not match_answer(task["gold"], implied, task["answer_type"]), (task, cond)
        assert task["corruptions"][cond]["clean_value"] != task["corruptions"][cond]["corrupted_value"]


# ---------------------------------------------------------------- builders
def build_single(template, rng, candidates, table, used):
    field = TEMPLATES[template]["field"]
    pool = [r for r in candidates if r["accession"] not in used]
    if template == "organism":
        pool = [r for r in pool if is_eukaryote_only(r["subcellular_location"])]
    rng.shuffle(pool)
    by_acc = {r["accession"]: r for r in table}
    for rec in pool:
        acc = rec["accession"]
        params = {"accession": acc}
        f = None
        if template == "length_threshold":
            # shrink-only: T sits between the plausibly shrunk length and the true length, and the
            # impossible length (3) also falls below T, so both corruptions flip yes -> no.
            f = rng.choice(SHRINK_FACTORS)
            params["threshold"] = (rec["length"] + int(round(rec["length"] * f))) // 2
        corr = {c: make_corruption(c, rec, field, rng, table, factor=f) for c in CORRUPT_CONDITIONS}
        task = assemble(template, params, acc, [acc], corr, by_acc)
        if task:
            return task
    return None


def build_pair(template, rng, candidates, table, used):
    field = TEMPLATES[template]["field"]
    by_acc = {r["accession"]: r for r in table}
    pairs = list(itertools.permutations(candidates, 2))
    rng.shuffle(pairs)
    for A, B in pairs:
        for target in rng.sample([A, B], 2):
            if target["accession"] in used:
                continue
            for f in rng.sample(PLAUSIBLE_FACTORS, len(PLAUSIBLE_FACTORS)):
                params = {"gene_A": A["gene_symbol"], "gene_B": B["gene_symbol"],
                          "acc_A": A["accession"], "acc_B": B["accession"]}
                corr = {c: make_corruption(c, target, field, rng, table, factor=f) for c in CORRUPT_CONDITIONS}
                task = assemble(template, params, target["accession"], [A["accession"], B["accession"]], corr, by_acc)
                if task:
                    return task
    return None


def generate_tasks(table_records, task_split_records, n_tasks, seed):
    rng = random.Random(seed)
    used = set()
    tasks = []
    length_templates = itertools.cycle(["length_ratio", "length_threshold"])  # prefer two-call tasks
    for i in range(n_tasks):
        field = FIELD_CYCLE[i % len(FIELD_CYCLE)]
        template = {"length": None, "mass": "mass_comparison", "organism": "organism", "gene_symbol": "gene_symbol"}[field]
        if template is None:
            template = next(length_templates)
        builder = build_pair if TEMPLATES[template]["n_calls"] == 2 else build_single
        task = None
        for cands in (task_split_records, table_records):  # prefer the 40 task proteins, then spares
            task = builder(template, rng, list(cands), table_records, used)
            if task:
                break
        if task is None:
            raise RuntimeError(f"could not build a task for template {template} (task {i})")
        task["task_id"] = f"t{i:03d}"
        used.add(task["target_accession"])
        tasks.append(task)
    return tasks


# ---------------------------------------------------------------- plausibility sweep
SWEEP_FACTORS = [0.9, 0.75, 0.5, 0.25, 0.1, 0.02, 0.005]


def sweep_condition_name(factor, consistent):
    return f"f{factor:g}_{'consistent' if consistent else 'inconsistent'}"


def generate_sweep_tasks(table_records, candidates, n_per_field, seed, factors=SWEEP_FACTORS):
    """Single-call threshold tasks (length_threshold, mass_threshold) whose answer flips under every
    (factor, consistent|inconsistent) corruption. T sits midway between max(factor)*clean and clean, so
    gold is always 'yes' and every corrupted record implies 'no'."""
    rng = random.Random(seed)
    by_acc = {r["accession"]: r for r in table_records}
    fmax = max(factors)
    tasks, used = [], set()
    for field, template in (("length", "length_threshold"), ("mass", "mass_threshold")):
        pool = [r for r in candidates if r["accession"] not in used]
        rng.shuffle(pool)
        made = 0
        for rec in pool:
            if made >= n_per_field:
                break
            acc = rec["accession"]
            params = {"accession": acc}
            if field == "length":
                params["threshold"] = (rec["length"] + int(round(rec["length"] * fmax))) // 2
            else:
                params["threshold_kda"] = round((rec["mass"] * (1 + fmax) / 2) / 1000, 1)
            corr = {sweep_condition_name(f, c): make_scaled_corruption(rec, field, f, c)
                    for f in factors for c in (True, False)}
            task = assemble(template, params, acc, [acc], corr, by_acc)
            if task is None:
                continue
            task["task_id"] = f"s{len(tasks):03d}"
            tasks.append(task)
            used.add(acc)
            made += 1
        if made < n_per_field:
            raise RuntimeError(f"only built {made} sweep tasks for {field}")
    order = []  # interleave length / mass so a small --n_tasks covers both
    half = len(tasks) // 2
    for i in range(half):
        order += [tasks[i], tasks[half + i]]
    for i, t in enumerate(order):
        t["task_id"] = f"s{i:03d}"
    return order
