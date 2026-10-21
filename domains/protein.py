"""Protein domain: thin shim over the original modules so run.py / make_tasks.py can treat domains uniformly."""
import json
from corrupt import apply_corruption  # noqa: F401
from tasks import TEMPLATES, generate_tasks, generate_sweep_tasks, verify_task  # noqa: F401
from tools import CorruptingToolLayer, ProteinTable as Table, render_record as render, tool_schemas  # noqa: F401

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
