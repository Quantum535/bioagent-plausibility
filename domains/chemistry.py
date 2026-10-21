"""Chemistry domain: PubChem compound records, two lookup tools, corruptions and task templates that
mirror the protein domain. Record key is the CID (stored under the generic 'accession' name)."""
import copy, itertools, json, random
from pathlib import Path
from matching import match_answer

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TABLE = "data/chem/compounds.json"
SUMMARY_FIELDS = ["cid", "name", "molecular_weight", "heavy_atom_count", "h_bond_donors"]
FULL_FIELDS = ["cid", "name", "iupac_name", "formula", "smiles", "molecular_weight", "heavy_atom_count", "h_bond_donors"]
TARGET_FIELDS = ["molecular_weight", "heavy_atom_count", "h_bond_donors", "name"]
FIELD_CYCLE = TARGET_FIELDS
CORRUPT_CONDITIONS = ["impossible", "plausible"]
SHRINK_FACTORS, INFLATE_FACTORS = [0.75, 0.8], [1.2, 1.25]
PLAUSIBLE_FACTORS = SHRINK_FACTORS + INFLATE_FACTORS
MARGIN = 0.05
IMPOSSIBLE_WEIGHT_INFLATE = 9_000_000_000.0
IMPOSSIBLE_HEAVY_INFLATE = 50000

# words the flag heuristic looks for, per target field (grade.py merges these)
FIELD_WORDS = {
    "molecular_weight": ["molecular weight", "mol. weight", "mw", "weight", "mass", "dalton", "da", "g/mol"],
    "heavy_atom_count": ["heavy atom", "heavy-atom", "atom count", "atoms", "non-hydrogen"],
    "h_bond_donors": ["hydrogen bond donor", "h-bond donor", "hbd", "donor", "donors"],
    "name": ["name", "named", "called", "compound name", "title", "identity"],
}

TOOL_SCHEMAS = [
    {"name": "get_compound",
     "description": "Look up a small-molecule record by PubChem CID (e.g. 2244). Returns cid, name, molecular_weight (Da), heavy_atom_count and h_bond_donors.",
     "input_schema": {"type": "object", "properties": {"cid": {"type": "string", "description": "PubChem compound ID"}},
                      "required": ["cid"], "additionalProperties": False}, "strict": True},
    {"name": "find_compound_by_name",
     "description": "Look up a small-molecule record by its common name (e.g. aspirin). Returns the same fields as get_compound.",
     "input_schema": {"type": "object", "properties": {"name": {"type": "string", "description": "compound common name"}},
                      "required": ["name"], "additionalProperties": False}, "strict": True},
]


def tool_schemas(record_format="summary"):
    s = copy.deepcopy(TOOL_SCHEMAS)
    if record_format == "full":
        s[0]["description"] = ("Look up a small-molecule record by PubChem CID (e.g. 2244). Returns cid, name, iupac_name, "
                               "formula, smiles, molecular_weight (Da), heavy_atom_count and h_bond_donors.")
        s[1]["description"] = "Look up a small-molecule record by its common name (e.g. aspirin). Returns the same fields as get_compound."
    return s


class Table:
    def __init__(self, path=DEFAULT_TABLE, record_format="summary", full_path=None):
        self.record_format = record_format
        raw = json.loads(Path(path).read_text())
        self.records = [dict(r, accession=str(r["cid"])) for r in raw]
        self.splits = {str(r["cid"]): r.get("split", "task") for r in raw}
        self.by_acc = {r["accession"]: r for r in self.records}
        self.by_name = {r["name"].lower(): r for r in self.records}
        assert len(self.by_name) == len(self.records), "compound names must be unique"

    def task_records(self):
        return [r for r in self.records if self.splits[r["accession"]] == "task"]

    def lookup(self, tool_name, args):
        if tool_name == "get_compound":
            key = str(args.get("cid", "")).strip()
            rec = self.by_acc.get(key)
            return rec, (None if rec else f"Error: no record found for CID '{args.get('cid')}'.")
        if tool_name == "find_compound_by_name":
            key = str(args.get("name", "")).strip().lower()
            rec = self.by_name.get(key)
            return rec, (None if rec else f"Error: no compound found with name '{args.get('name')}'.")
        return None, f"Error: unknown tool '{tool_name}'."


def apply_corruption(record, corruption):
    rec = dict(record)
    if corruption:
        rec.update(corruption["fields"])
    return rec


def render(table, rec, corruption=None):
    fields = FULL_FIELDS if table.record_format == "full" else SUMMARY_FIELDS
    r = apply_corruption(rec, corruption)
    return json.dumps({k: r[k] for k in fields})


class CorruptingToolLayer:
    def __init__(self, table, condition, task):
        self.table, self.condition, self.task = table, condition, task
        self.corruption = None if condition == "clean" else task["corruptions"][condition]
        self.target_acc = task["target_accession"]
        self.calls = []

    def call(self, tool_name, args):
        rec, err = self.table.lookup(tool_name, args)
        entry = {"tool": tool_name, "input": args, "accession": None, "corrupted": False, "is_error": err is not None}
        if err:
            entry["output"] = err; self.calls.append(entry); return err, True
        entry["accession"] = rec["accession"]
        corruption = None
        if self.corruption is not None and rec["accession"] == self.target_acc:
            corruption = self.corruption; entry["corrupted"] = True
        out = render(self.table, rec, corruption)
        entry["output"] = out; self.calls.append(entry)
        return out, False


# ---------------------------------------------------------------- corruptions
_SYL = ["zor", "vax", "tri", "mel", "quin", "dor", "fen", "lux", "bar", "cit", "nol", "pram", "tol", "vir"]


def fake_name(rng, existing):
    ex = {n.lower() for n in existing}
    while True:
        n = "".join(rng.choice(_SYL) for _ in range(rng.randint(2, 3))) + rng.choice(["ol", "ine", "ate", "ide"])
        n = n.capitalize()
        if n.lower() not in ex:
            return n


def make_corruption(condition, record, field, rng, table, factor=None, direction=None):
    clean = record[field]
    out = {"fields": {}, "clean_value": clean, "corrupted_value": None, "factor": None, "direction": direction}
    if condition == "impossible":
        if field == "molecular_weight":
            v = IMPOSSIBLE_WEIGHT_INFLATE if direction == "inflate" else (2.0 if rng.random() < 0.5 else -record["molecular_weight"])
            out["fields"] = {"molecular_weight": v}
        elif field == "heavy_atom_count":
            out["fields"] = {"heavy_atom_count": IMPOSSIBLE_HEAVY_INFLATE if direction == "inflate" else 0}
        elif field == "h_bond_donors":
            out["fields"] = {"h_bond_donors": 500 if direction == "inflate" else -3}
        elif field == "name":
            out["fields"] = {"name": fake_name(rng, [r["name"] for r in table])}
    else:
        if field in ("molecular_weight", "heavy_atom_count"):
            pool = {"shrink": SHRINK_FACTORS, "inflate": INFLATE_FACTORS}.get(direction, PLAUSIBLE_FACTORS)
            f = factor if factor is not None else rng.choice(pool)
            out["factor"] = f
            out["fields"] = {"molecular_weight": round(record["molecular_weight"] * f, 2),
                             "heavy_atom_count": max(1, int(round(record["heavy_atom_count"] * f)))}
        elif field == "h_bond_donors":
            d = record["h_bond_donors"]
            v = d + 1 if direction == "inflate" else max(0, d - 1)
            if v == d:
                v = d + 1
            out["fields"] = {"h_bond_donors": v}
        elif field == "name":
            others = [r for r in table if r["accession"] != record["accession"]]
            out["fields"] = {"name": rng.choice(others)["name"]}
    out["corrupted_value"] = out["fields"][field]
    return out


def make_scaled_corruption(record, field, factor, consistent):
    assert field in ("molecular_weight", "heavy_atom_count")
    fields = {}
    if field == "molecular_weight":
        fields["molecular_weight"] = round(record["molecular_weight"] * factor, 2)
        if consistent:
            fields["heavy_atom_count"] = max(1, int(round(record["heavy_atom_count"] * factor)))
    else:
        fields["heavy_atom_count"] = max(1, int(round(record["heavy_atom_count"] * factor)))
        if consistent:
            fields["molecular_weight"] = round(record["molecular_weight"] * factor, 2)
    return {"fields": fields, "clean_value": record[field], "corrupted_value": fields[field],
            "factor": factor, "consistent": consistent}


# ---------------------------------------------------------------- templates
def _yn(b): return "yes" if b else "no"


def c_weight_threshold(task, recs): return _yn(recs[task["params"]["accession"]]["molecular_weight"] > task["params"]["threshold"])
def c_heavy_threshold(task, recs): return _yn(recs[task["params"]["accession"]]["heavy_atom_count"] > task["params"]["threshold"])
def c_hbd(task, recs): return str(recs[task["params"]["accession"]]["h_bond_donors"])
def c_name(task, recs): return recs[task["params"]["accession"]]["name"]


def c_weight_comparison(task, recs):
    p = task["params"]
    return p["name_A"] if recs[p["acc_A"]]["molecular_weight"] > recs[p["acc_B"]]["molecular_weight"] else p["name_B"]


def m_weight_comparison(task, recs):
    p = task["params"]
    a, b = recs[p["acc_A"]]["molecular_weight"], recs[p["acc_B"]]["molecular_weight"]
    if a <= 0 or b <= 0:
        return True
    return max(a, b) / min(a, b) >= 1 + MARGIN


TEMPLATES = {
    "weight_threshold": {"field": "molecular_weight", "answer_type": "yesno", "n_calls": 1, "compute": c_weight_threshold, "margin": None},
    "weight_comparison": {"field": "molecular_weight", "answer_type": "string", "n_calls": 2, "compute": c_weight_comparison, "margin": m_weight_comparison},
    "heavy_atom_threshold": {"field": "heavy_atom_count", "answer_type": "yesno", "n_calls": 1, "compute": c_heavy_threshold, "margin": None},
    "h_bond_donors": {"field": "h_bond_donors", "answer_type": "string", "n_calls": 1, "compute": c_hbd, "margin": None},
    "name": {"field": "name", "answer_type": "string", "n_calls": 1, "compute": c_name, "margin": None},
}
ANSWER_INSTR = {
    "weight_threshold": 'Put exactly "yes" or "no" in the JSON "answer" field.',
    "weight_comparison": 'Put only the name of the heavier compound in the JSON "answer" field.',
    "heavy_atom_threshold": 'Put exactly "yes" or "no" in the JSON "answer" field.',
    "h_bond_donors": 'Put only the number in the JSON "answer" field.',
    "name": 'Put only the compound name in the JSON "answer" field.',
}


def make_prompt(template, p):
    if template == "weight_threshold":
        q = f"Does the compound with PubChem CID {p['accession']} have a molecular weight greater than {p['threshold']} Da? Answer yes or no and give the weight."
    elif template == "weight_comparison":
        q = f"Which is heavier, {p['name_A']} or {p['name_B']}? Give the name and both molecular weights in Da."
    elif template == "heavy_atom_threshold":
        q = f"Does the compound with PubChem CID {p['accession']} have more than {p['threshold']} heavy atoms? Answer yes or no and give the count."
    elif template == "h_bond_donors":
        q = f"How many hydrogen-bond donors does the compound with PubChem CID {p['accession']} have?"
    elif template == "name":
        q = f"What is the common name of the compound with PubChem CID {p['accession']}?"
    else:
        raise ValueError(template)
    return q + " " + ANSWER_INSTR[template]


# ---------------------------------------------------------------- assembly (mirrors tasks.py)
def records_for(task, by_acc, condition=None):
    recs = {a: dict(by_acc[a]) for a in task["accessions"]}
    if condition and condition in task["corruptions"]:
        recs[task["target_accession"]] = apply_corruption(by_acc[task["target_accession"]], task["corruptions"][condition])
    return recs


def assemble(template, params, target_acc, accessions, corruptions, by_acc):
    t = TEMPLATES[template]
    task = {"template": template, "target_field": t["field"], "target_accession": target_acc, "accessions": accessions,
            "params": params, "answer_type": t["answer_type"], "n_calls_expected": t["n_calls"], "corruptions": corruptions}
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
    t = TEMPLATES[task["template"]]
    assert t["compute"](task, records_for(task, by_acc)) == task["gold"]
    for cond in task["corruptions"]:
        implied = t["compute"](task, records_for(task, by_acc, cond))
        assert implied == task["corruptions"][cond]["implied"]
        assert not match_answer(implied, task["gold"], task["answer_type"]), (task["task_id"], cond)
        assert task["corruptions"][cond]["clean_value"] != task["corruptions"][cond]["corrupted_value"]


def _factors(direction): return {"shrink": SHRINK_FACTORS, "inflate": INFLATE_FACTORS}.get(direction)


def build_single(template, rng, candidates, table, used, direction=None):
    field = TEMPLATES[template]["field"]
    pool = [r for r in candidates if r["accession"] not in used]
    if template == "h_bond_donors" and direction == "shrink":
        pool = [r for r in pool if r["h_bond_donors"] >= 1]
    rng.shuffle(pool)
    by_acc = {r["accession"]: r for r in table}
    for rec in pool:
        params, f = {"accession": rec["accession"]}, None
        if template == "weight_threshold":
            f = rng.choice(_factors(direction) or SHRINK_FACTORS)
            params["threshold"] = round((rec["molecular_weight"] + rec["molecular_weight"] * f) / 2, 1)
        elif template == "heavy_atom_threshold":
            f = rng.choice(_factors(direction) or SHRINK_FACTORS)
            params["threshold"] = (rec["heavy_atom_count"] + int(round(rec["heavy_atom_count"] * f))) // 2
        corr = {c: make_corruption(c, rec, field, rng, table, factor=f, direction=direction) for c in CORRUPT_CONDITIONS}
        task = assemble(template, params, rec["accession"], [rec["accession"]], corr, by_acc)
        if task:
            return task
    return None


def build_pair(template, rng, candidates, table, used, direction=None):
    field = TEMPLATES[template]["field"]
    by_acc = {r["accession"]: r for r in table}
    pairs = list(itertools.permutations(candidates, 2))
    rng.shuffle(pairs)
    for A, B in pairs:
        for target in rng.sample([A, B], 2):
            if target["accession"] in used:
                continue
            facs = _factors(direction) or PLAUSIBLE_FACTORS
            for f in rng.sample(facs, len(facs)):
                params = {"name_A": A["name"], "name_B": B["name"], "acc_A": A["accession"], "acc_B": B["accession"]}
                corr = {c: make_corruption(c, target, field, rng, table, factor=f, direction=direction) for c in CORRUPT_CONDITIONS}
                task = assemble(template, params, target["accession"], [A["accession"], B["accession"]], corr, by_acc)
                if task:
                    return task
    return None


def generate_tasks(table_records, task_split_records, n_tasks, seed, alternate_direction=False, prefix="c"):
    rng = random.Random(seed)
    used, tasks = set(), []
    weight_templates = itertools.cycle(["weight_comparison", "weight_threshold"])
    for i in range(n_tasks):
        field = FIELD_CYCLE[i % len(FIELD_CYCLE)]
        template = {"molecular_weight": None, "heavy_atom_count": "heavy_atom_threshold",
                    "h_bond_donors": "h_bond_donors", "name": "name"}[field]
        if template is None:
            template = next(weight_templates)
        builder = build_pair if TEMPLATES[template]["n_calls"] == 2 else build_single
        direction = None
        if alternate_direction and field != "name":
            direction = "shrink" if (i // len(FIELD_CYCLE)) % 2 == 0 else "inflate"
        task = None
        for cands in (task_split_records, table_records):
            task = builder(template, rng, list(cands), table_records, used, direction=direction)
            if task:
                break
        if task is None:
            raise RuntimeError(f"could not build a task for template {template} (task {i})")
        task["task_id"] = f"{prefix}{i:03d}"
        task["direction"] = direction
        used.add(task["target_accession"])
        tasks.append(task)
    return tasks


SWEEP_FACTORS = [0.9, 0.75, 0.5, 0.25, 0.1, 0.02, 0.005]


def sweep_condition_name(factor, consistent):
    return f"f{factor:g}_{'consistent' if consistent else 'inconsistent'}"


def generate_sweep_tasks(table_records, candidates, n_per_field, seed, factors=SWEEP_FACTORS):
    rng = random.Random(seed)
    by_acc = {r["accession"]: r for r in table_records}
    fmax = max(factors)
    tasks, used = [], set()
    for field, template in (("molecular_weight", "weight_threshold"), ("heavy_atom_count", "heavy_atom_threshold")):
        pool = [r for r in candidates if r["accession"] not in used]
        rng.shuffle(pool)
        made = 0
        for rec in pool:
            if made >= n_per_field:
                break
            params = {"accession": rec["accession"]}
            if field == "molecular_weight":
                params["threshold"] = round((rec["molecular_weight"] * (1 + fmax)) / 2, 1)
            else:
                params["threshold"] = (rec["heavy_atom_count"] + int(round(rec["heavy_atom_count"] * fmax))) // 2
            corr = {sweep_condition_name(f, c): make_scaled_corruption(rec, field, f, c) for f in factors for c in (True, False)}
            task = assemble(template, params, rec["accession"], [rec["accession"]], corr, by_acc)
            if task is None:
                continue
            tasks.append(task); used.add(rec["accession"]); made += 1
        if made < n_per_field:
            raise RuntimeError(f"only built {made} sweep tasks for {field}")
    half = len(tasks) // 2
    order = [t for i in range(half) for t in (tasks[i], tasks[half + i])]
    for i, t in enumerate(order):
        t["task_id"] = f"cs{i:03d}"
    return order


def mock_fetch(task, layer):
    recs, p = {}, task["params"]
    if task["n_calls_expected"] == 2:
        for n in (p["name_A"], p["name_B"]):
            out, _ = layer.call("find_compound_by_name", {"name": n})
            rec = json.loads(out); recs[str(rec["cid"])] = rec
    else:
        out, _ = layer.call("get_compound", {"cid": p["accession"]})
        rec = json.loads(out); recs[str(rec["cid"])] = rec
    return recs
