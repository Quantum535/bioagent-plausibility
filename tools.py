"""Mock lookup tools backed by data/proteins.json, plus the corrupting wrapper."""
import json
from pathlib import Path

from corrupt import apply_corruption

DATA_PATH = Path(__file__).parent / "data" / "proteins.json"
FULL_PATH = Path(__file__).parent / "data" / "uniprot_full.json"
FULL_FIELD_PATH = {  # where each experiment field lives inside a full UniProtKB entry
    "length": ("sequence", "length"), "mass": ("sequence", "molWeight"),
    "organism": ("organism", "scientificName"), "gene_symbol": ("genes", 0, "geneName", "value"),
}
RECORD_FIELDS = ["accession", "protein_name", "gene_symbol", "organism", "length", "mass", "subcellular_location"]

def tool_schemas(record_format="summary"):
    """Tool declarations. The description changes with the record format, so the config hash does too."""
    if record_format == "summary":
        return TOOL_SCHEMAS
    import copy
    schemas = copy.deepcopy(TOOL_SCHEMAS)
    schemas[0]["description"] = ("Look up a protein record by UniProt accession (e.g. P04637). Returns the full "
                                 "UniProtKB entry as JSON (names, organism, sequence, features, comments, keywords).")
    schemas[1]["description"] = ("Look up the human (Homo sapiens) protein encoded by a gene symbol (e.g. TP53). "
                                 "Returns the full UniProtKB entry as JSON, as for get_protein.")
    return schemas


TOOL_SCHEMAS = [
    {
        "name": "get_protein",
        "description": ("Look up a protein record by UniProt accession (e.g. P04637). Returns accession, "
                        "protein_name, gene_symbol, organism, length (amino acids), mass (Da) and "
                        "subcellular_location."),
        "input_schema": {
            "type": "object",
            "properties": {"accession": {"type": "string", "description": "UniProt accession"}},
            "required": ["accession"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "find_protein_by_gene",
        "description": ("Look up the human (Homo sapiens) protein encoded by a gene symbol (e.g. TP53). "
                        "Returns the same record fields as get_protein."),
        "input_schema": {
            "type": "object",
            "properties": {"gene_symbol": {"type": "string", "description": "HGNC gene symbol"}},
            "required": ["gene_symbol"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


class ProteinTable:
    def __init__(self, path=DATA_PATH, record_format="summary", full_path=FULL_PATH):
        self.record_format = record_format
        self.records = [{k: r[k] for k in RECORD_FIELDS} for r in json.loads(Path(path).read_text())]
        self.full = None
        if record_format == "full":
            self.full = json.loads(Path(full_path).read_text())
            missing = [r["accession"] for r in self.records if r["accession"] not in self.full]
            assert not missing, f"full entries missing for {missing[:5]}... run fetch_full.py"
        self.splits = {r["accession"]: r.get("split", "task") for r in json.loads(Path(path).read_text())}
        self.by_acc = {r["accession"].upper(): r for r in self.records}
        self.by_gene = {r["gene_symbol"].upper(): r for r in self.records}
        assert len(self.by_gene) == len(self.records), "gene symbols must be unique"

    def task_records(self):
        return [r for r in self.records if self.splits[r["accession"]] == "task"]

    def spare_records(self):
        return [r for r in self.records if self.splits[r["accession"]] == "spare"]

    def lookup(self, tool_name, args):
        """Clean lookup. Returns (record or None, error string or None)."""
        if tool_name == "get_protein":
            key = str(args.get("accession", "")).strip().upper()
            rec = self.by_acc.get(key)
            return rec, (None if rec else f"Error: no record found for accession '{args.get('accession')}'.")
        if tool_name == "find_protein_by_gene":
            key = str(args.get("gene_symbol", "")).strip().upper()
            rec = self.by_gene.get(key)
            return rec, (None if rec else f"Error: no human protein found for gene symbol '{args.get('gene_symbol')}'.")
        return None, f"Error: unknown tool '{tool_name}'."


def record_to_json(rec):
    return json.dumps({k: rec[k] for k in RECORD_FIELDS})


def render_record(table, rec, corruption=None):
    """Serialize a clean record (with an optional corruption) in the table's record format."""
    if table.record_format == "summary":
        return record_to_json(apply_corruption(rec, corruption))
    import copy
    e = copy.deepcopy(table.full[rec["accession"]])
    if corruption:
        for field, value in corruption["fields"].items():
            node = e
            for key in FULL_FIELD_PATH[field][:-1]:
                node = node[key]
            node[FULL_FIELD_PATH[field][-1]] = value
    return json.dumps(e)


class CorruptingToolLayer:
    """Serves tool calls for one (task, condition). Corrupts only the task's target record's target field(s)."""

    def __init__(self, table, condition, task):
        self.table = table
        self.condition = condition
        self.task = task
        self.corruption = None if condition == "clean" else task["corruptions"][condition]
        self.target_acc = task["target_accession"].upper()
        self.calls = []

    def call(self, tool_name, args):
        rec, err = self.table.lookup(tool_name, args)
        entry = {"tool": tool_name, "input": args, "accession": None, "corrupted": False, "is_error": err is not None}
        if err:
            entry["output"] = err
            self.calls.append(entry)
            return err, True
        entry["accession"] = rec["accession"]
        corruption = None
        if self.corruption is not None and rec["accession"].upper() == self.target_acc:
            corruption = self.corruption
            entry["corrupted"] = True
        out = render_record(self.table, rec, corruption)
        entry["output"] = out
        self.calls.append(entry)
        return out, False
