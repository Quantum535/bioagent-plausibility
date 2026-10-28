"""Protein domain: thin shim over the original modules so run.py / make_tasks.py can treat domains uniformly."""
import json
from corrupt import apply_corruption  # noqa: F401
from tasks import TEMPLATES, generate_tasks, generate_sweep_tasks, verify_task  # noqa: F401
from tools import CorruptingToolLayer as _Layer, ProteinTable as Table, render_record as _render, tool_schemas  # noqa: F401


def _patch_full(d, patch):
    seq = patch["sequence"]; d["sequence"] = {"value": seq, "length": len(seq), "molWeight": patch["mass"]}
    d["features"] = [f for f in d.get("features", []) if (f.get("location", {}).get("end", {}).get("value") or 0) <= len(seq)]
    return d


def render(table, rec, corruption=None):
    out = _render(table, rec, corruption)
    if corruption and corruption.get("full_patch") and getattr(table, "record_format", "summary") == "full":
        out = json.dumps(_patch_full(json.loads(out), corruption["full_patch"]))
    return out


class CorruptingToolLayer(_Layer):
    def call(self, tool, args):
        out, err = super().call(tool, args)
        corr = getattr(self, "corruption", None) or (self.task["corruptions"].get(self.condition) if self.condition != "clean" else None)
        if not err and corr and corr.get("full_patch") and getattr(self.table, "record_format", "summary") == "full":
            d = json.loads(out)
            if d.get("primaryAccession") == self.task["target_accession"]:
                out = json.dumps(_patch_full(d, corr["full_patch"])); self.calls[-1]["output"] = out
        return out, err

DEFAULT_TABLE = "data/proteins.json"
FIELD_WORDS = None  # protein words already live in grade.py


def mock_fetch(task, layer):
    """Tool-trusting agent: fetch every record the task needs through the (corrupting) layer."""
    recs, p = {}, task["params"]
    if task["n_calls_expected"] == 2:
        for g in (p["gene_A"], p["gene_B"]):
            out, _ = layer.call("find_protein_by_gene", {"gene_symbol": g})
            rec = json.loads(out); recs[rec["accession"]] = rec
    else:
        out, _ = layer.call("get_protein", {"accession": p["accession"]})
        rec = json.loads(out); recs[rec["accession"]] = rec
    return recs
